"""Append-only bundles of immutable Director studies bound to an existing V4 revision.

This resource never writes scenarios, quantities, operations or legal documents.
"""
import hashlib
from uuid import UUID
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict
from .db import encoded, identifier, normalize
from .security import fail
from . import director, scenarios


class MultiStudyWrite(Strict):
    contract_version: Literal[1]
    request_id: UUID
    name: str = Field(min_length=5, max_length=180)
    scenario_id: UUID
    scenario_revision: int = Field(ge=1)
    source_studies: list[UUID] = Field(min_length=1, max_length=100)
    justification: str = Field(min_length=10, max_length=3000)

    @model_validator(mode='after')
    def unique_sources(self):
        if len(self.source_studies) != len(set(self.source_studies)):
            raise ValueError('Escolha cada estudo de origem uma única vez.')
        return self


class MultiStudyRevision(MultiStudyWrite):
    expected_revision: int = Field(ge=1)


def read(ctx, sid, revision=None):
    ctx.require('read')
    row = ctx.db.one('SELECT * FROM director_multi_study_version WHERE org_id=:o AND id=:i'
        + (' AND revision=:r' if revision is not None else '') + ' ORDER BY revision DESC LIMIT 1',
        {'o':ctx.org_id, 'i':sid, 'r':revision})
    if not row:
        fail(404, 'Este estudo com vários itens não está disponível neste espaço.', 'NOT_FOUND')
    scenario = scenarios.get_scenario(ctx, row['scenario_id'])
    sources = ctx.db.all('''SELECT b.source_study_id, s.current_revision=d.scenario_revision AS context_current
        FROM director_multi_study_item b JOIN director_study d ON d.org_id=b.org_id AND d.id=b.source_study_id
        JOIN scenario s ON s.org_id=d.org_id AND s.id=d.scenario_id
        WHERE b.org_id=:o AND b.study_id=:i AND b.revision=:r''',
        {'o':ctx.org_id, 'i':sid, 'r':row['revision']})
    sources_current = len(sources)==len(row['payload']['items']) and all(s['context_current'] for s in sources)
    return normalize({k:row[k] for k in ('id','revision','previous_revision','scenario_id','scenario_revision',
        'request_id','payload','context_sha256','created_by','created_at')} | {
        'contract_version':1, 'current_scenario_revision':scenario['current_revision'],
        'sources_context_current':sources_current,
        'context_current':sources_current and scenario['current_revision']==row['scenario_revision'],
        'notice':'Cada item mantém sua unidade e sua meta. O vínculo não altera cálculos nem confirma participação.'})


def write(ctx, body, sid=None):
    ctx.require('scenario.write')
    digest = hashlib.sha256(encoded(body.model_dump(mode='json')).encode()).hexdigest()
    # Serialize retries before looking up their identity, including retries of a previous revision.
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',
        {'k':f'multi-study-request:{ctx.org_id}:{body.request_id}'})
    retry = ctx.db.one('''SELECT id,revision,request_sha256 FROM director_multi_study_version
        WHERE org_id=:o AND request_id=:q''', {'o':ctx.org_id,'q':body.request_id})
    if retry:
        if retry['request_sha256']!=digest or (sid is not None and str(retry['id'])!=str(sid)):
            fail(409, 'Esta chave já foi usada com outros dados. Confira o pedido.', 'IDEMPOTENCY_CONFLICT')
        return read(ctx, retry['id'], retry['revision'])
    previous = None
    if sid is not None:
        ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',
            {'k':f'multi-study:{ctx.org_id}:{sid}'})
        previous = ctx.db.one('''SELECT revision,scenario_id FROM director_multi_study_version
            WHERE org_id=:o AND id=:i ORDER BY revision DESC LIMIT 1''', {'o':ctx.org_id,'i':sid})
        if not previous:
            fail(404, 'Este estudo com vários itens não está disponível neste espaço.', 'NOT_FOUND')
        if previous['revision']!=body.expected_revision:
            fail(409, 'O estudo mudou. Abra a versão atual antes de salvar.', 'VERSION_CONFLICT')
        if str(previous['scenario_id'])!=str(body.scenario_id):
            fail(422, 'Preserve o cenário vinculado ao revisar este estudo.', 'SCENARIO_BINDING_MISMATCH')
    scenario = scenarios.get_scenario(ctx, body.scenario_id, lock=True)
    if scenario['current_revision']!=body.scenario_revision:
        fail(409, 'O cenário mudou. Confira a versão atual antes de vincular os itens.', 'VERSION_CONFLICT')
    items = []
    for source_id in body.source_studies:
        source = director.study(ctx, source_id)
        if not source['context_current']:
            fail(409, 'Um estudo de origem mudou de contexto. Prepare sua versão atual.', 'SOURCE_CONTEXT_STALE')
        p = source['payload']
        if p['classification']!=scenario['classification']:
            fail(422, 'Mantenha estudos fictícios e internos em conjuntos separados.', 'DATASET_MISMATCH')
        if set(p['municipalities'])!=set(scenario['snapshot']['participants']):
            fail(422, 'Nesta versão, os municípios de cada item devem coincidir com os do cenário.', 'PARTICIPANT_SCOPE_MISMATCH')
        items.append({k:p[k] for k in ('planning_item','catalogue_entry','name','specification','unit',
            'quantity_step','preliminary_target','target_justification','municipalities')} | {
                'source_study_id':str(source_id), 'source_context_sha256':source['context_sha256'],
                'history_scope':{k:p[k] for k in ('phase','start','end','history_filters') if k in p},
                'catalogue_binding':{'snapshot_id':p.get('snapshot_id'),'code':p.get('code')},
            })
    refs = [(i['planning_item']['id'], i['planning_item']['version']) for i in items]
    expected = [(i['id'],i['version']) for i in scenario['snapshot']['items']]
    if len({i for i,v in refs})!=len(refs):
        fail(422, 'Escolha uma única definição de cada item no estudo.', 'DUPLICATE_ITEM')
    if set(refs)!=set(expected):
        fail(422, 'Os itens e suas versões devem corresponder exatamente ao cenário.', 'ITEM_BINDING_MISMATCH')
    payload = {'contract_version':1,'name':body.name,'classification':scenario['classification'],
        'items':items,'municipalities':scenario['snapshot']['participants'],
        'justification':body.justification,'cross_item_quantity_total':None,
        'historical_data_is_need':False,'scenario_modified':False,'municipal_approval_created':False}
    sid = sid or identifier()
    revision = previous['revision']+1 if previous else 1
    ctx.db.execute('''INSERT INTO director_multi_study_version
        (org_id,id,revision,previous_revision,scenario_id,scenario_revision,request_id,request_sha256,payload,context_sha256,created_by)
        VALUES (:o,:i,:r,:p,:s,:sr,:q,:qh,CAST(:body AS jsonb),:h,:a)''',
        {'o':ctx.org_id,'i':sid,'r':revision,'p':revision-1 if previous else None,
         's':body.scenario_id,'sr':body.scenario_revision,'q':body.request_id,'qh':digest,
         'body':encoded(payload),'h':hashlib.sha256(encoded({'payload':payload,'scenario_id':str(body.scenario_id),
             'scenario_revision':body.scenario_revision}).encode()).hexdigest(),'a':ctx.actor_id})
    ctx.db.execute('''INSERT INTO director_multi_study_item
        (org_id,study_id,revision,item_id,item_version,source_study_id)
        VALUES (:o,:i,:r,:item,:v,:source)''', [
            {'o':ctx.org_id,'i':sid,'r':revision,'item':item['planning_item']['id'],
             'v':item['planning_item']['version'],'source':item['source_study_id']} for item in items])
    ctx.audit('director.multi_study_version_created',sid,{'revision':revision,'scenario_revision':body.scenario_revision,'items':len(items)})
    return read(ctx, sid, revision)


def listing(ctx,limit=20,offset=0):
    ctx.require('read')
    return normalize({'records':ctx.db.all('''SELECT id,revision,scenario_id,scenario_revision,payload->>'name' AS name,created_at
        FROM (SELECT DISTINCT ON(id) * FROM director_multi_study_version WHERE org_id=:o ORDER BY id,revision DESC) latest
        ORDER BY created_at DESC,id LIMIT :n OFFSET :skip''',{'o':ctx.org_id,'n':limit,'skip':offset}), 'limit':limit,'offset':offset})
