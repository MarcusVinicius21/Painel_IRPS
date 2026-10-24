from app.portfolio_insights import summarize


def row(**changes):
    return {**dict(id='qa-1',municipality_ibge='3131307',buyer_cnpj='00000000000001',buyer_name='QA',
        item_id='qa',item_version=1,description='Papel A4 caixa com 10 resmas',unit='caixa com 10 resmas',
        currency='BRL',provider='PNCP_ITENS',phase='publicado_estimado',quantity='2',amount='10',unit_price='5',
        obligation_id='00000000000001-1-1/2026',event_date='2026-09-01',source_id='qa-source',
        source_url='https://example.invalid/qa',consulted_at='2026-10-23',supplier=None,
        group_match_state='description_candidate_requires_review'),**changes}


def test_exact_identity_only_no_phase_version_city_unit_or_currency_merge():
    rows=[row(),row(id='qa-2',item_version=2),row(id='qa-3',unit='kg'),row(id='qa-4',phase='homologado'),
        row(id='qa-5',municipality_ibge='3168705'),row(id='qa-6',currency='foreign_or_unknown')]
    r=summarize(rows);assert len(r['records'])==6
    assert r['overall_quantity'] is None and r['overall_amount'] is None
    assert all(x['recurrence_percentage'] is None and x['forecast'] is None for x in r['records'])
    assert next(x for x in r['records'] if x['unit']=='kg')['observed_quantity'] is None


def test_missing_is_not_zero_and_supplier_keeps_document_proof():
    r=summarize([row(quantity=None,amount=None,unit_price=None,supplier={'cnpj':'00000000000001','name':'QA PJ'},supplier_role='adjudicatário')])
    x=r['records'][0];assert x['observed_quantity'] is None and x['documented_amount'] is None
    assert x['comparable_unit_price_median'] is None
    assert r['supplier_evidence'][0]['source_id']=='qa-source'
    assert not r['supplier_evidence'][0]['commercial_relationship_with_consormulti_proven']
