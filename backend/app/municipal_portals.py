"""Institutional portal inventory: discovery is not collection completeness."""
from urllib.parse import urlparse


PORTALS = {
    '3131307': {'name':'Ipatinga', 'cnpj':'19876424000142',
        'institutional_url':'https://www.ipatinga.mg.gov.br/transparencia',
        'consultation_url':'https://transparencia.ipatinga.mg.gov.br/despesas-por-pagamentos',
        'delegated_url':'https://dadosabertos-portalfacil.azurewebsites.net/97/pagamentos',
        'provider':'ACTCON_IPATINGA', 'state':'period_filter_unverified',
        'reason_codes':['SOURCE_PERIOD_MISMATCH','FINANCIAL_IDENTITY_REQUIRES_REVIEW'],
        'schema_version':'observed-payments-2026-10-24', 'phase':'pago'},
    '3168705': {'name':'Timóteo', 'cnpj':'19875020000134',
        'institutional_url':'https://timoteo.mg.gov.br/portaltransparencia',
        'consultation_url':'https://transparencia.timoteo.mg.gov.br/licitacoes',
        'delegated_url':'https://transparencia.betha.cloud/',
        'provider':'BETHA_TIMOTEO', 'state':'anonymous_access_denied',
        'reason_codes':['HTTP_403','EXPORT_SCHEMA_NOT_VERIFIED'],
        'schema_version':None, 'phase':None},
}


def inventory(municipalities):
    """Every census city appears; unsupported cities are explicitly undiscovered.

    The curated institutional links are evidence from M04_03, not permission to
    fetch arbitrary redirects or enable an unverified connector.
    """
    rows=[];seen=set()
    for city in municipalities:
        code=city['ibge']
        if not isinstance(code,str) or len(code)!=7 or not code.isdigit():
            raise ValueError('INVALID_MUNICIPALITY')
        if code in seen:continue
        seen.add(code)
        known=PORTALS.get(code)
        row={'municipality_ibge':code,'name':city['name'],'state':'not_discovered',
            'priority':'official_gap_complement','can_ingest':False,'coverage':None,
            'verified_months':[], 'record_count':None,'rate_limit':None,
            'license_verified':False,'access':'anonymous_public_consultation_only'}
        if known:
            row.update(known)
            for field in ('institutional_url','consultation_url','delegated_url'):
                url=urlparse(row[field])
                if url.scheme!='https' or url.username or url.password or url.query:
                    raise ValueError('UNSAFE_CURATED_PORTAL')
            row['schema_observed']=known['schema_version'] is not None
            row['categories']={key:{'state':'not_verified','coverage':None}
                for key in ('procurements','contracts','commitments','liquidations','payments')}
            if code=='3131307':
                row['categories']['payments']['state']='documented_schema_period_mismatch'
        rows.append(row)
    return {'schema_version':1,'municipalities':rows,'municipality_count':len(rows),
        'enabled_connectors':0,'municipal_purchase_completeness':None}
