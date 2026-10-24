import pytest
from app.integration_providers import query,definitions

def test_registry_has_explicit_official_and_blocked_states(monkeypatch):
    monkeypatch.setattr('app.portal_credentials.load_portal_key',lambda:None)
    rows={r['provider']:r for r in definitions()}
    assert rows['LICITEI']['blocked'] and not rows['LICITEI']['operational']
    assert not rows['CATMAT_COM_BR']['official']
    assert rows['PNCP']['official'] and rows['PNCP']['operational']
    assert rows['PORTAL_TRANSPARENCIA']['blocked']=='KEY_REQUIRED'

def test_untrusted_provider_or_tool_never_executes(login):
    c=login()
    assert c.get('/api/v1/portfolio/providers').status_code==200
    assert c.get('/api/v1/portfolio/providers/CATMAT_COM_BR/item',params={'group':'15','code':'463562'}).status_code==422
    assert c.get('/api/v1/portfolio/providers/LICITEI/item',params={'group':'15','code':'463562'}).status_code==503
    assert c.get('/api/v1/portfolio/providers/UNTRUSTED/item',params={'group':'15','code':'463562'}).status_code==404

def test_anonymous_provider_registry_is_protected(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:assert c.get('/api/v1/portfolio/providers').status_code==401


def test_source_panel_matches_configured_cgu_without_exposing_key(login,monkeypatch):
    from app.portfolio_sources import sources
    from types import SimpleNamespace
    monkeypatch.setattr('app.portal_credentials.load_portal_key',lambda:'fixture-not-a-real-key')
    ctx=SimpleNamespace(require=lambda _:None,org_id='fixture',db=SimpleNamespace(all=lambda *a:[]))
    row=next(r for r in sources(ctx)['records'] if r['provider']=='PORTAL_TRANSPARENCIA_MCP')
    assert row['state']=='available' and row['official'] is True
    assert 'fixture-not-a-real-key' not in str(row)
    monkeypatch.setattr('app.portal_credentials.load_portal_key',lambda:None)
    assert next(r for r in sources(ctx)['records'] if r['provider']=='PORTAL_TRANSPARENCIA_MCP')['state']=='blocked'
