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
