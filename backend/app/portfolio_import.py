"""Append-only portfolio snapshot import; CLI-only, no commercial confirmations."""
import hashlib,json
from .portfolio_rules import GROUPS,VERSION
from .db import identifier,encoded


def import_rows(ctx,rows,*,rule_sha256,input_sha256,provenance):
    ctx.require('sources.sync')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':str(ctx.org_id)+':portfolio-import'})
    old=ctx.db.one('SELECT id FROM portfolio_run WHERE org_id=:o AND rule_sha256=:r AND input_sha256=:h',
        {'o':ctx.org_id,'r':rule_sha256,'h':input_sha256})
    if old:return {'id':str(old['id']),'duplicate':True,'inserted':0}
    rid=identifier();ctx.db.execute('''INSERT INTO portfolio_run(org_id,id,rule_version,rule_sha256,input_sha256,provenance,created_by)
        VALUES (:o,:i,:v,:r,:h,CAST(:p AS jsonb),:a)''',{'o':ctx.org_id,'i':rid,'v':VERSION,'r':rule_sha256,'h':input_sha256,'p':encoded(provenance),'a':ctx.actor_id})
    for code,name,scope in GROUPS:
        ctx.db.execute('INSERT INTO portfolio_group(org_id,run_id,code,name,scope) VALUES (:o,:r,:c,:n,:s)',
            {'o':ctx.org_id,'r':rid,'c':code,'n':name,'s':scope})
    conn=ctx.db.conn.connection.driver_connection
    values=[]
    for row in rows:
        if row['commercial_status'] not in ('COMMERCIAL_PENDING','OUT_OF_PORTFOLIO'):
            raise ValueError('RULES_CANNOT_CONFIRM_COMMERCIAL_OFFER')
        values.append((ctx.org_id,rid,row['group_id'],row['snapshot_id'],row['code'],row['technical_status'],
            row['commercial_status'],row['subgroup'],row['reason'],row.get('multiple_group_reason') or None))
    # COPY FROM cannot enforce PostgreSQL RLS. Use INSERT with the existing
    # application role/policy rather than disabling security for a bulk load.
    with conn.cursor() as cur:
        cur.executemany('''INSERT INTO portfolio_code_link(org_id,run_id,group_code,snapshot_id,code,technical_status,
            commercial_status,subgroup,reason,multiple_group_reason) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',values)
    ctx.audit('portfolio.rule_snapshot_imported',rid,{'records':len(rows),'rule_version':VERSION,'commercial_confirmed':0})
    return {'id':rid,'duplicate':False,'inserted':len(rows)}
