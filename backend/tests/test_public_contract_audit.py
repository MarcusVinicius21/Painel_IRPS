import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('public_audit', Path(__file__).resolve().parents[2] / 'scripts/auditar_contratos_publicos.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_contract_summary_retains_method_and_exact_parameter_names():
    result = audit.summarize_contract({'info': {'version': '1.0'}, 'paths': {
        '/v1/contratos': {'get': {'parameters': [{'name': 'cnpjOrgao'}, {'name': 'pagina'}]}},
        '/login': {'post': {}}}})
    assert result['paths_count'] == 2
    assert result['routes']['/v1/contratos'] == {'parameters': ['cnpjOrgao', 'pagina'], 'get': True}
    assert result['routes']['/login']['get'] is False


def test_audit_targets_never_include_credentialed_or_secondary_data_hosts():
    from urllib.parse import urlparse
    for url in audit.TARGETS.values():
        parsed = urlparse(url)
        assert parsed.scheme == 'https' and parsed.username is None and parsed.password is None
        assert parsed.hostname in ('pncp.gov.br', 'dadosabertos.compras.gov.br', 'dadosabertos.tce.mg.gov.br', 'www.tce.mg.gov.br')
