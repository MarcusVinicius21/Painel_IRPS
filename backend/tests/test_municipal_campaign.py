from datetime import date
import pytest
from app.municipal_campaign import buyer_identity, closed_months, freeze_scope, pending_matrix, verify_ibge


def test_manifest_is_order_independent_and_homonyms_remain_distinct():
    rows = [{'ibge': '3112056', 'name': 'Cantagalo', 'uf': 'MG'}, {'ibge': '3301108', 'name': 'Cantagalo', 'uf': 'RJ'}]
    a = freeze_scope(rows, date(2025, 10, 1), date(2026, 9, 30))
    assert a == freeze_scope(list(reversed(rows)), date(2025, 10, 1), date(2026, 9, 30))
    assert len(a['months']) == 12 and len(a['municipalities']) == 2
    assert len(pending_matrix(a)) == 216
    assert all(x['observed_records'] is None and x['completeness_percent'] is None for x in pending_matrix(a))


def test_duplicate_city_rejected():
    city = {'ibge': '3131307', 'name': 'Ipatinga', 'uf': 'MG'}
    with pytest.raises(ValueError, match='repetido'):
        freeze_scope([city, city], date(2025, 10, 1), date(2026, 9, 30))


@pytest.mark.parametrize('start,end', [(date(2025, 10, 2), date(2026, 9, 30)), (date(2025, 10, 1), date(2026, 9, 29))])
def test_incomplete_months_rejected(start, end):
    with pytest.raises(ValueError, match='complet'):
        closed_months(start, end)


def test_ibge_same_name_wrong_state_is_not_verified():
    with pytest.raises(ValueError, match='diverge'):
        verify_ibge({'ibge': '3301108', 'name': 'Cantagalo', 'uf': 'MG'},
                    {'id': 3301108, 'nome': 'Cantagalo', 'microrregiao': {'mesorregiao': {'UF': {'sigla': 'RJ'}}}})


def test_ibge_new_geographic_layout():
    verify_ibge({'ibge': '3131307', 'name': 'Ipatinga', 'uf': 'MG'},
                {'id': 3131307, 'nome': 'Ipatinga', 'regiao-imediata': {'regiao-intermediaria': {'UF': {'sigla': 'MG'}}}})


@pytest.mark.parametrize('sphere,power,municipal,branch', [('E', 'E', False, 'executivo'), ('F', 'E', False, 'executivo'), ('M', 'L', True, 'legislativo'), ('M', 'N', True, None)])
def test_location_does_not_establish_ownership(sphere, power, municipal, branch):
    buyer = {'cnpj': '19876424000142', 'unit_code': '1', 'municipality_ibge': '3131307'}
    record = {'orgaoEntidade': {'cnpj': buyer['cnpj'], 'esferaId': sphere, 'poderId': power},
              'unidadeOrgao': {'codigoUnidade': '1', 'codigoIbge': '3131307'}}
    result = buyer_identity(buyer, record)
    assert result['state'] == 'verified' and result['municipal_buyer'] is municipal
    assert result['power'] == branch and result['institutional_subtype'] is None
    assert result['cnpj_root'] == '19876424'


@pytest.mark.parametrize('field,value', [('cnpj', '19875020000134'), ('unit_code', '2'), ('municipality_ibge', '3168705')])
def test_same_name_or_cnpj_root_cannot_merge_conflicting_buyers(field, value):
    buyer = {'cnpj': '19876424000142', 'unit_code': '1', 'municipality_ibge': '3131307'}
    record = {'orgaoEntidade': {'cnpj': buyer['cnpj'], 'esferaId': 'M'},
              'unidadeOrgao': {'codigoUnidade': '1', 'codigoIbge': '3131307'}}
    buyer[field] = value
    result = buyer_identity(buyer, record)
    assert result['state'] == 'ORGAO_NAO_VERIFICADO'
    assert result['municipal_buyer'] is None and result['cnpj'] is None
