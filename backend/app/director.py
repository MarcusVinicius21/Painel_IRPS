"""Director workflow: evidence context, exploratory target and controlled IRP drafts.

No target is a V4 input. No municipal assent or official act is created here.
"""
import hashlib
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict, Number, Code, Snapshot, ScenarioCreate
from .db import encoded, identifier, normalize
from .security import fail
from . import catalogue, national_catalogue, scenarios


class CatalogueLink(Strict):
    snapshot_id: UUID
    code: str = Field(pattern=r'^\d{1,20}$')
    product_id: UUID
    justification: str = Field(min_length=20,max_length=2000)
    evidence: str = Field(min_length=10,max_length=2000)
    confirmed: Literal[True]


class StudyCreate(Strict):
    classification: Literal['internal','synthetic'] = 'internal'
    snapshot_id: UUID | None = None
    code: str | None = Field(default=None,pattern=r'^\d{1,20}$')
    product_id: UUID | None = None
    name: str = Field(min_length=5,max_length=5000)
    category: Literal['material','veiculo','uniforme','saas','servico','obra']
    specification: str = Field(min_length=10,max_length=6000)
    unit: str = Field(min_length=1,max_length=120)
    quantity_step: Number = Field(gt=0)
    service_period: str = Field(default='',max_length=200)
    quantity_basis: str = Field(default='',max_length=500)
    municipalities: list[Code] = Field(min_length=1,max_length=118)
    phase: str
    start: date
    end: date
    preliminary_target: Number | None = None
    target_justification: str = Field(default='',max_length=3000)
    technical_evidence: str = Field(min_length=10,max_length=2000)
    technical_confirmed: Literal[True]

    @model_validator(mode='after')
    def pair(self):
        if bool(self.snapshot_id)!=bool(self.code):raise ValueError('Informe código e versão do catálogo juntos.')
        if self.preliminary_target is not None and len(self.target_justification)<10:raise ValueError('Justifique a meta preliminar.')
        return self


class DraftCreate(Strict):
    scenario_revision: int = Field(ge=1)
    object: str = Field(min_length=10,max_length=6000)
    kind: Literal['procedimento','formulario','planilha','especificacoes','municipios','quantitativos'] = 'procedimento'
    procedure_reference: str = Field(default='',max_length=100)
    deadline: str = Field(default='',max_length=300)
    delivery: str = Field(default='',max_length=1000)
    note: str = Field(default='',max_length=3000)
    coherence_confirmed: bool = False
    coherence_evidence: str = Field(default='',max_length=2000)
    municipality_ibge: Code | None = None


def checked_unit(unit):
    if not unit.strip() or 'R$' in unit.upper() or '$' in unit or 'REAL' in catalogue.fold(unit).split():
        fail(422,'Informe a unidade de quantidade. O preço em reais deve ficar separado.','QUANTITY_UNIT_REQUIRED')


def get_product(ctx, pid):
    product=next((p for p in catalogue.active_products(ctx) if str(p['id'])==str(pid)),None)
    if not product:fail(404,'Este produto precisa de uma revisão atual antes de ser usado.','PRODUCT_NOT_FOUND')
    return product


def link(ctx, body):
    ctx.require('opportunity.manage')
    item=national_catalogue.entry(ctx,body.snapshot_id,body.code)
    product=get_product(ctx,body.product_id)
    if product['classification']!='official':fail(422,'Vincule o catálogo somente a fatos oficiais revisados.','DATASET_MISMATCH')
    lid=identifier()
    ctx.db.execute('''INSERT INTO national_product_link(org_id,id,snapshot_id,code,product_id,justification,evidence,created_by)
        VALUES (:o,:i,:s,:c,:p,:j,:e,:a) ON CONFLICT(org_id,snapshot_id,code,product_id) DO NOTHING''',
        {'o':ctx.org_id,'i':lid,'s':body.snapshot_id,'c':item['code'],'p':body.product_id,'j':body.justification,'e':body.evidence,'a':ctx.actor_id})
    ctx.audit('catalogue.national_link_reviewed',item['code'],{'snapshot':str(body.snapshot_id),'product':str(body.product_id)})
    return {'reviewed':True,'purchase_implied':False}


def links(ctx, snapshot, code):
    national_catalogue.entry(ctx,snapshot,code)
    return normalize({'records':ctx.db.all('''SELECT l.product_id,l.evidence,l.justification,l.created_at,c.name,c.unit_key,c.package_signature
        FROM national_product_link l JOIN canonical_product c ON c.org_id=l.org_id AND c.id=l.product_id
        WHERE l.org_id=:o AND l.snapshot_id=:s AND l.code=:c
        AND NOT EXISTS(SELECT 1 FROM canonical_product next WHERE next.org_id=c.org_id AND next.supersedes_id=c.id)
        ORDER BY l.created_at DESC''',{'o':ctx.org_id,'s':snapshot,'c':code}),
        'notice':'Um vínculo revisado identifica os itens comparáveis. O catálogo sozinho não comprova compras.'})


def create_study(ctx, body):
    ctx.require('scenario.write')
    from .opportunity_schemas import PHASES
    from typing import get_args
    if body.phase not in get_args(PHASES):fail(422,'Escolha uma situação de compra válida.')
    if body.end<body.start or (body.end-body.start).days>1826 or body.end>date.today():fail(422,'Escolha um período passado de até cinco anos.')
    cities=catalogue.validated_municipalities(ctx,body.municipalities)
    checked_unit(body.unit)
    if body.category in ('saas','servico') and (not body.service_period or not body.quantity_basis):
        fail(422,'Descreva o período de prestação e o que uma unidade do serviço representa.','SERVICE_MEASUREMENT_REQUIRED')
    entry=national_catalogue.entry(ctx,body.snapshot_id,body.code) if body.snapshot_id else None
    product=None;history=None
    if body.product_id:
        product=get_product(ctx,body.product_id)
        if product['classification']!='official':fail(422,'Um estudo interno não pode incorporar histórico fictício.','DATASET_MISMATCH')
        if entry and not any(str(l['product_id'])==str(body.product_id) for l in links(ctx,body.snapshot_id,body.code)['records']):
            fail(422,'Revise o vínculo entre este código e os registros antes de planejar.','CATALOGUE_LINK_REQUIRED')
        if catalogue.unit_key(body.unit)!=product['unit_key'] or catalogue.pack(body.unit)!=product['package_signature']:
            fail(422,'A unidade ou embalagem não corresponde ao histórico revisado.','INCOMPATIBLE_ITEMS')
        history=catalogue.product_history(ctx,body.product_id,body.phase,body.start,body.end,cities)
    raw=body.model_dump(mode='json')
    # A new planning identity preserves the exact catalogue snapshot and technical definition.
    definition={k:raw[k] for k in ('classification','snapshot_id','code','name','category','specification','unit','quantity_step','service_period','quantity_basis')}
    item_id='plan-'+hashlib.sha256(encoded({'org':ctx.org_id,**definition}).encode()).hexdigest()[:48]
    ctx.db.execute('''INSERT INTO item_version(id,version,name,family,unit,step,classification,org_id)
        VALUES (:i,1,:n,:f,:u,:step,:classification,:o) ON CONFLICT(id,version) DO NOTHING''',
        {'i':item_id,'n':body.name,'f':body.category,'u':body.unit,'step':body.quantity_step,'o':ctx.org_id,'classification':body.classification})
    snapshot=Snapshot(period=f'{body.start} a {body.end} · estudo',participants=cities,items=[{'id':item_id,'version':1}],
                      mode='A',justification='Estudo preliminar. A meta não foi distribuída nem convertida em necessidade V4.')
    scenario=scenarios.create_scenario(ctx,ScenarioCreate(title=body.name[:170],classification=body.classification,snapshot=snapshot))
    payload={**raw,'catalogue_entry':entry,'planning_item':{'id':item_id,'version':1},'municipalities':cities,
             'history':history,'history_state':'reviewed_link' if history else 'no_reviewed_link',
             'historical_data_is_need':False,'suggested_quantities':None,'confirmed_quantities':None}
    sid=identifier();digest=hashlib.sha256(encoded(payload).encode()).hexdigest()
    ctx.db.execute('''INSERT INTO director_study(org_id,id,scenario_id,scenario_revision,payload,context_sha256,created_by)
        VALUES (:o,:i,:s,1,CAST(:p AS jsonb),:h,:a)''',{'o':ctx.org_id,'i':sid,'s':scenario['id'],'p':encoded(payload),'h':digest,'a':ctx.actor_id})
    ctx.audit('director.study_created',sid,{'scenario_id':str(scenario['id']),'context_sha256':digest,'meta_distributed':False})
    return normalize({'id':sid,'scenario':scenario,'payload':payload,'context_sha256':digest})


def study(ctx, sid):
    ctx.require('read')
    row=ctx.db.one('SELECT * FROM director_study WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':sid})
    if not row:fail(404,'Este estudo não está disponível neste espaço.','NOT_FOUND')
    current=scenarios.get_scenario(ctx,row['scenario_id'])
    row['scenario']=current
    row['context_current']=current['current_revision']==row['scenario_revision']
    row['internal_reference']=f'EST-{row["created_at"].year}-{sid}'
    row['notice']='Alterações do cenário exigem nova conferência. O estudo original e suas evidências permanecem preservados.'
    return normalize(row)


def validate_draft(data, body):
    errors=[];pending=['Revisão jurídica do modelo e das cláusulas.','Publicidade, assinatura e manifestação exigem atos externos comprovados.']
    payload=data['payload'];scenario=data['scenario']
    if body.scenario_revision!=scenario['current_revision'] or not data['context_current']:
        errors.append('O cenário mudou. Prepare um novo estudo com o recorte e os itens atuais.')
    if body.kind=='formulario' and body.municipality_ibge not in payload['municipalities']:
        errors.append('Escolha um município do estudo para preparar o formulário.')
    unit=payload['unit']
    if not unit.strip() or '$' in unit:errors.append('A unidade de quantidade precisa ser conferida e separada do preço.')
    obj=catalogue.fold(body.object)
    descriptions=catalogue.fold(payload['name']+' '+payload['specification'])
    tech=('SOFTWARE','FACIAL','CATRACA','PLATAFORMA','SAAS')
    vehicles=('VEICULO','AUTOMOVEL','AMBULANCIA','CAMINHAO','ONIBUS','MINIVAN')
    if (any(t in obj for t in vehicles) and any(t in descriptions for t in tech)) or (any(t in obj for t in tech) and any(t in descriptions for t in vehicles)):
        errors.append('O objeto e os itens misturam veículos e tecnologia. Corrija a descrição antes de gerar.')
    if payload['category']=='veiculo' and any(t in descriptions for t in tech):errors.append('A categoria veículo não corresponde aos itens de tecnologia.')
    if payload['category'] in ('saas','servico') and (not payload.get('service_period') or not payload.get('quantity_basis')):
        errors.append('Faltam o período de prestação e a definição da unidade de serviço.')
    if not body.coherence_confirmed or len(body.coherence_evidence)<10:errors.append('Registre a conferência técnica entre objeto, especificação e unidade.')
    if not body.procedure_reference:pending.append('Número e ano oficiais a definir pelo controle autorizado.')
    if not body.deadline:pending.append('Prazo e canal de manifestação a validar.')
    if not body.delivery:pending.append('Locais e condições de entrega a confirmar.')
    pending+=['Autoridade competente e signatários a conferir.','Quantidades municipais sugeridas e confirmadas ainda não registradas.']
    return {'state':'blocked' if errors else 'needs_review','errors':errors,'pending':pending,'officially_published':False,'legally_approved':False}


def create_draft(ctx,sid,body):
    ctx.require('document.write')
    data=study(ctx,sid)
    data['scenario']=scenarios.get_scenario(ctx,data['scenario_id'],lock=True)
    data['context_current']=data['scenario']['current_revision']==data['scenario_revision']
    validation=validate_draft(data,body)
    from .irp_register import summary
    register=summary(ctx,sid)
    if register['confirmed_known_total'] is not None:
        validation['pending']=[p for p in validation['pending'] if p!='Quantidades municipais sugeridas e confirmadas ainda não registradas.']
        if register['pending_municipalities']:validation['pending'].append('Há municípios sem manifestação confirmada; o total conhecido é parcial.')
    calc=ctx.db.one('SELECT id,summary,core_sha256 FROM calculation WHERE org_id=:o AND scenario_id=:s AND revision=:r ORDER BY created_at DESC,id DESC LIMIT 1',
        {'o':ctx.org_id,'s':data['scenario_id'],'r':body.scenario_revision})
    lines=ctx.db.all('SELECT ibge,item_id,item_version,unit,quantity,value,state,memory FROM calculation_line WHERE org_id=:o AND calculation_id=:c ORDER BY ibge,item_id LIMIT 119',{'o':ctx.org_id,'c':calc['id']}) if calc else []
    if len(lines)>118:fail(422,'Restrinja a minuta a até 118 linhas municipais.')
    payload={'study':data['payload'],'context_sha256':data['context_sha256'],'scenario_id':str(data['scenario_id']),
             'scenario_revision':body.scenario_revision,'scenario_classification':data['scenario']['classification'],
             'municipalities':ctx.db.all('SELECT ibge,name,uf FROM municipality WHERE ibge=ANY(:c) ORDER BY name',{'c':data['payload']['municipalities']}),
             'prepared_by':ctx.name,'request':body.model_dump(mode='json'),'template_version':'irp-derived-v1',
             'calculation':normalize(calc),'calculation_lines':normalize(lines),'register':register,
             'legal_clauses_included':False,'signature_invented':False,'official_number_assigned':False}
    did=identifier()
    ctx.db.execute('INSERT INTO irp_draft(org_id,id,study_id,payload,validation,created_by) VALUES (:o,:i,:s,CAST(:p AS jsonb),CAST(:v AS jsonb),:a)',
        {'o':ctx.org_id,'i':did,'s':sid,'p':encoded(payload),'v':encoded(validation),'a':ctx.actor_id})
    ctx.audit('irp.draft_prepared',did,{'study_id':str(sid),'state':validation['state'],'scenario_revision':body.scenario_revision})
    return normalize({'id':did,'payload':payload,'validation':validation})


def draft(ctx,did):
    ctx.require('document.read')
    row=ctx.db.one('SELECT * FROM irp_draft WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':did})
    if not row:fail(404,'Esta minuta não está disponível neste espaço.','NOT_FOUND')
    current=scenarios.get_scenario(ctx,row['payload']['scenario_id'])
    row['current_scenario_revision']=current['current_revision']
    row['stale']=row['payload']['scenario_revision']!=current['current_revision']
    from .irp_register import summary
    row['register_changed']=row['payload'].get('register')!=summary(ctx,row['study_id'])
    row['stale']=row['stale'] or row['register_changed']
    return normalize(row)
