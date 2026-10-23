"""Official manifest contracts tested only with deterministic disposable QA files."""
import hashlib
from uuid import uuid4
import pytest
from app.national_catalogue import import_csv

def test_import_manifest_hash_and_count_are_atomic(settings,tmp_path):
    p=tmp_path/'manifest.csv';code=str(int(uuid4().hex[:9],16))
    p.write_text('codigoItem;descricaoItem;statusItem\n'+code+';Café de teste isolado;False\n',encoding='utf-8')
    sha=hashlib.sha256(p.read_bytes()).hexdigest();url=settings.owner_database_url.get_secret_value()
    with pytest.raises(ValueError,match='Checksum'):import_csv(url,p,'CATMAT',expected_sha256='0'*64)
    with pytest.raises(ValueError,match='contagem'):import_csv(url,p,'CATMAT',expected_sha256=sha,expected_records=2)
    r=import_csv(url,p,'CATMAT',expected_sha256=sha,expected_records=1)
    assert r['rows']==1 and r['active']==0 and r['inactive']==1 and r['rejected']==0
    assert import_csv(url,p,'CATMAT',expected_sha256=sha,expected_records=1)['duplicate']

def test_mixed_catalogue_pages_preserve_both_namespaces(login,settings,tmp_path):
    prefix=str(int(uuid4().hex[:8],16));url=settings.owner_database_url.get_secret_value()
    material=tmp_path/'mixed-material.csv';service=tmp_path/'mixed-service.csv'
    material.write_text('codigoItem;descricaoItem;statusItem\n'+''.join(f'{prefix}{n};Café {n};{n%2==0}\n' for n in range(4)),encoding='utf-8')
    service.write_text('codigoServico;nomeServico;statusServico\n'+''.join(f'{prefix}{n};Serviço {n};True\n' for n in range(3)),encoding='utf-8')
    import_csv(url,material,'CATMAT');import_csv(url,service,'CATSER');c=login()
    records=[]
    for offset in [0,3,6]:
        r=c.get('/api/v1/national-catalogue',params={'offset':offset,'limit':3}).json()
        assert r['total']==7
        assert r['next_offset']==(offset+3 if offset<6 else None)
        assert r['last_offset']==6
        records+=r['records']
    assert len({(r['kind'],r['code']) for r in records})==7
    assert [r['kind'] for r in records]==['CATMAT']*4+['CATSER']*3
    far=c.get('/api/v1/national-catalogue',params={'offset':500000}).json()
    assert far['records']==[] and far['next_offset'] is None and far['total']==7
    assert c.get('/api/v1/national-catalogue',params={'kind':'CATMAT','active':'false'}).json()['total']==2
    assert c.get('/api/v1/national-catalogue',params={'q':prefix+'0'}).json()['total']==2
    assert c.get('/api/v1/national-catalogue',params={'q':'CAFE'}).json()['total']==4

def test_plan_execution_requires_source_evidence(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    response=c.post('/api/v1/history-collections',json={'municipalities':['3131307'],'start':'2025-02-01','end':'2025-02-01','modalities':[6],'items':False,'results':False,'max_pages':2})
    assert response.status_code==201
    cid=response.json()['id']
    with app.state.database.transaction(identity['org_id']) as db:
        # A corrupted QA task flag must not manufacture observed coverage.
        db.execute("UPDATE history_task SET state='done' WHERE org_id=:o AND collection_id=:c",{'o':identity['org_id'],'c':cid})
    r=c.get('/api/v1/history-collections/'+cid).json()['execution']
    assert r['materialized_tasks']==1 and r['evidenced_completed_tasks']==0
    assert r['request_plan_percent']=='0' and not r['complete_known_plan']
    assert r['municipal_purchase_completeness'] is None
