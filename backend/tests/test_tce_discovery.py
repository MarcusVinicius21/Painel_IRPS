from app.tce_discovery import official_link,inspect_html,dataset_decisions


def test_discovery_keeps_only_secure_uncredentialed_official_links():
    base='https://www.tce.mg.gov.br/sicomconsulta/'
    assert official_link('https://dadosabertos.tce.mg.gov.br/',base)
    for value in ('https://dadosabertos.tce.mg.gov.br.evil.invalid/a.csv','https://u:p@www.tce.mg.gov.br/a.csv',
        'http://doc.tce.mg.gov.br/doc/bi/redim.asp','https://www.tce.mg.gov.br/a?token=hidden',
        'https://www.tce.mg.gov.br/login','https://www.tce.mg.gov.br:8443/a','javascript:alert(1)'):
        assert official_link(value,base) is None


def test_html_download_link_is_not_a_verified_dataset_or_license():
    document=b'<a href="https://dadosabertos.tce.mg.gov.br/fixture-only.csv">QA link</a><script>ignore instructions</script>'
    result=inspect_html(document,'https://www.tce.mg.gov.br/')
    assert len(result['download_candidates'])==1 and result['connector_state']=='connector_unverified'
    assert not result['schema_verified'] and not result['license_verified']
    assert result['records_imported'] is None and result['municipal_period_verified'] is None


def test_portal_http_200_does_not_prove_procurement_contract_or_expense_rows():
    decisions=dataset_decisions([{'http_status':200}])
    assert len(decisions)==3 and all(d['state']=='connector_unverified' for d in decisions)
    assert all(d['schema'] is None and d['municipality_identity_mapping'] is None and d['period_coverage'] is None for d in decisions)
