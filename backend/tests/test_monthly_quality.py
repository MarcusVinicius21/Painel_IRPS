"""Quality is an annotation, never an inferred unit or a source mutation."""
import sys
from pathlib import Path
import pytest
from app.monthly_prices import unit_status
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from auditar_unidades_mensais import quality

@pytest.mark.parametrize('unit',[None,'','   ','\t'])
def test_unknown_units_stay_unknown(unit):
    body={'unit':unit,'quantity':'50'};assert unit_status(body)=='unknown' and body['unit']==unit

def test_documented_unit_is_not_replaced_by_alternative_or_description():
    source={'nome_unidade_fornecimento':'CAIXA','nome_unidade_medida':'UNIDADE','sigla_unidade_medida':'UN','quantidade':'10'}
    result=quality([source]);assert result['different_unit_fields']==1 and result['recovered_units']==0
    assert source['nome_unidade_fornecimento']=='CAIXA'

def test_abbreviation_is_evidence_for_review_not_automatic_recovery():
    result=quality([{'nome_unidade_medida':'','sigla_unidade_fornecimento':'CX','ni_fornecedor':'qa-only'}])
    assert result['unknown_unit']==1 and result['unknown_with_supply_abbreviation']==1 and result['recovered_units']==0
    assert 'qa-only' not in str(result)

def test_orphan_code_remains_queryable_without_a_fabricated_catalogue_link(app,login,settings,tmp_path):
    from test_monthly_prices import archive,row
    from app.monthly_prices import import_archive
    from uuid import uuid4
    client=login();identity=client.get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:10],16))
    source,sha=archive(tmp_path,[row(code)])
    import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],source,'servico','2026-09',sha,'https://example.invalid/qa-orphan.zip')
    response=client.get('/api/v1/catalogue-intelligent/monthly-prices',params={'kind':'servico','code':code,'start':'2026-09-01','end':'2026-09-30'})
    assert response.status_code==200
    result=response.json();assert result['state']=='needs_review'
    assert len(result['records'])==1
    record=result['records'][0]
    assert record['catalogue_code']==code and record['catalogue_kind']=='servico'
    assert record['catalogue_code_verified'] is False and record['needs_review'] is True
    assert any('catálogo' in reason for reason in record['review_reasons'])
