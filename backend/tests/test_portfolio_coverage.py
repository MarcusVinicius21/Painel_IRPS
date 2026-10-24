from app.portfolio_coverage import summarize


def group(**changes):
    return {**dict(materialized_tasks=2,verified_pages=2,expected_pages=3,pagination_reconciled=False,
        errors=[],source_errors=[],task_states={'done':2},last_sync='2026-10-23'),**changes}


def test_missing_page_never_becomes_one_hundred_percent():
    result=summarize([group()]);assert result['coverage_status']=='partial'
    assert 66<float(result['request_reconciliation_pct'])<67
    assert result['municipal_purchase_completeness'] is None


def test_unknown_page_denominator_429_and_empty_remain_explicit():
    assert summarize([group(expected_pages=None)])['request_reconciliation_pct'] is None
    fail=group(materialized_tasks=1,verified_pages=0,expected_pages=None,task_states={'blocked':1},source_errors=['RATE_LIMIT'])
    assert summarize([fail])['coverage_status']=='blocked'
    empty=summarize([]);assert empty['coverage_status']=='not_collected' and empty['request_reconciliation_pct'] is None


def test_complete_requests_not_complete_purchases():
    result=summarize([group(expected_pages=2,pagination_reconciled=True,fully_reconciled=True)])
    assert result['coverage_status']=='available' and result['request_reconciliation_pct']=='100'
    assert result['municipal_purchase_completeness'] is None
