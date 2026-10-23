"""Read-only operational evidence and original V4 hash verification."""
import hashlib,json,sys
from pathlib import Path
from sqlalchemy import create_engine,text
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize

def main():
    s=load_settings()
    if s.auth_mode!='operational_local':raise SystemExit('Selecione o ambiente operacional local.')
    database=Database(s)
    with database.transaction(s.operator_org_id) as db:
        result={'municipalities':db.all('SELECT * FROM municipality ORDER BY ibge'),
            'official_facts':db.all("SELECT provider,phase,count(*) AS records FROM procurement_fact WHERE classification='official' GROUP BY provider,phase ORDER BY provider"),
            'actors':db.one('SELECT count(*) n FROM actor')['n'],'memberships':db.one('SELECT count(*) n FROM membership')['n'],
            'organizations':db.one('SELECT count(*) n FROM organization')['n'],
            'national_catalogue_entries':db.one('SELECT count(*) n FROM national_catalogue_entry')['n'],
            'observations':db.all('SELECT provider,count(*) observations FROM source_observation GROUP BY provider ORDER BY provider'),
            'scope_coverage':db.all('SELECT provider,state,scope,record_count,pages_fetched,expected_pages,latest_success_at FROM coverage ORDER BY latest_success_at'),
            'audit':db.all('SELECT action,count(*) events FROM audit_event GROUP BY action ORDER BY action')}
        for name,table in [('facts','procurement_fact'),('items','item_version'),('scenarios','scenario'),('documents','document')]:
            result['synthetic_'+name]=db.one("SELECT count(*) n FROM "+table+" WHERE classification='synthetic'")['n']
        assert result['actors']==result['memberships']==result['organizations']==1
        assert all(result['synthetic_'+k]==0 for k in ['facts','items','scenarios','documents'])
    # Migration metadata requires the owner; no grant is added to the app role.
    owner=create_engine(s.owner_database_url.get_secret_value(),hide_parameters=True)
    with owner.connect() as conn:
        result['migration']=conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        result['forced_rls']=[dict(r) for r in conn.execute(text("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('director_study','irp_draft','irp_operation','national_product_link','item_version','director_progress') ORDER BY relname")).mappings()]
    modules=json.loads((ROOT/'docs/validacao/integridade-v4.json').read_text(encoding='utf-8'))['modules']
    result['v4']=[{'file':m['file'],'sha256':hashlib.sha256((ROOT/'backend/irps_core'/m['file']).read_bytes()).hexdigest(),
        'unchanged':hashlib.sha256((ROOT/'backend/irps_core'/m['file']).read_bytes()).hexdigest()==m['sha256']} for m in modules]
    assert len(result['v4'])==8 and all(m['unchanged'] for m in result['v4'])
    assert result['migration']=='0014' and all(r['relrowsecurity'] and r['relforcerowsecurity'] for r in result['forced_rls'])
    ready=httpx.get('http://127.0.0.1:5296/health/ready');assert ready.status_code==200
    result['health']=ready.json();result['application_url']='http://127.0.0.1:5296/'
    out=ROOT/'docs/IRPS_PILOTO_REAL_LOGIN_UNICO/verificacao-banco.json'
    out.write_text(json.dumps(normalize(result),ensure_ascii=False,indent=2),encoding='utf-8')
    owner.dispose();database.engine.dispose()
    print(json.dumps({'single_operator':True,'synthetic_records':0,'v4_intact':8,'migration':'0014','ready':True}))

if __name__=='__main__':main()
