"""Synthetic isolated-tenant annual union, no operational writes or network."""
from datetime import date
import base64,json
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app import monthly_prices as raw,monthly_consolidated as annual,sources
from test_monthly_prices import archive,row,isolated_monthly_identity

START,END=date(2025,10,1),date(2026,9,30)

def setup(login,settings):return isolated_monthly_identity(login,settings),str(int(uuid4().hex[:8],16))

def load(settings,identity,tmp_path,rows,kind='material',month='2026-09'):
    p,sha=archive(tmp_path,rows,str(uuid4())+'.zip')
    return raw.import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,kind,month,sha,'https://example.invalid/qa.zip')

def query(app,identity,code,**kwargs):
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        return annual.query(sources.job_context(db,identity['org_id'],identity['actor_id']),'material',code,START,END,**kwargs)

def test_latest_file_revision_and_cross_month_code_change_are_ranked_before_code_filter(app,login,settings,tmp_path):
    identity,code=setup(login,settings);other=str(int(code)+1)
    first=load(settings,identity,tmp_path,[{**row(code),'data_compra':'2025-10-31'}],month='2025-10')
    load(settings,identity,tmp_path,[{**row(other),'preco_unitario':'15','data_compra':'2025-10-31'}],month='2025-10')
    assert query(app,identity,code)['records']==[]
    assert query(app,identity,other)['records'][0]['unit_price']=='15'
    load(settings,identity,tmp_path,[row(code)])
    assert query(app,identity,other)['records']==[]
    record=query(app,identity,code)['records'][0]
    assert record['revision_count']==2 and record['conflict'] and record['source_month']=='2026-09-01'
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        assert db.one('SELECT count(*) n FROM price_monthly_snapshot')['n']==3
        assert db.one('SELECT count(*) n FROM price_monthly_record')['n']==3
        assert db.one('SELECT id FROM price_monthly_snapshot WHERE id=:i',{'i':first['snapshot_id']})

def test_rejected_revision_does_not_replace_reconciled_source(app,login,settings,tmp_path):
    identity,code=setup(login,settings);load(settings,identity,tmp_path,[row(code)])
    load(settings,identity,tmp_path,[{**row(code),'preco_unitario':'99'},{**row(code),'data_compra':'2026-08-01'}])
    result=query(app,identity,code)
    assert result['records'][0]['unit_price']=='10.50'
    assert result['coverage']['state']=='review_required'

def test_missing_data_conflict_units_and_namespace_never_generate_means(app,login,settings,tmp_path):
    identity,code=setup(login,settings)
    load(settings,identity,tmp_path,[{**row(code),'quantidade':'','preco_unitario':'','nome_unidade_medida':' '},
                                    {**row(code),'id_item_compra':'second','nome_unidade_medida':'CAIXA'}])
    load(settings,identity,tmp_path,[{**row(code),'preco_unitario':'999'}],kind='servico')
    result=query(app,identity,code)
    assert len(result['records'])==2 and result['statistics']['mean'] is None and result['statistics']['median'] is None
    assert all(x['catalogue_kind']=='material' for x in result['records'])
    missing=next(x for x in result['records'] if x['source_key'].endswith('item-qa'))
    assert missing['quantity'] is None and missing['unit_price'] is None and missing['unit_status']=='unknown'
    assert len(query(app,identity,code,unit='CAIXA')['records'])==1

def test_full_filters_and_year_boundary_preserve_exact_source_codes(app,login,settings,tmp_path):
    identity,code=setup(login,settings)
    load(settings,identity,tmp_path,[{**row(code),'data_compra':'2025-10-01','codigo_uasg':'001234','codigo_municipio':'3131307','ni_fornecedor':'12345678000190'}],month='2025-10')
    assert len(query(app,identity,code,uasg='001234',municipality='3131307',supplier='12345678000190')['records'])==1
    assert query(app,identity,code,municipality='3168705')['records']==[]
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        assert annual.query(ctx,'material',code,date(2025,10,2),END)['records']==[]
        empty=annual.query(ctx,'material',code,date(2024,1,1),date(2024,1,31))
        assert empty['total_records_reported'] is None and empty['state']=='not_collected'

def test_summary_counts_distinct_codes_once_and_excludes_missing_price(app,login,settings,tmp_path):
    identity,code=setup(login,settings)
    load(settings,identity,tmp_path,[{**row(code),'data_compra':'2025-10-01'}],month='2025-10')
    load(settings,identity,tmp_path,[{**row(code),'id_item_compra':'second'},
                                    {**row(str(int(code)+1)),'id_item_compra':'third','preco_unitario':''}])
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        result=annual.summary(sources.job_context(db,identity['org_id'],identity['actor_id']),START,END)
    assert result['totals']['logical_records']==3
    assert result['totals']['source_codes_with_price']==1 and result['totals']['unknown_price']==1
    assert result['coverage']['state']=='partially_imported' and not result['quantities_aggregated']
    other=isolated_monthly_identity(login,settings)
    assert query(app,other,code)['total_records_reported'] is None

def test_keyset_over_100_pages_scope_revision_invalid_uuid_and_page(app,login,settings,tmp_path):
    identity,code=setup(login,settings)
    load(settings,identity,tmp_path,[{**row(code),'id_item_compra':f'{i:05d}'} for i in range(1005)])
    cursor=None;seen=[];first_cursor=None
    for page in range(1,102):
        result=query(app,identity,code,page=page,cursor=cursor)
        if page==1:first_cursor=result['next_cursor']
        seen.extend(x['source_key'] for x in result['records']);cursor=result['next_cursor']
    assert len(seen)==len(set(seen))==1005 and not result['has_next_page'] and cursor is None
    for bad in ['*',base64.urlsafe_b64encode(b'{}').decode()]:
        with pytest.raises(HTTPException) as error:query(app,identity,code,page=2,cursor=bad)
        assert error.value.status_code==422
    token=json.loads(base64.urlsafe_b64decode(first_cursor));token['after'][3]='invalid-uuid'
    bad=base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
    with pytest.raises(HTTPException):query(app,identity,code,page=2,cursor=bad)
    with pytest.raises(HTTPException):query(app,identity,code,page=3,cursor=first_cursor)
    load(settings,identity,tmp_path,[{**row(code),'preco_unitario':'55'}])
    with pytest.raises(HTTPException) as error:query(app,identity,code,page=2,cursor=first_cursor)
    assert error.value.status_code==422

def test_consolidated_endpoint_requires_auth_and_keeps_tenant_isolation(app,login,settings,tmp_path):
    client=login();identity=client.get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16))
    load(settings,identity,tmp_path,[row(code)])
    params={'kind':'material','code':code,'start':START.isoformat(),'end':END.isoformat()}
    assert client.get('/api/v1/catalogue-intelligent/consolidated-prices',params=params).json()['records']
    other=login('compras-b');result=other.get('/api/v1/catalogue-intelligent/consolidated-prices',params=params)
    assert result.status_code==200 and result.json()['records']==[]
    from fastapi.testclient import TestClient
    with TestClient(app) as anonymous:assert anonymous.get('/api/v1/catalogue-intelligent/consolidated-prices',params=params).status_code==401

def test_cached_summary_refreshes_coverage_after_rejected_revision(app,login,settings,tmp_path):
    identity,code=setup(login,settings);load(settings,identity,tmp_path,[row(code)])
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        original=annual.summary(sources.job_context(db,identity['org_id'],identity['actor_id']),START,END)
    load(settings,identity,tmp_path,[row(code),{**row(code),'data_compra':'2026-08-01'}])
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        current=annual.summary(sources.job_context(db,identity['org_id'],identity['actor_id']),START,END)
    assert current['scope_fingerprint']==original['scope_fingerprint']
    assert current['totals']==original['totals']
    assert original['coverage']['state']=='partially_imported' and current['coverage']['state']=='review_required'
