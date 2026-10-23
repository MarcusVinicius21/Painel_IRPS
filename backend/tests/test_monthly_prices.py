"""Small synthetic archives, exclusively inside the isolated QA database."""
import csv,io,zipfile,hashlib,json
from uuid import uuid4
from datetime import date
import pytest
from app import monthly_prices,sources


def archive(tmp_path,rows,name='month.zip'):
    p=tmp_path/name;stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
    with zipfile.ZipFile(p,'w') as z:z.writestr('test.csv',stream.getvalue().encode('utf-8'))
    return p,hashlib.sha256(p.read_bytes()).hexdigest()


def row(code):
    return dict(id_compra='compra-qa',id_item_compra='item-qa',numero_item_compra='1',codigo_item_catalogo=code,
        data_compra='2026-09-12',preco_unitario='10.50',quantidade='2',descricao_item='Item de teste isolado',
        nome_unidade_medida='UNIDADE',nome_fornecedor='Pessoa natural excluída',ni_fornecedor='12345678901')


def test_import_is_atomic_deduplicated_private_and_idempotent(app,login,settings,tmp_path):
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16));p,sha=archive(tmp_path,[row(code),row(code)])
    args=(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-09',sha,'https://example.invalid/qa.zip')
    first=monthly_prices.import_archive(*args);second=monthly_prices.import_archive(*args)
    assert first['source_rows']==2 and first['accepted_rows']==1 and first['duplicate_rows']==1 and second['idempotent']
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        result=monthly_prices.query(sources.job_context(db,identity['org_id'],identity['actor_id']),'material',code,date(2026,9,1),date(2026,9,30))
        assert result['total_records_reported']==1 and result['records'][0]['unit_price']=='10.50'
        assert result['records'][0]['supplier_cnpj'] is None and 'Pessoa natural' not in json.dumps(result)
        assert not result['municipal_coverage_claimed'] and result['records'][0]['source_line']==2
    other=login('compras-b').get('/api/v1/auth/context').json()
    with app.state.database.transaction(other['org_id'],other['actor_id']) as db:
        result=monthly_prices.query(sources.job_context(db,other['org_id'],other['actor_id']),'material',code,date(2026,9,1),date(2026,9,30))
        assert result['records']==[] and result['state']=='not_collected'
        assert result['total_records_reported'] is None


def test_revisions_and_namespaces_are_preserved_without_merging(app,login,settings,tmp_path):
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16))
    old=row(code);new={**old,'preco_unitario':'12.50'};p,sha=archive(tmp_path,[old,new])
    for kind in ['material','servico']:
        r=monthly_prices.import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,kind,'2026-09',sha,'https://example.invalid/qa.zip')
        assert r['conflicting_source_keys']==1 and r['accepted_rows']==2
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        result=monthly_prices.query(sources.job_context(db,identity['org_id'],identity['actor_id']),'servico',code,date(2026,9,1),date(2026,9,30))
        assert len(result['records'])==2 and all(r['needs_review'] and r['revision_count']==2 for r in result['records'])
        assert all(r['catalogue_kind']=='servico' for r in result['records'])


def test_bad_hash_rolls_back_and_rejections_are_explicit(app,login,settings,tmp_path):
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16));p,sha=archive(tmp_path,[row(code),{**row(code),'data_compra':'2026-08-01'}])
    args=(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-09')
    with pytest.raises(ValueError,match='checksum'):monthly_prices.import_archive(*args,'0'*64,'https://example.invalid/qa.zip')
    result=monthly_prices.import_archive(*args,sha,'https://example.invalid/qa.zip')
    assert result['rejected_rows']==1 and not result['complete_file_import']
    assert result['rejections'][0]['reason']=='date_outside_source_month'


def test_online_failure_uses_monthly_evidence_with_visible_failure(app,login,settings,tmp_path,monkeypatch):
    client=login();identity=client.get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16));p,sha=archive(tmp_path,[row(code)])
    monthly_prices.import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-09',sha,'https://example.invalid/qa.zip')
    def failed(*args,**kwargs):raise sources.SourceFault('SOURCE_UNAVAILABLE',503,60)
    monkeypatch.setattr(sources,'public_get',failed)
    response=client.get('/api/v1/catalogue-intelligent/reference-prices',params={'kind':'material','code':code,'start':'2026-09-01','end':'2026-09-30'})
    assert response.status_code==200
    data=response.json();assert data['state']=='partial' and data['source_kind']=='monthly_file' and data['fallback_from']=='live_api'
    assert data['source_error']['code'] in ('SOURCE_UNAVAILABLE','SOURCE_COOLDOWN') and data['records'][0]['unit_price']=='10.50'
    assert data['scope']['imported_months']==['2026-09-01']

def test_keyset_crosses_page_100_without_duplicates_or_gaps(app,login,settings,tmp_path):
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16))
    p,sha=archive(tmp_path,[{**row(code),'id_item_compra':f'{i:05d}','numero_item_compra':str(i)} for i in range(1005)])
    monthly_prices.import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-09',sha,'https://example.invalid/qa.zip')
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id']);cursor=None;seen=[]
        for page in range(1,102):
            result=monthly_prices.query(ctx,'material',code,date(2025,10,1),date(2026,9,30),page,cursor)
            repeated=monthly_prices.query(ctx,'material',code,date(2025,10,1),date(2026,9,30),page,cursor)
            assert result==repeated and len(result['records'])<=10
            seen.extend(r['source_key'] for r in result['records']);cursor=result['next_cursor']
        assert len(seen)==len(set(seen))==1005 and not result['has_next_page'] and cursor is None
        assert result['total_records_reported']==1005 and len(result['records'])==5
        empty=monthly_prices.query(ctx,'material',str(int(code)+1),date(2025,10,1),date(2026,9,30))
        assert empty['records']==[]
