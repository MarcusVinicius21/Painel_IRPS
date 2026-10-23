"""Failure taxonomy for durable public requests; retries never imply coverage."""
import random

MAX_ATTEMPTS = 3
FAILED_STATES = frozenset(('failed', 'failed_retryable', 'blocked', 'quarantined'))


def host_key(provider):
    return 'PNCP_HOST' if provider.startswith('PNCP') else provider


def policy(code, status, attempts, retry_after=60):
    if status is not None and 400 <= status < 500 and status not in (408, 429):
        return {'state': 'blocked', 'retry_after': None, 'reason': 'access_or_resource_unverified'}
    if code.startswith(('INVALID_', 'MISSING_', 'PAGINATION_', 'SOURCE_PAGE_', 'RESPONSE_LIMIT')) or code == 'HISTORY_PAGE_FAILED':
        return {'state': 'quarantined', 'retry_after': None, 'reason': 'source_or_processing_requires_review'}
    if attempts >= MAX_ATTEMPTS:
        return {'state': 'blocked', 'retry_after': None, 'reason': 'retry_exhausted'}
    delay = max(retry_after, 60 * (2 ** max(attempts - 1, 0))) + int(random.uniform(1, 10))
    return {'state': 'failed_retryable', 'retry_after': delay, 'reason': 'controlled_retry'}
