import hashlib,json
from datetime import date
import pytest
from fastapi import HTTPException
from app.municipal_portal_adapter import review_response


class Context:
    def __init__(self,allowed=True):self.allowed=allowed
    def require(self,permission):
        assert permission=='sources.sync'
        if not self.allowed:raise HTTPException(403)
    @property
    def db(self):raise AssertionError('No database operation permitted in candidate review')


URL='https://dadosabertos-portalfacil.azurewebsites.net/api/pagamentos?type=json&idCliente=97&page=1&pageSize=100&numAno=2026'


def run(body=b'[]',**kwargs):
    args=dict(url=URL,status=200,body=body,sha256=hashlib.sha256(body).hexdigest(),
        start=date(2026,1,1),end=date(2026,9,30));args.update(kwargs)
    return review_response(Context(),**args)


@pytest.mark.parametrize('status',[429,503])
def test_limited_retry_is_not_coverage_or_success(status):
    result=run(status=status,retry_after='120')
    assert result['state']=='retry_later' and result['retry_after_seconds']==120
    assert result['coverage'] is None and result['automatic_attempts']==0


def test_404_and_bad_layout_are_not_empty_success():
    assert run(status=404)['state']=='source_unavailable'
    assert run(b'<html>layout changed</html>')['reason']=='INVALID_JSON_OR_LAYOUT_CHANGE'
    assert run(b'{}')['reason']=='INVALID_PAGE_OR_PERIOD'


def test_same_validated_batch_receipt_is_deterministic_but_no_persistence_claimed():
    body=json.dumps([dict(numExercicio='2026',numUnidade='1',numEmpenho='2',
        numPagamento='3',dtPagamento='01/09/2026',vlPagamento='12.30')]).encode()
    a=run(body);b=run(body)
    assert a==b and a['state']=='candidates_require_review'
    assert len(a['candidate_records'])==1
    assert not a['can_ingest'] and not a['database_mutated']
    assert a['records_imported'] is None and a['coverage'] is None


@pytest.mark.parametrize('url',[URL.replace('idCliente=97','idCliente=98'),URL+'&token=QA',
    URL.replace('https://','http://'),URL.replace('numAno=2026','numAno=2025'),
    URL.replace('page=1','page=0')])
def test_scope_or_unapproved_destination_rejected(url):
    with pytest.raises(ValueError,match='UNVERIFIED_PORTAL_URL'):run(url=url)


def test_bad_hash_unknown_schema_and_permission_fail_before_io():
    with pytest.raises(ValueError,match='INVALID_PORTAL_EVIDENCE'):run(sha256='bad')
    with pytest.raises(ValueError,match='UNVERIFIED_PORTAL_SCHEMA'):run(schema='client-approved')
    with pytest.raises(HTTPException) as exc:
        review_response(Context(False),url=URL,status=200,body=b'[]',sha256='bad',
            start=date(2026,1,1),end=date(2026,9,30))
    assert exc.value.status_code==403


def test_ignored_official_period_is_rejected_not_silently_filtered():
    body=json.dumps([dict(numExercicio='2010',numUnidade='1',numEmpenho='2',
        numPagamento='3',dtPagamento='04/01/2010',vlPagamento='74.49')]).encode()
    assert run(body)['reason']=='SOURCE_PERIOD_MISMATCH'
