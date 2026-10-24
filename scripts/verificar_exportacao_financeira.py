"""Validate saved, hashed official payment probes; no database writes or HTTP."""
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.municipal_finance import payment_candidates, FinanceEvidenceError


def main():
    folder=ROOT/'.runtime/irps-municipal/financial-discovery'
    proofs=json.loads((folder/'payment-scope-probes.json').read_text(encoding='utf-8'))
    output=[]
    for proof in proofs:
        # Only the exact, institutionally linked anonymous export is evaluated.
        year=next((y for y in (2025,2026) if proof['url']==
            f'https://dadosabertos-portalfacil.azurewebsites.net/api/pagamentos?type=json&idCliente=97&page=1&pageSize=100&numAno={y}'),None)
        if year is None:raise ValueError('UNVERIFIED_EXPORT_URL')
        file=(folder/proof['file']).resolve()
        if file.parent!=folder.resolve():raise ValueError('INVALID_EVIDENCE_PATH')
        body=file.read_bytes()
        if proof['status']!=200 or hashlib.sha256(body).hexdigest()!=proof['sha256']:
            raise ValueError('INVALID_SAVED_EVIDENCE')
        record={k:proof[k] for k in ('url','status','at','sha256','rows','exercise_values')}
        try:
            result=payment_candidates(json.loads(body),start=date(year,1,1),end=date(year,12,31))
            record.update(state='candidates_require_review',candidates=len(result['candidates']))
        except FinanceEvidenceError as exc:
            record.update(state='rejected',reason=str(exc))
        output.append(record)
    report={'at':datetime.now(timezone.utc).isoformat(),'probes':output,
        'database_mutated':False,'financial_rows_imported':None,'financial_coverage':None,
        'net_balance':None,'item_associations_created':False}
    (folder/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
