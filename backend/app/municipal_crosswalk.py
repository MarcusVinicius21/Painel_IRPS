"""Strong process crosswalk, deliberately separate from additive event totals."""
from collections import defaultdict
import re

PROCESS=re.compile(r'^(\d{14})-1-(\d+)/(\d{4})$')
VERIFIED_PROVIDERS=frozenset(('PNCP','PNCP_ITENS','PNCP_RESULTADOS','PNCP_CONTRATOS'))


def process_key(row):
    # External portal/TCE identity contracts have not been validated yet. An
    # arbitrary metadata flag or coincident description cannot enroll a source.
    if row.get('classification')!='official' or row.get('provider') not in VERIFIED_PROVIDERS:
        return None,'SOURCE_PROCESS_CONTRACT_UNVERIFIED'
    match=PROCESS.fullmatch(str(row.get('obligation_id') or ''))
    if not match:return None,'STRONG_PROCESS_ID_MISSING'
    if row.get('buyer_cnpj')!=match[1]:return None,'BUYER_PROCESS_ID_CONFLICT'
    return (match[1],match[3],str(int(match[2]))),None


def crosswalk(rows):
    groups=defaultdict(list);pending=[]
    for row in rows:
        key,reason=process_key(row)
        if key is None:
            pending.append({'fact_id':str(row['id']),'reason':reason});continue
        groups[key].append(row)
    output=[]
    for key,records in sorted(groups.items()):
        # Same process can have many contracts, winners, phases and item lines.
        # Preserve all of them, and all revisions/evidence IDs, without summing.
        output.append({'buyer_cnpj':key[0],'year':key[1],'sequence':key[2],
            'state':'verified_process_identity','confidence_basis':'exact_official_pncp_id_and_buyer',
            'fact_ids':sorted(str(r['id']) for r in records),
            'source_ids':sorted({str(r['source_id']) for r in records}),
            'providers':sorted({r['provider'] for r in records}),
            'phases':sorted({r['phase'] for r in records}),
            'municipalities':sorted({r['municipality_ibge'] for r in records if r.get('municipality_ibge')}),
            'amount':None,'quantity':None,'event_merges_applied':False})
    return {'version':1,'processes':output,'distinct_identified_processes':len(output),
        'pending_match':pending,'pending_records':len(pending),'facts_considered':len(rows),
        'cross_source_event_matches':0,'source_coverage':None,'database_mutated':False,
        'limitation':'Process identity does not prove that item, contract and financial events are the same fact.'}
