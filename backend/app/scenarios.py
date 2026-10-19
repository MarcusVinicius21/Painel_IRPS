"""Adapters around the unchanged V4. All decimal computation stays in that core."""
import hashlib,json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from fastapi import HTTPException
from irps_core.domain import Item,QuantityInput,NeedResult,Status,ValidationError
from irps_core.forecast import calculate_need
from irps_core.allocate import allocate_independent,allocate_total,AllocationCandidate
from irps_core.tender import ReferencePrice,TenderLine,calculate_tender_value
from irps_core.finance import QuoteInput,calculate_quote
from .db import encoded,identifier,normalize
from .security import fail
from .schemas import Snapshot,ScenarioCreate

def core_hash():
 files=sorted((Path(__file__).resolve().parents[1]/'irps_core').glob('*.py'))
 return hashlib.sha256(''.join(p.name+':'+hashlib.sha256(p.read_bytes()).hexdigest() for p in files).encode()).hexdigest()

def jsonable(v):return json.loads(encoded(v))

def get_scenario(ctx,sid,revision=None,lock=False):
 row=ctx.db.one('SELECT * FROM scenario WHERE org_id=:o AND id=:i'+(' FOR UPDATE' if lock else ''),{'o':ctx.org_id,'i':sid})
 if not row:fail(404,'Este cenário não está disponível neste espaço.','NOT_FOUND')
 rev=revision or row['current_revision']
 version=ctx.db.one('SELECT snapshot,created_at FROM scenario_version WHERE org_id=:o AND scenario_id=:i AND revision=:v',{'o':ctx.org_id,'i':sid,'v':rev})
 if not version:fail(404,'Esta versão não está disponível.','NOT_FOUND')
 return {**row,'revision':rev,'snapshot':version['snapshot'],'version_created_at':version['created_at']}

def etag(value):
 if value is None:fail(428,'Abra a versão atual antes de salvar.','VERSION_REQUIRED')
 try:return int(value.strip('"'))
 except ValueError:fail(422,'A versão informada não é válida.','INVALID_VERSION')

def assert_version(row,expected):
 if row['current_revision']!=expected:fail(409,'Outra pessoa alterou este cenário. Abra a versão atual.','VERSION_CONFLICT')

def selection_digest(snapshot):
 return hashlib.sha256(encoded({k:snapshot[k] for k in ('mode','participants','items','allocations','inputs','period')}).encode()).hexdigest()

def validate_snapshot(ctx,snapshot):
 raw=jsonable(snapshot.model_dump() if hasattr(snapshot,'model_dump') else snapshot)
 validated=Snapshot.model_validate({k:v for k,v in raw.items() if k not in ('distribution_confirmation','review')})
 raw=jsonable(validated.model_dump())
 if len(raw['participants'])!=len(set(raw['participants'])):fail(422,'Um município foi selecionado mais de uma vez.')
 refs=[(x['id'],x['version']) for x in raw['items']]
 if len(refs)!=len(set(refs)) or len({x[0] for x in refs})!=len(refs):fail(422,'Escolha apenas uma versão de cada item.')
 known={x['ibge'] for x in ctx.db.all('SELECT ibge FROM municipality')}
 if set(raw['participants'])-known:fail(422,'Há um município sem identidade confirmada.','UNKNOWN_MUNICIPALITY')
 catalog={(x['id'],x['version']):x for x in ctx.db.all('SELECT * FROM item_version')}
 if set(refs)-set(catalog):fail(422,'Há um item sem versão confirmada.','UNKNOWN_ITEM')
 keys={c+'|'+i for c in raw['participants'] for i,v in refs}
 if set(raw['inputs'])-keys:fail(422,'Há parâmetros de município ou item fora desta seleção.','EXTRA_PARAMETERS')
 ids={i for i,v in refs}
 if (set(raw['prices'])|set(raw['allocations']))-ids:fail(422,'Há preços ou critérios de itens fora desta seleção.')
 for i,p in raw['prices'].items():
  item=catalog[(i,next(v for k,v in refs if k==i))]
  if p['unit']!=item['unit'] or p['item_version']!=item['version']:fail(422,'O preço pertence a outra unidade ou versão do item.','PRICE_MISMATCH')
 for i,a in raw['allocations'].items():
  if len(a['candidates'])!=len(set(c['ibge'] for c in a['candidates'])) or set(c['ibge'] for c in a['candidates'])!=set(raw['participants']):fail(422,'Os critérios precisam corresponder aos municípios selecionados.')
 return raw

def save_version(ctx,sid,revision,snapshot):
 ctx.db.execute('INSERT INTO scenario_version(org_id,scenario_id,revision,snapshot,created_by) VALUES (:o,:i,:v,CAST(:s AS jsonb),:a)',{'o':ctx.org_id,'i':sid,'v':revision,'s':encoded(snapshot),'a':ctx.actor_id})
 ctx.db.execute('INSERT INTO scenario_participant(org_id,scenario_id,revision,ibge) VALUES (:o,:i,:v,:c)',[{'o':ctx.org_id,'i':sid,'v':revision,'c':c} for c in snapshot['participants']])
 ctx.db.execute('INSERT INTO scenario_item(org_id,scenario_id,revision,item_id,item_version) VALUES (:o,:i,:v,:k,:kv)',[{'o':ctx.org_id,'i':sid,'v':revision,'k':i['id'],'kv':i['version']} for i in snapshot['items']])

def create_scenario(ctx,body):
 ctx.require('scenario.write');snapshot=validate_snapshot(ctx,body.snapshot);sid=identifier()
 ctx.db.execute('INSERT INTO scenario(org_id,id,title,current_revision,classification,created_by) VALUES (:o,:i,:t,1,:c,:a)',{'o':ctx.org_id,'i':sid,'t':body.title,'c':body.classification,'a':ctx.actor_id})
 save_version(ctx,sid,1,snapshot);ctx.audit('scenario.created',sid)
 return get_scenario(ctx,sid)

def update_scenario(ctx,sid,snapshot,expected):
 ctx.require('scenario.write');old=get_scenario(ctx,sid,lock=True);assert_version(old,expected)
 raw=validate_snapshot(ctx,snapshot)
 if old['snapshot'].get('distribution_confirmation')==selection_digest(raw):raw['distribution_confirmation']=selection_digest(raw)
 rev=old['current_revision']+1;save_version(ctx,sid,rev,raw)
 ctx.db.execute('UPDATE scenario SET current_revision=:v WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':sid,'v':rev})
 ctx.audit('scenario.updated',sid,{'revision':rev});return get_scenario(ctx,sid)

def confirm_distribution(ctx,sid,expected):
 ctx.require('scenario.review');row=get_scenario(ctx,sid,lock=True);assert_version(row,expected);s=row['snapshot']
 if s['mode']!='B':fail(422,'Este cenário usa a necessidade individual.')
 catalog={(x['id'],x['version']):x for x in ctx.db.all('SELECT * FROM item_version')}
 try:
  for ref in s['items']:
   a=s['allocations'].get(ref['id'])
   if not a:fail(422,'Informe a quantidade global e os critérios de cada item.')
   allocate_total(Decimal(a['target']),[AllocationCandidate(c['ibge'],Decimal(c['weight']),Decimal(c['floor']),Decimal(c['ceiling']),c['criteria_source']) for c in a['candidates']],catalog[(ref['id'],ref['version'])]['step'])
 except ValidationError as e:fail(422,str(e),'ALLOCATION_INVALID')
 s={**s,'distribution_confirmation':selection_digest(s)};s.pop('review',None)
 rev=row['current_revision']+1;save_version(ctx,sid,rev,s);ctx.db.execute('UPDATE scenario SET current_revision=:v WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':sid,'v':rev});ctx.audit('scenario.distribution_confirmed',sid,{'revision':rev})
 return get_scenario(ctx,sid)

def synthetic_scenario(ctx,body):
 cities=ctx.db.all('SELECT ibge FROM municipality ORDER BY ibge LIMIT :n',{'n':body.participants})
 items=ctx.db.all('SELECT * FROM item_version WHERE classification=\'synthetic\' ORDER BY CASE WHEN id IN (\'papel\',\'medicamento\',\'veiculo\',\'servico\',\'obra\') THEN 0 ELSE 1 END,id,version LIMIT :n',{'n':body.items})
 inputs={};prices={}
 for item in items:
  prices[item['id']]={'item_version':item['version'],'unit':item['unit'],'unit_price':str(item['example_price']),'source_url':'https://example.invalid/irps/dados-ficticios','reference_date':'2026-10-19','justification':'Preço fictício para verificar o funcionamento local.'}
  for idx,city in enumerate(cities):
   inputs[city['ibge']+'|'+item['id']]={'driver_name':'Unidades de teste','driver_count':str(10+idx),'units_per_driver':'2','driver_source':'Parâmetro artificial; não representa o município.','rate_source':'Taxa artificial para teste.','safety_rate':'0','available_stock':'1','confirmed_incoming':'0','floor':'0','ceiling':'1000000','justification':'Dados fictícios inseridos explicitamente no ambiente local.'}
 snapshot=Snapshot.model_validate({'period':'2027 · teste','mode':'A','participants':[c['ibge'] for c in cities],'items':[{'id':i['id'],'version':i['version']} for i in items],'inputs':inputs,'prices':prices})
 return create_scenario(ctx,ScenarioCreate(title=body.title,classification='synthetic',snapshot=snapshot))

def calculate(ctx,sid,revision=None):
 ctx.require('scenario.calculate');row=get_scenario(ctx,sid,revision);s=row['snapshot'];cid=identifier()
 catalog={(x['id'],x['version']):x for x in ctx.db.all('SELECT * FROM item_version')}
 lines=[];totals=[];blocked=0;unpriced=0;known_total=Decimal('0');item_summary=[]
 for ref in s['items']:
  itemrow=catalog[(ref['id'],ref['version'])];item=Item(ref['id'],itemrow['name'],itemrow['unit'],itemrow['family'],specification_version=str(ref['version']),quantity_step=itemrow['step'])
  needs=[]
  if s['mode']=='B':
   a=s['allocations'].get(item.key);alloc=None;reason='Confirme os critérios após escolher os municípios.'
   if a and s.get('distribution_confirmation')==selection_digest(s):
    try:alloc=allocate_total(Decimal(a['target']),[AllocationCandidate(c['ibge'],Decimal(c['weight']),Decimal(c['floor']),Decimal(c['ceiling']),c['criteria_source']) for c in a['candidates']],item.quantity_step)
    except ValidationError as e:reason=str(e)
   for city in s['participants']:
    needs.append(NeedResult(city,item.key,s['period'],alloc.assigned[city] if alloc else None,item.unit,Status.READY_FOR_REVIEW if alloc else Status.BLOCKED,'Distribuição da quantidade global.' if alloc else '',() if alloc else (reason,),str(ref['version'])))
  else:
   for city in s['participants']:
    raw=s['inputs'].get(city+'|'+item.key)
    if not raw or raw.get('available_stock') is None or raw.get('confirmed_incoming') is None:
     needs.append(NeedResult(city,item.key,s['period'],None,item.unit,Status.INSUFFICIENT_DATA,'',('Confira o estoque e os recebimentos previstos. Informação ausente não vale zero.',),str(ref['version'])));continue
    pars={k:(Decimal(v) if k in ('driver_count','units_per_driver','safety_rate','available_stock','confirmed_incoming','floor','ceiling') and v is not None else v) for k,v in raw.items()}
    needs.append(calculate_need(QuantityInput(city,item,s['period'],**pars)))
  if all(n.status==Status.READY_FOR_REVIEW for n in needs):
   independent=allocate_independent(needs,set(s['participants']))
   item_summary.append({'item_id':item.key,'unit':item.unit,'quantity':str(independent.total),'state':'para_revisao'})
  else:item_summary.append({'item_id':item.key,'unit':item.unit,'quantity':None,'state':'dados_insuficientes'})
  p=s['prices'].get(item.key)
  for n in needs:
   price=None;value=None
   if n.quantity is not None and n.quantity>Decimal('9999999999999999.99999999'):fail(422,'A quantidade excede o limite de armazenamento. Revise a base e a taxa.','QUANTITY_RANGE')
   if n.status!=Status.READY_FOR_REVIEW:blocked+=1
   if not p:unpriced+=1
   if n.quantity is not None and n.status==Status.READY_FOR_REVIEW and p:
    if n.quantity*Decimal(p['unit_price'])>Decimal('9999999999999999999999.99'):fail(422,'O valor estimado excede o limite de armazenamento. Revise os parâmetros.','VALUE_RANGE')
    price=ReferencePrice(item.key,str(p['item_version']),p['unit'],Decimal(p['unit_price']),p['source_url'],p['reference_date'],True)
    result=calculate_tender_value([TenderLine(n.municipality_ibge,item.key,str(ref['version']),item.unit,n.quantity,price)])
    value=result.total_brl;known_total+=value
   lines.append({'o':ctx.org_id,'cid':cid,'ibge':n.municipality_ibge,'item':item.key,'version':ref['version'],'unit':item.unit,'quantity':n.quantity,'price':price.unit_price_brl if price else None,'value':value,'state':n.status.value,'memory':encoded({'formula':n.calculation,'notices':list(n.notices),'parameters':s['inputs'].get(n.municipality_ibge+'|'+item.key),'distribution':s['allocations'].get(item.key) if s['mode']=='B' else None,'price_source':p,'administrative_approval':False})})
 summary={'participants':len(s['participants']),'items':len(s['items']),'lines':len(lines),'blocked_lines':blocked,'unpriced_lines':unpriced,'known_value':str(known_total),'total':str(known_total) if not blocked and not unpriced else None,'item_totals':item_summary,'classification':row['classification'],'period':s['period'],'mode':s['mode'],'reviewed':bool(s.get('review')),'administrative_approval':False}
 ctx.db.execute('INSERT INTO calculation(org_id,id,scenario_id,revision,core_sha256,summary) VALUES (:o,:i,:s,:v,:h,CAST(:m AS jsonb))',{'o':ctx.org_id,'i':cid,'s':sid,'v':row['revision'],'h':core_hash(),'m':encoded(summary)})
 for start in range(0,len(lines),1000):ctx.db.execute('INSERT INTO calculation_line(org_id,calculation_id,ibge,item_id,item_version,unit,quantity,unit_price,value,state,memory) VALUES (:o,:cid,:ibge,:item,:version,:unit,:quantity,:price,:value,:state,CAST(:memory AS jsonb))',lines[start:start+1000])
 ctx.audit('scenario.calculated',sid,{'revision':row['revision'],'lines':len(lines),'calculation_id':cid})
 return {'id':cid,'scenario_id':sid,'revision':row['revision'],'core_sha256':core_hash(),'summary':summary}

def review(ctx,sid,expected):
 ctx.require('scenario.review');row=get_scenario(ctx,sid,lock=True);assert_version(row,expected)
 latest=ctx.db.one('SELECT summary FROM calculation WHERE org_id=:o AND scenario_id=:s AND revision=:v ORDER BY created_at DESC LIMIT 1',{'o':ctx.org_id,'s':sid,'v':expected})
 if not latest or latest['summary']['total'] is None:fail(422,'Calcule e resolva as pendências antes de registrar a revisão.')
 s={**row['snapshot'],'review':{'actor_id':ctx.actor_id,'meaning':'Revisão interna de planejamento; não autoriza despesa.'}};rev=expected+1
 save_version(ctx,sid,rev,s);ctx.db.execute('UPDATE scenario SET current_revision=:v WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':sid,'v':rev});ctx.audit('scenario.reviewed',sid,{'revision':rev});return get_scenario(ctx,sid)

def quote(ctx,body,qid=None,expected=None):
 ctx.require('quote.write');qid=qid or identifier();rev=1
 if expected is not None:
  current=ctx.db.one('SELECT * FROM private_quote WHERE org_id=:o AND id=:i FOR UPDATE',{'o':ctx.org_id,'i':qid})
  if not current:fail(404,'Esta simulação não está disponível neste espaço.')
  assert_version(current,expected);rev=expected+1
 else:ctx.db.execute('INSERT INTO private_quote(org_id,id,current_revision,created_by) VALUES (:o,:i,1,:a)',{'o':ctx.org_id,'i':qid,'a':ctx.actor_id})
 result=asdict(calculate_quote(QuoteInput(**body.model_dump())))
 ctx.db.execute('INSERT INTO quote_version(org_id,quote_id,revision,inputs,result) VALUES (:o,:i,:v,CAST(:b AS jsonb),CAST(:r AS jsonb))',{'o':ctx.org_id,'i':qid,'v':rev,'b':encoded(body.model_dump()),'r':encoded(result)})
 ctx.db.execute('UPDATE private_quote SET current_revision=:v WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':qid,'v':rev});ctx.audit('quote.calculated',qid,{'revision':rev})
 return {'id':qid,'revision':rev,'inputs':jsonable(body.model_dump()),'result':normalize(result),'classification':'business_private'}
