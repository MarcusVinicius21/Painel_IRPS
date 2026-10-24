"""Read-only validation of the Ipatinga-linked Actcon payment export.

Candidates are not procurement facts: this source does not identify purchased
items, reversals, contract amendments or a reconciled financial balance.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json


class FinanceEvidenceError(ValueError):
    pass


def payment_candidates(rows, *, start: date, end: date):
    """Reject a whole out-of-scope/conflicting page, never silently filter it.

    Exact copies collapse within this response only. The composite source key
    retains installments and organizational units; no cross-source identity is
    inferred. Persistence and financial netting remain disabled.
    """
    if start > end or not isinstance(rows, list) or len(rows) > 100:
        raise FinanceEvidenceError('INVALID_PAGE_OR_PERIOD')
    seen = {}; result = []
    for row in rows:
        if not isinstance(row, dict):
            raise FinanceEvidenceError('INVALID_ROW')
        required = ('numExercicio', 'numUnidade', 'numEmpenho', 'numPagamento', 'dtPagamento')
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            raise FinanceEvidenceError('MISSING_FINANCIAL_IDENTITY')
        try:
            day = datetime.strptime(row['dtPagamento'], '%d/%m/%Y').date()
            exercise = int(row['numExercicio'])
        except (ValueError, TypeError):
            raise FinanceEvidenceError('INVALID_FINANCIAL_DATE') from None
        if not start <= day <= end:
            raise FinanceEvidenceError('SOURCE_PERIOD_MISMATCH')
        if exercise != day.year:
            raise FinanceEvidenceError('EXERCISE_DATE_REQUIRES_REVIEW')
        raw_amount = row.get('vlPagamento')
        amount = None
        if raw_amount not in (None, ''):
            try:
                if not isinstance(raw_amount, str):
                    raise InvalidOperation
                amount = Decimal(raw_amount)
                if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
                    raise InvalidOperation
            except InvalidOperation:
                raise FinanceEvidenceError('AMOUNT_OR_REVERSAL_REQUIRES_REVIEW') from None
        key = tuple(row[k].strip() for k in required[:4])
        digest = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if key in seen:
            if seen[key] != digest:
                raise FinanceEvidenceError('CONFLICTING_FINANCIAL_IDENTITY')
            continue
        seen[key] = digest
        # No supplier name/CPF, bank account or free-text narrative is exposed.
        result.append({'source_key': key, 'municipality_ibge': '3131307',
            'buyer_cnpj': '19876424000142', 'phase': 'pago', 'date': day.isoformat(),
            'documented_amount': str(amount) if amount is not None else None,
            'currency': 'BRL', 'source_record_sha256': digest,
            'quantity': None, 'item_id': None, 'contract_id': None,
            'link_state': 'unlinked', 'review_required': True})
    return {'candidates': result, 'source_rows': len(rows),
        'exact_duplicate_rows': len(rows)-len(result), 'records_imported': None,
        'coverage': None, 'net_balance': None, 'consumption_proven': False,
        'limitations': ['SOURCE_IDENTITY_REQUIRES_REVIEW', 'REVERSALS_NOT_DOCUMENTED',
            'NO_ITEM_OR_CONTRACT_LINK', 'NO_COMPLETENESS_DENOMINATOR']}
