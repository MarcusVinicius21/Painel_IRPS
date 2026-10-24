"""Audit exact catalogue declarations using the existing technical review gate."""
from collections import Counter
from . import catalogue_evidence


def inspect_binding(fact, entry=None):
    record=catalogue_evidence.original_record(fact)
    declared=catalogue_evidence.declaration(record or {})
    base={'fact_id':str(fact['id']),'item_id':fact.get('item_id'),'item_version':fact.get('item_version'),
        'source_id':str(fact['source_id']),'source_sha256':fact.get('source_sha256'),
        'description':fact['description'],'unit':fact.get('unit'),
        'namespace':declared['namespace'],'code':declared['code'],
        'identity_preserved':True,'automatic_equivalence_created':False}
    if record is None:return {**base,'state':'requires_review','reasons':['ORIGINAL_RECORD_NOT_VERIFIED']}
    if not declared['namespace_verified']:
        return {**base,'state':'requires_review','reasons':['CATALOGUE_NAMESPACE_OR_CODE_MISSING']}
    if entry is None:
        return {**base,'state':'requires_review','reasons':['CODE_ABSENT_FROM_VALIDATED_SNAPSHOT']}
    checks=catalogue_evidence.automatic_checks(entry,fact,record)
    return {**base,'state':'eligible_existing_source_link' if checks['eligible'] else 'requires_review',
        'snapshot_id':str(entry['snapshot_id']),'reasons':checks['reasons'],
        'technical_equivalence_between_purchases':False}


def summarize(records):
    return {'facts_evaluated':len(records),'states':dict(Counter(r['state'] for r in records)),
        'reasons':dict(Counter(reason for row in records for reason in row['reasons'])),
        'distinct_declared_codes':len({(r['namespace'],r['code']) for r in records if r['namespace'] and r['code']}),
        'links_created':0,'technical_equivalences_created':0,'municipal_coverage':None}
