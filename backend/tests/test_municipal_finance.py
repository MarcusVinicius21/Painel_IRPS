from datetime import date
import pytest
from app.municipal_finance import payment_candidates, FinanceEvidenceError


def row(**changes):
    return dict(numExercicio='2026', numUnidade='001', numEmpenho='42',
        numPagamento='123', dtPagamento='15/09/2026', vlPagamento='10.20', **changes)


def check(rows):
    return payment_candidates(rows, start=date(2025, 10, 1), end=date(2026, 9, 30))


def test_repeated_rows_not_new_payments_and_installments_remain_distinct():
    a=row(); b={**a, 'numPagamento':'124'}
    result=check([a, a.copy(), b])
    assert len(result['candidates'])==2 and result['exact_duplicate_rows']==1
    assert all(r['item_id'] is None and r['quantity'] is None and r['contract_id'] is None for r in result['candidates'])
    assert result['net_balance'] is None and result['coverage'] is None


def test_financial_unit_is_part_of_identity():
    a=row();result=check([a, {**a, 'numUnidade':'002'}])
    assert len(result['candidates'])==2


@pytest.mark.parametrize('change', [{'vlPagamento':'11.20'}, {'dtPagamento':'16/09/2026'}, {'nuTipo':'2'}])
def test_conflicting_identity_never_silently_summed(change):
    a=row()
    with pytest.raises(FinanceEvidenceError, match='CONFLICTING_FINANCIAL_IDENTITY'):
        check([a, {**a, **change}])


@pytest.mark.parametrize('value', ['-10.00','NaN','Infinity','10.001','R$ 10,00',False])
def test_reversal_or_ambiguous_amount_requires_review(value):
    with pytest.raises(FinanceEvidenceError, match='AMOUNT_OR_REVERSAL'):
        check([{**row(), 'vlPagamento':value}])


def test_unknown_amount_not_zero_and_no_private_supplier_fields_exposed():
    result=check([{**row(), 'vlPagamento':None, 'numCpfCnpj':'QA_PRIVATE_ONLY',
        'descFornecedor':'Synthetic private test', 'descPagamento':'Aditivo, anulação e saldo não tipificados'}])
    candidate=result['candidates'][0]
    assert candidate['documented_amount'] is None and candidate['phase']=='pago'
    assert 'numCpfCnpj' not in candidate and 'descFornecedor' not in candidate
    assert result['net_balance'] is None and not result['consumption_proven']


def test_official_year_filter_ignored_rejects_entire_page():
    with pytest.raises(FinanceEvidenceError, match='SOURCE_PERIOD_MISMATCH'):
        check([row(), {**row(), 'numExercicio':'2010', 'dtPagamento':'04/01/2010'}])


def test_absent_identity_or_empty_page_does_not_prove_coverage():
    with pytest.raises(FinanceEvidenceError, match='MISSING_FINANCIAL_IDENTITY'):
        check([{**row(), 'numEmpenho':''}])
    result=check([])
    assert result['coverage'] is None and result['records_imported'] is None
