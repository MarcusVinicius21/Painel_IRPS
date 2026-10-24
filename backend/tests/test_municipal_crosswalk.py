from app.municipal_crosswalk import crosswalk,process_key


def row(**change):
    return {**dict(id='qa-1',source_id='qa-source',provider='PNCP',phase='publicado_estimado',
        classification='official',obligation_id='19876424000142-1-000001/2026',
        buyer_cnpj='19876424000142',municipality_ibge='3131307'),**change}


def test_same_process_keeps_contracts_items_winners_and_phases_separate():
    result=crosswalk([row(),row(id='qa-2',provider='PNCP_ITENS'),
        row(id='qa-3',provider='PNCP_CONTRATOS',phase='contratado'),
        row(id='qa-4',provider='PNCP_RESULTADOS',phase='homologado')])
    assert result['distinct_identified_processes']==1
    process=result['processes'][0]
    assert len(process['fact_ids'])==4 and len(process['phases'])==3
    assert process['amount'] is None and process['quantity'] is None
    assert not process['event_merges_applied']


def test_homonymous_buyer_council_and_prefecture_never_merge():
    a=row();b=row(id='qa-2',buyer_cnpj='17112673000136',obligation_id='17112673000136-1-1/2026',
        municipality_ibge='3168705')
    assert crosswalk([a,b])['distinct_identified_processes']==2
    key,reason=process_key({**a,'buyer_cnpj':b['buyer_cnpj']})
    assert key is None and reason=='BUYER_PROCESS_ID_CONFLICT'


def test_external_name_amount_date_and_self_asserted_match_do_not_authorize_join():
    a=row(provider='TCE_MG',description='Same name',amount='10.00',pncp_identity_verified=True)
    result=crosswalk([row(),a])
    assert result['pending_records']==1 and result['cross_source_event_matches']==0
    assert result['pending_match'][0]['reason']=='SOURCE_PROCESS_CONTRACT_UNVERIFIED'


def test_missing_id_synthetic_and_revisions_are_not_discarded():
    assert process_key(row(obligation_id='1/2026'))[0] is None
    assert process_key(row(classification='synthetic'))[0] is None
    result=crosswalk([row(),row(id='qa-prior-version',source_id='qa-old-source')])
    assert len(result['processes'][0]['source_ids'])==2
    assert len(result['processes'][0]['fact_ids'])==2
