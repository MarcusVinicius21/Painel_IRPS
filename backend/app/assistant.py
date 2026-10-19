"""Offline, typed, deterministic tool dispatcher. No arbitrary SQL, URLs or model calls."""
import hashlib,re
from dataclasses import asdict
from decimal import Decimal
from irps_core.domain import Evidence,FactKind
from irps_core.forecast import forecast_from_history
from irps_core.market import summarize_history
from .documents import normalized
from .db import identifier,encoded,normalize
from .schemas import ToolCall
from .security import fail
from . import scenarios

def resolve_question(ctx,question,dataset):
 q=normalized(question);cities=ctx.db.all('SELECT ibge,name FROM municipality');items=ctx.db.all('SELECT id,version,name FROM item_version')
 codes=set(re.findall(r'\b\d{7}\b',q));matched={c['ibge'] for c in cities if re.search(r'\b'+re.escape(normalized(c['name']))+r'\b',q)}|codes
 if len(matched)>1:return None,'Você citou várias cidades. Escolha uma para esta consulta.'
 if codes-{c['ibge'] for c in cities}:return None,'Não encontramos esse código municipal. Confira o município.'
 city=next(iter(matched),None)
 if 'papel higienico' in q:return None,'Papel higiênico ainda não está classificado. Escolha o item na pesquisa.'
 aliases={'papel a4':'papel','aciclovir':'medicamento','limpeza predial':'servico','pavimentacao':'obra','veiculo de 5 lugares':'veiculo'}
 matched_items={i['id'] for i in items if normalized(i['name']) in q or re.search(r'\b'+re.escape(i['id'])+r'\b',q) and i['id']!='papel'}
 matched_items|={v for k,v in aliases.items() if k in q}
 if len(matched_items)>1:return None,'Você citou mais de um item. Escolha uma descrição e uma unidade.'
 item=next(iter(matched_items),None)
 if not item:return None,'Qual produto ou serviço você quer consultar? Use a descrição do catálogo.'
 version=next(i['version'] for i in items if i['id']==item)
 if re.search(r'\b(pagou|pago|pagamentos|paga)\b',q):
  if not city:return None,'Escolha o município para consultar os pagamentos.'
  return ToolCall(tool='net_payments',municipality_ibge=city,item_id=item,item_version=version,dataset=dataset),None
 if any(k in q for k in ('vai precisar','previsao','podera precisar','pode precisar')):
  if not city:return None,'Escolha o município para estimar a quantidade.'
  return ToolCall(tool='forecast',municipality_ibge=city,item_id=item,item_version=version,phase='contratado',dataset=dataset),None
 phase='contratado'
 for word,value in [('publicado','publicado_estimado'),('consumido','consumido'),('entregue','entregue'),('empenhado','empenhado'),('liquidado','liquidado')]:
  if word in q:phase=value
 return ToolCall(tool='search_purchases',municipality_ibge=city,item_id=item,item_version=version,phase=phase,dataset=dataset),None

def selected_facts(ctx,call,include_reversal=False):
 if not call.item_id or not call.item_version:fail(422,'Escolha o item e sua versão.','ITEM_REQUIRED')
 item=ctx.db.one('SELECT * FROM item_version WHERE id=:i AND version=:v',{'i':call.item_id,'v':call.item_version})
 if not item:fail(422,'Este item ou versão não foi encontrado.','UNKNOWN_ITEM')
 if call.municipality_ibge and not ctx.db.one('SELECT ibge FROM municipality WHERE ibge=:i',{'i':call.municipality_ibge}):fail(422,'Este município não foi encontrado.','UNKNOWN_MUNICIPALITY')
 clauses=['f.is_current','f.classification=:class','f.item_id=:item','f.item_version=:version'];params={'class':call.dataset,'item':call.item_id,'version':call.item_version}
 if call.municipality_ibge:clauses.append('f.municipality_ibge=:city');params['city']=call.municipality_ibge
 if call.obligation_id:clauses.append('f.obligation_id=:obligation');params['obligation']=call.obligation_id
 if include_reversal:clauses.append("f.phase IN ('pago','estorno')")
 else:
  if not call.phase:fail(422,'Escolha a situação da compra.','PHASE_REQUIRED')
  clauses.append('f.phase=:phase');params['phase']=call.phase
 rows=ctx.db.all('SELECT f.*,s.url AS source_url,s.consulted_at,b.name AS buyer_name,m.name AS municipality_name,i.unit AS item_unit FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id LEFT JOIN buyer b ON b.id=f.buyer_id LEFT JOIN municipality m ON m.ibge=f.municipality_ibge JOIN item_version i ON i.id=f.item_id AND i.version=f.item_version WHERE '+' AND '.join(clauses)+' ORDER BY f.event_date,f.id LIMIT 1000',params)
 return item,rows

def execute_tool(ctx,call):
 if call.tool=='read_quote':
  ctx.require('quote.read')
  if not call.quote_id:fail(422,'Escolha uma simulação privada.')
  row=ctx.db.one('SELECT v.* FROM private_quote q JOIN quote_version v ON v.org_id=q.org_id AND v.quote_id=q.id AND v.revision=q.current_revision WHERE q.org_id=:o AND q.id=:i',{'o':ctx.org_id,'i':call.quote_id})
  if not row:fail(404,'Esta simulação não está disponível neste espaço.','NOT_FOUND')
  return {'message':'Esta simulação fica no espaço privado da sua empresa.','result':row['result'],'sources':[],'classification':'business_private'}
 if call.tool=='calculate_scenario':
  if not call.scenario_id:fail(422,'Escolha um cenário.')
  result=scenarios.calculate(ctx,call.scenario_id)
  return {'message':'Calculamos as quantidades. Confira as pendências antes de revisar.','result':result,'sources':[]}
 if call.tool=='net_payments' and not call.municipality_ibge:fail(422,'Escolha o município para consultar os pagamentos.')
 item,rows=selected_facts(ctx,call,call.tool=='net_payments')
 sources=list({str(r['source_id']):{'id':str(r['source_id']),'url':r['source_url'],'consulted_at':str(r['consulted_at']),'classification':r['classification']} for r in rows}.values())
 if call.tool=='net_payments':
  # A reversal without its matching payment/obligation cannot be allocated to another city.
  paid_ob={r['obligation_id'] for r in rows if r['phase']=='pago'}
  valid=rows and all(r['amount'] is not None for r in rows) and all(r['obligation_id'] in paid_ob for r in rows if r['phase']=='estorno')
  amount=sum(((-r['amount'] if r['phase']=='estorno' else r['amount']) for r in rows),Decimal('0')) if valid else None
  return {'message':'Pagamentos líquidos documentados. Pagamento não comprova consumo.' if amount is not None else 'Não encontramos pagamentos suficientes neste recorte. Confira a cobertura das fontes.','result':{'amount':str(amount) if amount is not None else None,'currency':'BRL','municipality_ibge':call.municipality_ibge,'item_id':item['id'],'item_version':item['version'],'records':len(rows),'obligations':sorted(paid_ob),'consumption_proven':False},'sources':sources}
 if call.tool=='forecast':
  events=[Evidence(r['event_identity'],r['municipality_ibge'],r['item_id'],str(r['item_version']),r['unit'],FactKind(r['phase']),r['event_date'].year,r['quantity'],r['amount'],r['source_url'],str(r['source_id']),str(r['consulted_at'])) for r in rows if r['municipality_ibge'] and r['unit'] and r['event_date']]
  qty,notices=forecast_from_history(events,item['id'],call.municipality_ibge,item['unit'],FactKind(call.phase))
  return {'message':'Estimativa exploratória baseada em contratos. Ela não comprova consumo.' if qty is not None else 'O histórico ainda não permite estimar esta quantidade. Confira as fontes.','result':{'quantity':str(qty) if qty is not None else None,'unit':item['unit'],'minimum_years':3,'notices':notices,'administrative_approval':False},'sources':sources}
 events=[Evidence(r['event_identity'],r['municipality_ibge'],r['item_id'],str(r['item_version']),r['unit'],FactKind(r['phase']),r['event_date'].year,r['quantity'],r['amount'],r['source_url'],str(r['source_id']),str(r['consulted_at'])) for r in rows if r['municipality_ibge'] and r['unit'] and r['event_date'] and r['phase']!='estorno']
 summary=asdict(summarize_history(events,kind=FactKind(call.phase),item_key=item['id'],unit=item['unit'],years={e.year for e in events},municipalities={e.municipality_ibge for e in events},specification_version=str(item['version']))) if call.phase!='estorno' else None
 return {'message':'Encontramos registros no recorte escolhido. Confira a situação de cada compra.' if rows else 'Não encontramos registros neste recorte. Isso não comprova ausência de compras.','result':{'records':normalize(rows),'count':len(rows),'summary':normalize(summary),'phase':call.phase,'item_id':item['id'],'item_version':item['version'],'unit':item['unit']},'sources':sources}

def ask(ctx,body):
 ctx.require('read');sid=body.session_id
 if sid:
  if not ctx.db.one('SELECT id FROM ai_session WHERE org_id=:o AND id=:i AND actor_id=:a',{'o':ctx.org_id,'i':sid,'a':ctx.actor_id}):fail(404,'Esta conversa não está disponível neste espaço.')
 else:
  sid=identifier();ctx.db.execute('INSERT INTO ai_session(org_id,id,actor_id) VALUES (:o,:i,:a)',{'o':ctx.org_id,'i':sid,'a':ctx.actor_id})
 revision=ctx.db.one('SELECT count(*)::text AS n,max(consulted_at)::text AS t FROM source_observation')
 permission=ctx.org_id+':'+ctx.actor_id+':'+ctx.role+':'+ctx.kind
 cache_key=hashlib.sha256(encoded([permission,revision,body.dataset,body.question]).encode()).hexdigest()
 cached=ctx.db.one('SELECT result FROM ai_cache WHERE org_id=:o AND key=:k AND actor_id=:a AND permission_revision=:p AND expires_at>now()',{'o':ctx.org_id,'k':cache_key,'a':ctx.actor_id,'p':permission})
 if cached:result={**cached['result'],'cache_hit':True}
 else:
  call,clarification=resolve_question(ctx,body.question,body.dataset)
  result={'message':clarification,'result':None,'sources':[],'needs_clarification':True} if clarification else {**execute_tool(ctx,call),'tool':call.model_dump(),'needs_clarification':False}
  result.update(mode='offline',external_calls=0,estimated_external_cost='0',dataset=body.dataset,cache_hit=False)
  ctx.db.execute("INSERT INTO ai_cache(org_id,key,actor_id,permission_revision,result,expires_at) VALUES (:o,:k,:a,:p,CAST(:r AS jsonb),now()+interval '5 minutes') ON CONFLICT(org_id,key) DO UPDATE SET result=EXCLUDED.result,expires_at=EXCLUDED.expires_at",{'o':ctx.org_id,'k':cache_key,'a':ctx.actor_id,'p':permission,'r':encoded(result)})
 ctx.db.execute('INSERT INTO ai_turn(org_id,id,session_id,actor_id,context_revision,question_digest,result) VALUES (:o,:i,:s,:a,:v,:q,CAST(:r AS jsonb))',{'o':ctx.org_id,'i':identifier(),'s':sid,'a':ctx.actor_id,'v':encoded(revision),'q':hashlib.sha256(body.question.encode()).hexdigest(),'r':encoded(result)})
 ctx.audit('assistant.answered',sid,{'mode':'offline','cache':result.get('cache_hit',False)});return {**result,'session_id':sid}

def reserve_budget(ctx,amount,limit,operation):
 """Transactional reservation, including uncertain spend; no paid provider is configured."""
 ctx.require('read');amount=Decimal(amount);limit=Decimal(limit)
 if not amount.is_finite() or not limit.is_finite() or amount<0 or limit<0:fail(422,'O limite informado não é válido.')
 ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:o,0))',{'o':'ai-budget:'+ctx.org_id})
 used=ctx.db.one("SELECT COALESCE(sum(CASE WHEN state='reconciled' THEN billed ELSE amount END),0) AS amount FROM ai_reservation WHERE org_id=:o AND created_at>=date_trunc('month',now())",{'o':ctx.org_id})['amount']
 if used+amount>limit:fail(429,'O limite de uso foi alcançado.','BUDGET_LIMIT')
 rid=identifier();ctx.db.execute("INSERT INTO ai_reservation(org_id,id,actor_id,operation,amount,state) VALUES (:o,:i,:a,:op,:amount,'reserved')",{'o':ctx.org_id,'i':rid,'a':ctx.actor_id,'op':operation,'amount':amount});return rid
