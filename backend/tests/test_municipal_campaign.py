from datetime import date
import pytest
from app.municipal_campaign import closed_months, freeze_scope, pending_matrix, verify_ibge


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
