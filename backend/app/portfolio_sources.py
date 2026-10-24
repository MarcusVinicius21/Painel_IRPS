"""Explicit source fallback decisions; never promote inaccessible finance to facts."""
from .db import normalize


def sources(ctx):
    ctx.require('read')
    from .portal_credentials import load_portal_key
    portal_available=bool(load_portal_key())
    rows=ctx.db.all('''SELECT f.provider,f.phase,count(*) AS current_records,
        count(DISTINCT f.source_id) AS evidence_documents,max(s.consulted_at) AS last_consulted
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
        WHERE f.org_id=:o AND f.classification='official' AND f.is_current AND s.classification='official'
        AND b.government_level='M' AND f.event_date BETWEEN '2025-10-01' AND '2026-09-30'
        GROUP BY f.provider,f.phase ORDER BY f.provider,f.phase''',{'o':ctx.org_id})
    definitions=[
        {'provider':'PNCP','state':'available','origin':'municipal_procurement','official':True,
            'url':'https://pncp.gov.br/api/consulta/swagger-ui/index.html',
            'message':'Registros oficiais locais. Períodos e fases ainda têm lacunas.','fallback':'saved_local_evidence'},
        {'provider':'COMPRAS_GOV','state':'available','origin':'national_price_history','official':True,
            'url':'https://dadosabertos.compras.gov.br/swagger-ui/index.html',
            'message':'Preços nacionais de doze meses. Não representam automaticamente compras municipais.','fallback':'immutable_local_monthly_snapshots'},
        {'provider':'IBGE','state':'available','origin':'context_indicator','official':True,
            'url':'https://servicodados.ibge.gov.br/api/v1/localidades/municipios',
            'message':'Identificação dos municípios. Não comprova compras.','fallback':'saved_identity_census'},
        {'provider':'TCE_MG','state':'blocked','origin':'municipal_procurement','official':True,
            'url':'https://dadosabertos.tce.mg.gov.br/',
            'message':'Ainda falta validar um recurso acessível e seu formato.','fallback':'PNCP_local'},
        {'provider':'PORTAL_IPATINGA','state':'needs_review','origin':'municipal_payment','official':True,
            'url':'https://transparencia.ipatinga.mg.gov.br/despesas-por-pagamentos',
            'message':'A exportação devolveu datas fora do período solicitado. Nenhum pagamento foi importado.','fallback':'no_financial_inference'},
        {'provider':'PORTAL_TIMOTEO','state':'blocked','origin':'municipal_payment','official':True,
            'url':'https://timoteo.mg.gov.br/portaltransparencia',
            'message':'O caminho público retornou acesso negado.','fallback':'no_authentication_bypass'},
        {'provider':'CATMAT_COM_BR','state':'optional','origin':'catalogue_enrichment','official':False,
            'url':'https://catmat.com.br/api-docs','message':'Complemento opcional para materiais. O catálogo local permanece disponível.','fallback':'official_local_catalogue'},
        {'provider':'PORTAL_TRANSPARENCIA_MCP','state':'available' if portal_available else 'blocked','origin':'context_indicator','official':True,
            'url':'https://portaldatransparencia.gov.br/api-de-dados',
            'message':'Consulta CEIS por CNPJ disponível. Não comprova regularidade nem compras municipais.' if portal_available else 'A consulta depende de chave autorizada.',
            'fallback':'not_required'},
    ]
    return normalize({'records':definitions,'municipal_evidence':rows,
        'external_dependencies_required_to_open':False,'new_financial_facts':0,'cross_source_merges_applied':0,
        'municipal_purchase_completeness':None,'notice':'Fontes e fases têm finalidades diferentes. Nenhum bloqueio vira ausência de compras.'})
