import pytest
from fastapi import HTTPException
from app.tce_adapter import capabilities,ingest


class NoIOContext:
    def __init__(self,allowed=True):self.allowed=allowed;self.checked=[]
    def require(self,permission):
        self.checked.append(permission)
        if not self.allowed:raise HTTPException(403,'Access denied in QA')
    @property
    def db(self):raise AssertionError('A blocked connector must not open a DB operation.')


def test_unverified_contract_cannot_be_enabled_by_request_claims():
    ctx=NoIOContext()
    for _ in range(2):
        with pytest.raises(HTTPException) as exc:
            ingest(ctx,{'verified':True,'format':'CSV','url':'https://dadosabertos.tce.mg.gov.br/fixture-only.csv',
                'rows':[{'municipality':'3131307','amount':999}]})
        assert exc.value.status_code==409 and exc.value.detail['code']=='TCE_SOURCE_UNVERIFIED'
    assert ctx.checked==['sources.sync','sources.sync']
    status=capabilities()
    assert not status['can_ingest'] and not status['connector_verified']
    assert status['records_imported'] is None and status['municipal_purchase_completeness'] is None


def test_permission_is_checked_before_any_import_attempt():
    ctx=NoIOContext(allowed=False)
    with pytest.raises(HTTPException) as exc:ingest(ctx)
    assert exc.value.status_code==403
