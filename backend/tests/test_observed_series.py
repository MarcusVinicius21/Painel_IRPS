"""I04_02: persisted isolated facts, additive monthly/geographic contract."""
from decimal import Decimal
from datetime import date, datetime, timezone
from uuid import uuid4
from app.catalogue import observed_series
from test_history_contract import fixture_history, CITIES
from test_history_filters import filtered


def test_months_null_zero_and_geographic_partition(fixture_history):
    create,_,_=fixture_history;_,add,get=create()
    a=add(day='2025-01-10',quantity='2')
    b=add(day='2025-03-12',quantity='4',city=CITIES[1])
    add(day='2025-04-10',quantity=None)
    add(day='2025-05-10',quantity='0')
    s=get()['observed_series'];m={r['month']:r for r in s['monthly']}
    assert len(m)==12 and Decimal(m['2025-01']['observed_quantity'])==2
    assert m['2025-02']['observed_quantity'] is None
    assert m['2025-04']['observed_quantity'] is None
    assert Decimal(m['2025-05']['observed_quantity'])==0
    assert m['2025-01']['fact_ids']==[a] and m['2025-03']['fact_ids']==[b]
    assert Decimal(s['states'][0]['observed_quantity'])==6
    assert len(s['municipalities'])==3
    assert s['municipalities'][0]['partial'] and not s['source_completeness_claimed']
    assert all(r['coverage_verified'] is False for r in s['monthly'])
    assert m['2025-01']['consulted_at'] and m['2025-01']['source_ids']
    assert m['2025-01']['sources'][0]['url'].startswith('https://example.invalid/test-only/')


def test_current_compatible_facts_only_and_no_evidence_preview_truncation(fixture_history):
    create,_,_=fixture_history;_,add,get=create()
    event=uuid4().hex
    add(event=event,current=False,quantity='999')
    good=add(event=event,quantity='3')
    add(unit='caixa de 20 resmas',quantity='999')
    add(phase='publicado_estimado',quantity='888')
    add(day='2024-01-01',quantity='777')
    result=get();s=result['observed_series'];assert s['monthly'][-1]['fact_ids']==[good]
    assert Decimal(s['states'][0]['observed_quantity'])==3
    assert Decimal(result['summary']['observed_quantity'])==3


def test_exact_provider_city_phase_and_date_filters(filtered):
    _,add,get,_,_=filtered
    add(quantity='3',day='2025-03-10')
    add(provider='OTHER_TEST_SOURCE',quantity='8',day='2025-03-11')
    add(city=CITIES[1],quantity='5',day='2025-03-12')
    add(quantity='9',day='2025-05-10')
    s=get('PNCP_RESULTADOS',cities=[CITIES[0]],start='2025-03-05',end='2025-04-20')['observed_series']
    assert len(s['monthly'])==2 and Decimal(s['monthly'][0]['observed_quantity'])==3
    assert s['monthly'][0]['start']=='2025-03-05'
    assert s['monthly'][1]['end']=='2025-04-20' and s['monthly'][1]['observed_quantity'] is None
    assert len(s['municipalities'])==1 and s['filters']['provider']=='PNCP_RESULTADOS'


def test_empty_series_never_infers_zero(fixture_history):
    create,_,_=fixture_history;_,_,get=create()
    s=get()['observed_series']
    assert all(r['observed_quantity'] is None for key in ('monthly','states','municipalities') for r in s[key])


def test_series_uses_full_set_beyond_municipal_evidence_preview(fixture_history):
    create,_,_=fixture_history;_,add,get=create()
    for _ in range(101):add(quantity='1',amount='1')
    result=get();city=next(r for r in result['municipalities'] if r['municipality']['ibge']==CITIES[0])
    assert city['evidence_truncated']
    assert len(city['evidence'])==100
    assert len(result['observed_series']['monthly'][-1]['fact_ids'])==101
    assert Decimal(result['observed_series']['states'][0]['observed_quantity'])==101


def test_uf_partition_no_provider_or_supplier_join():
    facts=[{'id':str(n),'quantity':Decimal(n),'source_id':'source-'+str(n),
            'provider':'PNCP_RESULTADOS','consulted_at':datetime(2025,6,1,tzinfo=timezone.utc),
            'municipality_ibge':city,'event_date':date(2025,5,1)} for n,city in [(2,'MG1'),(3,'MG2'),(4,'RJ1')]]
    cities=[{'ibge':'MG1','uf':'MG'},{'ibge':'MG2','uf':'MG'},{'ibge':'RJ1','uf':'RJ'}]
    s=observed_series(facts,cities,'homologado',date(2025,1,1),date(2025,12,31),{}, {'unit_key':'UNIDADE','classification':'synthetic'})
    assert {r['uf']:r['observed_quantity'] for r in s['states']}=={'MG':Decimal(5),'RJ':Decimal(4)}
    assert sum(r['comparable_records'] for r in s['states'])==3
    assert s['monthly'][4]['observed_quantity']==9
    assert set(s['monthly'][4]['fact_ids'])=={'2','3','4'}
