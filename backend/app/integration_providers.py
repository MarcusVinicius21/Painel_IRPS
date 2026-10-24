"""One allowlisted facade over existing adapters; no raw MCP or arbitrary URLs."""
from .security import fail
from .db import normalize

def definitions():
    from .portal_credentials import load_portal_key
    portal_key=bool(load_portal_key())
    return [
      {'provider':'PNCP','official':True,'operational':True,'installed':True,'tested':True,'blocked':None,
       'adapter':'existing_durable_history','scope':'publication/result/contract/ata; phases remain separate'},
      {'provider':'COMPRAS_GOV','official':True,'operational':True,'installed':True,'tested':True,'blocked':None,
       'adapter':'existing_monthly_prices','scope':'national prices, not municipal purchase coverage'},
      {'provider':'IBGE','official':True,'operational':True,'installed':True,'tested':True,'blocked':None,
       'adapter':'existing_identity','scope':'municipal identity only'},
      {'provider':'CATMAT_COM_BR','official':False,'operational':True,'installed':True,'tested':True,'blocked':None,
       'adapter':'bounded_secondary_enrichment','scope':'CATMAT only; exact portfolio snapshot/code required'},
      {'provider':'LICITEI','official':False,'operational':False,'installed':True,'tested':True,'blocked':'AGPL_AND_INDEX_RUNTIME',
       'adapter':'isolated_stdio_poc','scope':'85 tools discovered; queries not validated; no source merge'},
      {'provider':'PORTAL_TRANSPARENCIA','official':True,'operational':portal_key,'installed':True,'tested':True,'blocked':None if portal_key else 'KEY_REQUIRED',
       'adapter':'cgu_bounded_cnpj_and_isolated_stdio','scope':'CEIS single page; no clearance or municipal purchase inference'},
      {'provider':'THIAGOSY_PNCP','official':False,'operational':False,'installed':False,'tested':False,'blocked':'LICENSE_NOT_IDENTIFIED',
       'adapter':'official_PNCP_alternative','scope':'No unlicensed source copied'},
      *[{'provider':name,'official':False,'operational':False,'installed':False,'tested':False,'blocked':'NOT_ADOPTED',
         'adapter':None,'scope':'No additional unique validated capability installed'} for name in ['MCP_BRASIL','LICINEXUS','QUERIDO_DIARIO']]]

def registry(ctx):
    ctx.require('read')
    evidence=ctx.db.all('''SELECT provider,count(*) AS documents,max(consulted_at) AS last_consulted
                         FROM source_observation WHERE org_id=:o AND classification='official'
                         GROUP BY provider ORDER BY provider''',{'o':ctx.org_id})
    return normalize({'records':definitions(),'evidence':evidence,'scope_groups':20,'raw_mcp_exposed':False,
      'identity_method':'provider + original event/document identity + immutable revision; never text-only merging',
      'municipal_purchase_completeness':None})

def query(ctx,provider,group,code,snapshot=None,transport=None):
    ctx.require('read')
    entry=next((p for p in definitions() if p['provider']==provider),None)
    if entry is None:fail(404,'Esta fonte não está disponível.')
    if not entry['operational']:fail(503,'Esta fonte ainda depende de configuração ou revisão.',entry['blocked'])
    if provider!='CATMAT_COM_BR':fail(422,'Consulte esta fonte pela pesquisa e pelo histórico existentes.')
    if group not in {f'{i:02}' for i in range(1,21)} or not snapshot:fail(422,'Escolha um código e sua versão no portfólio.')
    from . import portfolio,national_catalogue,catalogue_enrichment
    run=portfolio.run(ctx)
    match=ctx.db.one('''SELECT 1 FROM portfolio_code_link WHERE org_id=:o AND run_id=:r AND group_code=:g
      AND snapshot_id=:s AND code=:c AND technical_status IN ('DIRECT_TECHNICAL','NEEDS_TECH_REVIEW')''',
      {'o':ctx.org_id,'r':run['id'] if run else None,'g':group,'s':snapshot,'c':code})
    if not match:fail(422,'Este código não é candidato do grupo selecionado.')
    local=national_catalogue.entry(ctx,snapshot,code)
    result=catalogue_enrichment.fetch('item',kind=local['kind'],code=code,official_description=local['name'],transport=transport)
    return {**result,'snapshot_id':snapshot,'group':group,'commercial_confirmation_implied':False}
