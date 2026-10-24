"""Read-only full catalogue triage; private CSV is not a confirmed whitelist."""
import csv,json,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.portfolio_rules import VERSION,GROUPS,classify


def main():
    s=load_settings();d=Database(s);folder=ROOT/'.runtime/irps-fcp';folder.mkdir(exist_ok=True)
    d.engine.update_execution_options(isolation_level='REPEATABLE READ')
    scanned=0;counts=Counter();groups=defaultdict(Counter);samples=defaultdict(list);codes=set()
    try:
        with d.transaction(s.operator_org_id,s.operator_actor_id) as db, (folder/'portfolio-correspondencias.csv').open('w',encoding='utf-8',newline='') as f:
            db.execute('SET TRANSACTION READ ONLY')
            writer=csv.DictWriter(f,fieldnames=['snapshot_id','snapshot_sha256','kind','code','name','active','class_name','pdm_name',
                'group_id','technical_status','commercial_status','subgroup','reason','rule_version','cross_purchase_equivalence','multiple_group_reason'])
            writer.writeheader()
            query=db.conn.execute(text('''SELECT e.snapshot_id,s.sha256 AS snapshot_sha256,s.kind,e.code,e.name,e.active,e.class_name,e.pdm_name
                FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id
                WHERE s.id IN (SELECT DISTINCT ON(kind) id FROM national_catalogue_snapshot ORDER BY kind,imported_at DESC,id DESC)
                ORDER BY s.kind,e.code'''),execution_options={'stream_results':True,'yield_per':1000})
            try:
                for row in query.mappings():
                    entry=dict(row);entry['snapshot_id']=str(entry['snapshot_id']);scanned+=1
                    for match in classify(entry):
                        record={**entry,**match};writer.writerow(record);state=match['technical_status'];group=match['group_id']
                        counts[state]+=1;groups[group][state]+=1;codes.add((entry['kind'],entry['code'],entry['snapshot_id']))
                        if len(samples[group])<8:samples[group].append(record)
            finally:query.close()
        report={'at':datetime.now(timezone.utc).isoformat(),'rule_version':VERSION,'catalogue_rows_scanned':scanned,
            'classified_pairs':dict(counts),'distinct_codes_with_any_classification':len(codes),
            'commercial_confirmed':0,'groups':[{'id':gid,'name':name,'scope':scope,'counts':dict(groups[gid]),
                'sample':samples[gid]} for gid,name,scope in GROUPS],
            'source':'Local immutable national catalogue snapshots; original CSV fields retained.',
            'unmatched_state':'EXCLUDED_FROM_PRIORITY_RULE_NOT_DELETED','database_mutated':False,
            'limitations':['Conservative automatic triage; not human technical approval or commercial confirmation.',
                'A code is not technical equivalence across packaging, concentration or specification.']}
        (folder/'portfolio-classification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='groups'},ensure_ascii=False))
    finally:d.engine.dispose()


if __name__=='__main__':main()
