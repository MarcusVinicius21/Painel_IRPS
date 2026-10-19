"""Verified PNCP contracts/results. A result is not a contract, payment or consumption."""
import hashlib,json,re
from datetime import date
from .db import encoded,identifier
from . import sources
from .security import fail

def parse_date(value):
    try:return date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError):return None

def public_supplier(record):
    value=str(record.get('niFornecedor') or '')
    if record.get('tipoPessoa')=='PJ' and re.fullmatch(r'\d{14}',value):
        return {'cnpj':value,'name':record.get('nomeRazaoSocialFornecedor') or 'Nome não informado'}
    return {'cnpj':None,'name':None,'not_exposed':bool(value)}

def redacted_source(value):
    if isinstance(value,list):return [redacted_source(v) for v in value]
    if not isinstance(value,dict):return value
    out={k:redacted_source(v) for k,v in value.items()}
    if value.get('tipoPessoa')=='PF':
        for k in ('niFornecedor','nomeRazaoSocialFornecedor'):out[k]=None
    if value.get('tipoPessoaSubContratada')=='PF':
        for k in ('niFornecedorSubContratado','nomeFornecedorSubContratado'):out[k]=None
    return out

def observe(ctx,provider,url,status,content,data,args):
    safe=encoded(redacted_source(data)).encode()
    return sources.observe(ctx,provider,url,status,safe,{'scope':args,'original_response_sha256':hashlib.sha256(content).hexdigest(),
        'natural_person_identifiers_redacted':True,'partial':True})

def write_fact(ctx,provider,event,record,sid,values):
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':provider+':'+event})
    revision=hashlib.sha256(encoded({'record':redacted_source(record),'item_version':values.get('item_version')}).encode()).hexdigest()
    old=ctx.db.one("SELECT * FROM procurement_fact WHERE provider=:p AND event_identity=:e AND classification='official' AND revision_hash=:h",{'p':provider,'e':event,'h':revision})
    if old:return False
    current=ctx.db.one("SELECT * FROM procurement_fact WHERE provider=:p AND event_identity=:e AND classification='official' AND is_current",{'p':provider,'e':event})
    if current and str(current['org_id'])!=ctx.org_id:return False
    if current:ctx.db.execute('UPDATE procurement_fact SET is_current=false WHERE id=:i AND org_id=:o',{'i':current['id'],'o':ctx.org_id})
    payload={'id':identifier(),'org':ctx.org_id,'provider':provider,'event':event,'revision':revision,'previous':current['id'] if current else None,
        'source':sid,'buyer_id':None,'municipality_ibge':None,'item_id':None,'item_version':None,'unit':None,'quantity':None,'unit_price':None,'amount':None,**values}
    payload['metadata']=encoded(payload['metadata'])
    ctx.db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,supersedes_id,source_id,
       buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata)
       VALUES (:id,:org,'official',:provider,:event,:revision,:previous,:source,:buyer_id,:municipality_ibge,:item_id,:item_version,:description,
       :unit,:quantity,:unit_price,:amount,:phase,:event_date,:obligation_id,CAST(:metadata AS jsonb))""",payload)
    return True

def results(ctx,args,transport=None):
    parent=ctx.db.one("SELECT * FROM procurement_fact WHERE id=:i AND provider='PNCP_ITENS' AND classification='official'",{'i':args['procurement_id']})
    if not parent:fail(404,'O item oficial não está disponível.')
    match=re.fullmatch(r'pncp:(\d{14}):(\d{4}):(\d+):(\d+)',parent['item_id'] or '')
    if not match:fail(422,'Confira a identificação original deste item.')
    cnpj,year,sequence,number=match.groups()
    url=f'https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{year}/{sequence}/itens/{number}/resultados'
    url,status,content,data=sources.cached_get(ctx,'PNCP_RESULTADOS',url,transport=transport)
    if data is None:data=[]
    if not isinstance(data,list) or len(data)>2000:raise sources.SourceFault('INVALID_RESULT_FORMAT')
    sid=observe(ctx,'PNCP_RESULTADOS',url,status,content,data,args);new=0
    for record in data:
        sequence_result=record.get('sequencialResultado')
        if not isinstance(sequence_result,int):continue
        cancelled=bool(record.get('dataCancelamento')) or str(record.get('situacaoCompraItemResultadoId'))=='2'
        active=str(record.get('situacaoCompraItemResultadoId'))=='1' and not cancelled
        new+=write_fact(ctx,'PNCP_RESULTADOS',parent['event_identity']+':result:'+str(sequence_result),record,sid,{
            'buyer_id':parent['buyer_id'],'municipality_ibge':parent['municipality_ibge'],'item_id':parent['item_id'],
            'item_version':parent['item_version'],'description':parent['description'],'unit':parent['unit'],
            'quantity':sources.documented_number(record.get('quantidadeHomologada')) if active else None,
            'unit_price':sources.documented_number(record.get('valorUnitarioHomologado')) if active else None,
            'amount':sources.documented_number(record.get('valorTotalHomologado')) if active else None,
            'phase':'homologado','event_date':parse_date(record.get('dataResultado')),'obligation_id':parent['obligation_id'],
            'metadata':{'record_level':'item','parent_id':str(parent['id']),'supplier':public_supplier(record),'cancelled':cancelled,
                'eligible_result':active,'source_phase':record.get('situacaoCompraItemResultadoNome'),'result_status':record.get('situacaoCompraItemResultadoId'),
                'category':parent['metadata'].get('category'),'modality':parent['metadata'].get('modality'),
                'currency':'foreign_or_unknown' if record.get('moedaEstrangeira') else 'BRL',
                'publication_date':str(parent['event_date']) if parent['event_date'] else None,'quantity_is_consumption':False}})
    return {'provider':'PNCP_RESULTADOS','records':len(data),'new_revisions':new,'source_id':str(sid),'state':'partial','pages_fetched':1,
        'expected_pages':1,'scope':args,'phase':'homologado','payments_collected':False,'pagination':'Endpoint não recebe paginação no contrato consultado.'}

def contracts(ctx,args,transport=None):
    params={'dataInicial':date.fromisoformat(args['start_date']).strftime('%Y%m%d'),'dataFinal':date.fromisoformat(args['end_date']).strftime('%Y%m%d'),
        'pagina':args.get('page',1),'tamanhoPagina':args.get('size',10),'cnpjOrgao':args['cnpj']}
    url,status,content,data=sources.cached_get(ctx,'PNCP_CONTRATOS','https://pncp.gov.br/api/consulta/v1/contratos',params,transport)
    if data is None:data={'data':[],'totalPaginas':0}
    if not isinstance(data,dict) or not isinstance(data.get('data'),list):raise sources.SourceFault('INVALID_CONTRACT_FORMAT')
    sid=observe(ctx,'PNCP_CONTRATOS',url,status,content,data,args);new=0
    for record in data['data'][:args.get('size',10)]:
        entity=record.get('orgaoEntidade') or {};unit=record.get('unidadeOrgao') or {};cnpj=str(entity.get('cnpj') or '')
        if cnpj!=args['cnpj'] or not record.get('numeroControlePNCP'):continue
        code=str(unit.get('codigoIbge') or '')
        known=ctx.db.one('SELECT ibge FROM municipality WHERE ibge=:c',{'c':code})
        external=cnpj+':'+str(unit.get('codigoUnidade',''))
        ctx.db.execute("INSERT INTO buyer(id,org_id,cnpj,name,unit_code,municipality_ibge,government_level,classification,external_identity) VALUES (:i,:o,:c,:n,:u,:m,:g,'official',:e) ON CONFLICT(classification,external_identity) DO NOTHING",{'i':identifier(),'o':ctx.org_id,'c':cnpj,'n':entity.get('razaoSocial') or 'Nome não informado','u':str(unit.get('codigoUnidade','')),'m':code if known else None,'g':entity.get('esferaId'),'e':external})
        buyer=ctx.db.one("SELECT id FROM buyer WHERE classification='official' AND external_identity=:e",{'e':external})['id']
        instrument=record.get('tipoContrato') or {};is_commitment=instrument.get('id')==7
        new+=write_fact(ctx,'PNCP_CONTRATOS',record['numeroControlePNCP']+':contract',record,sid,{
            'buyer_id':buyer,'municipality_ibge':code if known else None,'description':record.get('objetoContrato') or 'Objeto não informado',
            'amount':sources.documented_number(record.get('valorInicial')),'phase':'empenhado' if is_commitment else 'contratado',
            'event_date':parse_date(record.get('dataAssinatura')),
            'obligation_id':record.get('numeroControlePncpCompra') or record.get('numeroControlePNCPCompra') or record['numeroControlePNCP'],
            'metadata':{'record_level':'contract','supplier':public_supplier(record),'instrument':instrument,'category':(record.get('categoriaProcesso') or {}).get('nome'),
                'publication_date':record.get('dataPublicacaoPncp'),'contract_identity':record['numeroControlePNCP'],
                'purchase_identity':record.get('numeroControlePncpCompra') or record.get('numeroControlePNCPCompra'),
                'amount_kind':'valorInicial','global_value':sources.documented_number(record.get('valorGlobal')),
                'receipt':record.get('receita'),'items_unavailable':True,'quantity_is_consumption':False,
                'commitment_instrument_only':is_commitment,'financial_execution_proven':False}})
    return {'provider':'PNCP_CONTRATOS','records':len(data['data']),'new_revisions':new,'source_id':str(sid),'state':'partial',
        'pages_fetched':1,'expected_pages':data.get('totalPaginas'),'scope':args,'quantities_collected':False,'unit_prices_collected':False}
