"""Small synthetic archives for fail-closed campaign validation, never operational data."""
import sys,json,zipfile,hashlib
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from monthly_import_support import validate_manifest,private_path

@pytest.mark.parametrize('month',['2025-09','2026-10','2026-13','invalid'])
def test_campaign_rejects_unapproved_month(month):
    with pytest.raises(ValueError):validate_manifest([],month)

def test_campaign_requires_two_kinds_and_private_files():
    with pytest.raises(ValueError):validate_manifest([],'2026-08')
    with pytest.raises(ValueError):private_path('README.md')

def test_invalid_numeric_is_not_treated_as_a_documented_price():
    from test_monthly_prices import row
    from app.monthly_prices import normalize_row
    with pytest.raises(ValueError,match='invalid_numeric'):
        normalize_row({**row('1'),'preco_unitario':'invalid'},'material','2026-09')

def test_invalid_zip_is_rejected_before_writing(app,login,settings,tmp_path):
    from app.monthly_prices import import_archive
    identity=login().get('/api/v1/auth/context').json();p=tmp_path/'bad.zip';p.write_bytes(b'not a zip')
    with pytest.raises(zipfile.BadZipFile):
        import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-08',hashlib.sha256(p.read_bytes()).hexdigest(),'https://example.invalid/qa.zip')

def test_manifest_has_24_origins_atomic_resume_and_one_writer(tmp_path):
    from manifesto_precos_mensais import fresh,save,single_writer,event
    data=fresh();assert len(data['files'])==24 and len({(i['kind'],i['month']) for i in data['files']})==24
    path=tmp_path/'manifest.json';event(data,data['files'][0],'downloaded',sha256='a'*64);save(path,data)
    loaded=json.loads(path.read_text(encoding='utf-8'));assert loaded==data and loaded['files'][0]['state']!='reconciled'
    with single_writer(tmp_path):
        with pytest.raises(OSError):
            with single_writer(tmp_path):pass

def test_new_hash_preserves_previous_monthly_snapshot(app,login,settings,tmp_path):
    from test_monthly_prices import archive,row,isolated_monthly_identity
    from app import monthly_prices
    identity=isolated_monthly_identity(login,settings);code='123456';url=settings.owner_database_url.get_secret_value()
    old,sha=archive(tmp_path,[row(code)],'old.zip');first=monthly_prices.import_archive(url,identity['org_id'],old,'material','2026-09',sha,'https://example.invalid/qa.zip')
    new,newsha=archive(tmp_path,[{**row(code),'preco_unitario':'30'}],'new.zip');second=monthly_prices.import_archive(url,identity['org_id'],new,'material','2026-09',newsha,'https://example.invalid/qa.zip')
    assert first['snapshot_id']!=second['snapshot_id']
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        assert db.one('SELECT count(*) n FROM price_monthly_snapshot')['n']==2
        assert db.one('SELECT count(*) n FROM price_monthly_record')['n']==2

def test_archive_size_bound_rolls_back(app,login,settings,tmp_path):
    from test_monthly_prices import archive,row
    from app import monthly_prices
    from uuid import uuid4
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16));p,sha=archive(tmp_path,[{**row(code),'data_compra':'2026-08-12'}])
    args=(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-08',sha,'https://example.invalid/qa.zip')
    with pytest.raises(ValueError,match='size rejected'):monthly_prices.import_archive(*args,max_uncompressed_bytes=1)
    result=monthly_prices.import_archive(*args);assert result['accepted_rows']==1
    again=monthly_prices.import_archive(*args);assert again['idempotent']
    other,other_sha=archive(tmp_path,[{**row(code),'data_compra':'2026-08-12','preco_unitario':'99'}],name='other.zip')
    with pytest.raises(ValueError,match='row safety limit'):
        monthly_prices.import_archive(args[0],identity['org_id'],other,'material','2026-08',other_sha,args[-1],max_rows=0)

def test_explicit_refresh_preserves_hash_versions_without_duplicate_entries(tmp_path,monkeypatch):
    from test_monthly_prices import archive,row
    import manifesto_precos_mensais as manifest
    from contextlib import contextmanager
    monkeypatch.setattr(manifest,'ROOT',tmp_path)
    data=manifest.fresh();item=data['files'][0];folder=tmp_path/'sources';folder.mkdir();path=folder/'manifest.json'
    source,_=archive(tmp_path,[row('1')]);payload=[source.read_bytes()]
    @contextmanager
    def stream(*args,**kwargs):
        class Response:
            headers={'content-type':'application/zip'}
            def raise_for_status(self):pass
            def iter_bytes(self,*args):return iter([payload[0]])
        yield Response()
    monkeypatch.setattr(manifest.httpx,'stream',stream)
    manifest.download(data,item,folder,path,refresh=True)
    first=item['sha256'];item['state']='reconciled'
    manifest.download(data,item,folder,path,refresh=True)
    assert len(item['versions'])==1 and item['sha256']==first
    source,_=archive(tmp_path,[{**row('1'),'preco_unitario':'42'}],name='revision.zip');payload[0]=source.read_bytes()
    manifest.download(data,item,folder,path,refresh=True)
    assert len(item['versions'])==2 and first!=item['sha256']
    assert all((tmp_path/v['path']).exists() for v in item['versions'])
