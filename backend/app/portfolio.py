"""Tenant scoped, local-first portfolio over immutable national catalogue snapshots."""
from datetime import date
from typing import Literal
from pydantic import Field,model_validator
from .schemas import Strict,Code
from .db import normalize,identifier,encoded
from .security import fail
from .portfolio_rules import VERSION


class Preference(Strict):
    group:str=Field(default='01',pattern=r'^(0[1-9]|1[0-9]|20)$')
    q:str=Field(default='',max_length=150)
    kind:Literal['CATMAT','CATSER']|None=None
    technical:Literal['DIRECT_TECHNICAL','NEEDS_TECH_REVIEW']|None=None
    active:bool|None=None
    subgroup:str=Field(default='',max_length=80)
    municipalities:list[Code]=Field(default_factory=list,max_length=118)
    start:date=date(2025,10,1)
    end:date=date(2026,9,30)
    phase:Literal['publicado_estimado','homologado','contratado','empenhado','liquidado','pago']='homologado'
    @model_validator(mode='after')
    def period(self):
        if self.end<self.start or self.end>date.today() or (self.end-self.start).days>366:raise ValueError('Escolha até doze meses passados.')
        return self


def run(ctx):
    return ctx.db.one('SELECT * FROM portfolio_run WHERE org_id=:o AND rule_version=:v ORDER BY created_at DESC,id DESC LIMIT 1',{'o':ctx.org_id,'v':VERSION})


def groups(ctx):
    ctx.require('read');selected=run(ctx)
    if not selected:return {'records':[],'state':'not_initialized','notice':'O portfólio ainda não foi preparado neste espaço.'}
    rows=ctx.db.all('''SELECT g.*,count(l.code) FILTER(WHERE l.technical_status='DIRECT_TECHNICAL') AS direct_codes,
        count(l.code) FILTER(WHERE l.technical_status='NEEDS_TECH_REVIEW') AS review_codes,
        count(l.code) FILTER(WHERE l.commercial_status='COMMERCIAL_CONFIRMED') AS commercial_confirmed,
        array_agg(DISTINCT l.subgroup) FILTER(WHERE l.technical_status IN ('DIRECT_TECHNICAL','NEEDS_TECH_REVIEW')) AS subgroups
        FROM portfolio_group g LEFT JOIN portfolio_code_link l ON l.org_id=g.org_id AND l.run_id=g.run_id AND l.group_code=g.code
        WHERE g.org_id=:o AND g.run_id=:r GROUP BY g.org_id,g.run_id,g.code ORDER BY g.code''',{'o':ctx.org_id,'r':selected['id']})
    return normalize({'records':rows,'run_id':selected['id'],'rule_version':selected['rule_version'],'state':'available',
        'notice':'Candidatos técnicos. A oferta comercial de cada código ainda precisa de confirmação.'})


def codes(ctx,group,q='',kind=None,active=None,technical=None,subgroup=None,offset=0,limit=25):
    ctx.require('read');selected=run(ctx)
    if not selected:return {'records':[],'total':0,'state':'not_initialized','next_offset':None}
    if group not in {f'{i:02}' for i in range(1,21)}:fail(422,'Escolha um dos vinte grupos.')
    if not 0<=offset<=500000 or not 1<=limit<=50:fail(422,'Confira a página de resultados.')
    clauses=['l.org_id=:o','l.run_id=:r','l.group_code=:g',"l.technical_status IN ('DIRECT_TECHNICAL','NEEDS_TECH_REVIEW')"]
    params={'o':ctx.org_id,'r':selected['id'],'g':group,'off':offset,'n':limit}
    if q.strip():
        clauses.append('(e.code=:exact OR e.search_vector @@ plainto_tsquery(\'portuguese\',:q))');params.update(exact=q.strip(),q=q.strip())
    for key,value,clause in [('kind',kind,'s.kind=:kind'),('active',active,'e.active=:active'),
        ('technical',technical,'l.technical_status=:technical'),('subgroup',subgroup,'l.subgroup=:subgroup')]:
        if value is not None:clauses.append(clause);params[key]=value
    join=''' FROM portfolio_code_link l JOIN national_catalogue_entry e ON e.snapshot_id=l.snapshot_id AND e.code=l.code
        JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id WHERE '''+' AND '.join(clauses)
    total=ctx.db.one('SELECT count(*) AS n'+join,params)['n']
    rows=ctx.db.all('''SELECT e.snapshot_id,e.code,e.name,e.active,e.class_name,e.pdm_name,s.kind,s.sha256 AS snapshot_sha256,
        l.technical_status,l.commercial_status,l.subgroup,l.reason,l.multiple_group_reason'''+join+' ORDER BY s.kind,e.code LIMIT :n OFFSET :off',params)
    return normalize({'records':rows,'total':total,'offset':offset,'limit':limit,'next_offset':offset+limit if offset+limit<total else None,
        'run_id':selected['id'],'rule_version':selected['rule_version'],'group':group,'commercial_confirmation_implied':False})


def preference_get(ctx):
    ctx.require('read')
    row=ctx.db.one('SELECT id,payload,created_at FROM portfolio_preference WHERE org_id=:o AND actor_id=:a ORDER BY created_at DESC,id DESC LIMIT 1',{'o':ctx.org_id,'a':ctx.actor_id})
    return normalize(row or {'payload':Preference().model_dump(),'id':None})


def preference_save(ctx,body):
    ctx.require('scenario.write')
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(body.municipalities)-known:fail(422,'Confira os municípios selecionados.')
    payload=body.model_dump();payload['municipalities']=sorted(set(body.municipalities));pid=identifier()
    ctx.db.execute('INSERT INTO portfolio_preference(org_id,id,actor_id,payload) VALUES (:o,:i,:a,CAST(:p AS jsonb))',
        {'o':ctx.org_id,'i':pid,'a':ctx.actor_id,'p':encoded(payload)})
    ctx.audit('portfolio.filters_saved',pid,{'group':body.group,'rule_version':VERSION})
    return {'id':pid,'saved':True}
