import pytest
from app.municipal_portals import inventory


def test_two_registered_cities_have_distinct_source_limitations():
    result=inventory([{'ibge':'3131307','name':'Ipatinga'},{'ibge':'3168705','name':'Timóteo'}])
    a,b=result['municipalities']
    assert result['municipality_count']==2 and result['enabled_connectors']==0
    assert a['cnpj']=='19876424000142' and a['schema_observed']
    assert a['state']=='period_filter_unverified'
    assert b['cnpj']=='19875020000134' and not b['schema_observed']
    assert b['state']=='anonymous_access_denied'
    assert all(not r['can_ingest'] and r['coverage'] is None and r['verified_months']==[] for r in (a,b))
    assert a['categories']['contracts']['state']=='not_verified'


def test_unknown_city_remains_undiscovered_and_duplicates_do_not_expand_census():
    city={'ibge':'3106200','name':'Belo Horizonte'}
    result=inventory([city,city])
    assert result['municipality_count']==1
    assert result['municipalities'][0]['state']=='not_discovered'
    assert result['municipalities'][0]['record_count'] is None


@pytest.mark.parametrize('code',['','123','313130X',3131307])
def test_bad_census_identity_rejected(code):
    with pytest.raises(ValueError,match='INVALID_MUNICIPALITY'):
        inventory([{'ibge':code,'name':'QA'}])
