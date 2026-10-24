"""Monitoring scope is not consortium membership or observed purchase coverage."""
import hashlib,json,unicodedata
from .db import encoded,normalize
from .security import fail

ALIASES={'Córrego Bom Jesus':'Córrego do Bom Jesus','Jacuri':'São José do Jacuri',
         'Miracena (RJ)':'Miracema','São Francisco do Itabapoana (RJ)':'São Francisco de Itabapoana'}

def key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c)).strip()

def reconcile(origin,reference,official):
    if len(origin)!=118 or len(reference)!=118:raise ValueError('Exactly 118 requested targets required')
    lookup={str(r['id']):r for r in official};names={key(r['name']):r for r in reference}
    if len(names)!=118 or len({str(r['id']) for r in reference})!=118:raise ValueError('Duplicate reference identity')
    result=[]
    for row in origin:
        original=row['municipio_nome_origem'];canonical=ALIASES.get(original,original)
        ref=names.get(key(canonical))
        if not ref:raise ValueError('Unresolved original name: '+original)
        code=str(ref['id']);actual=lookup.get(code,{})
        uf=((actual.get('microrregiao') or {}).get('mesorregiao') or {}).get('UF') or (((actual.get('regiao-imediata') or {}).get('regiao-intermediaria') or {}).get('UF')) or {}
        if len(code)!=7 or not code.isdigit() or actual.get('nome')!=ref['name'] or uf.get('sigla')!=ref['uf']:
            raise ValueError('Official IBGE identity mismatch: '+code)
        result.append({'ibge':code,'name':actual['nome'],'uf':uf['sigla'],'origin_name':original,
                       'origin':row['origem'],'membership_status':'PENDING','monitoring_enabled':True})
    if len({r['ibge'] for r in result})!=118:raise ValueError('Duplicate target')
    return sorted(result,key=lambda r:r['ibge'])

def register(ctx,rows,sources,roster_sha):
    ctx.require('sources.sync')
    # All identities have been validated before this single atomic transaction.
    for row in rows:
        old=ctx.db.one('SELECT name,uf FROM municipality WHERE ibge=:i',{'i':row['ibge']})
        if old and (old['name']!=row['name'] or old['uf']!=row['uf']):fail(409,'O cadastro existente diverge do IBGE. Confira antes de importar.')
        source_id=sources[row['uf']]
        previous=ctx.db.one('SELECT roster_sha256 FROM monitoring_target WHERE org_id=:o AND municipality_ibge=:i',{'o':ctx.org_id,'i':row['ibge']})
        if previous and previous['roster_sha256']!=roster_sha:fail(409,'Esta lista mudou. Revise sua origem antes de substituir o monitoramento.')
        ctx.db.execute('INSERT INTO municipality(ibge,name,uf,origin) VALUES (:i,:n,:u,:origin) ON CONFLICT(ibge) DO NOTHING',
                       {'i':row['ibge'],'n':row['name'],'u':row['uf'],'origin':'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/'+row['ibge']})
        ctx.db.execute('''INSERT INTO monitoring_target(org_id,municipality_ibge,origin_name,origin,source_id,roster_sha256,
                          membership_status,monitoring_enabled,created_by) VALUES (:o,:i,:n,:origin,:s,:h,'PENDING',true,:a)
                          ON CONFLICT(org_id,municipality_ibge) DO NOTHING''',
                       {'o':ctx.org_id,'i':row['ibge'],'n':row['origin_name'],'origin':row['origin'],'s':source_id,'h':roster_sha,'a':ctx.actor_id})
    ctx.audit('monitoring.roster_verified',roster_sha,{'targets':len(rows),'membership_confirmed':False})
    return {'targets':len(rows),'membership_confirmed':0,'roster_sha256':roster_sha}

def targets(ctx):
    ctx.require('read')
    rows=ctx.db.all('''SELECT t.municipality_ibge AS ibge,m.name,m.uf,t.origin_name,t.membership_status,t.monitoring_enabled,
                     t.validated_at,s.url AS source_url,s.sha256 AS source_sha256
                     FROM monitoring_target t JOIN municipality m ON m.ibge=t.municipality_ibge
                     JOIN source_observation s ON s.id=t.source_id WHERE t.org_id=:o ORDER BY m.name''',{'o':ctx.org_id})
    return normalize({'records':rows,'monitored':sum(bool(r['monitoring_enabled']) for r in rows),
                      'membership_confirmed':sum(r['membership_status']=='CONFIRMED' for r in rows),
                      'notice':'Municípios monitorados; a filiação ao consórcio depende de confirmação documental.'})
