"""Bounded shared campaign runner. Default preview; never reimports national prices."""
import argparse,json,sys,time
from datetime import date,datetime,timezone
from pathlib import Path
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize
from app.sources import job_context
from app.campaign_worker import tick
from app.municipal_items import create_item_plan
from app.municipal_results import create_result_plan
from app.municipal_contracts import create_linked_contract_plan,create_linked_ata_plan


def refresh_known(database,settings,start,end):
    folder=ROOT/'.runtime/irps-municipal';scope=json.loads((folder/'census.json').read_text(encoding='utf-8'))['scope']
    buyers=json.loads((folder/'buyers.json').read_text(encoding='utf-8'))
    cities=[c['ibge'] for c in scope['municipalities']]
    cnpjs=sorted({b['cnpj'] for b in buyers if b['state']=='verified' and not b['conflicting_evidence']
        and b['identities'] and all(i['municipal_buyer'] for i in b['identities'])})
    output=[]
    for month in scope['months']:
        first=date.fromisoformat(month+'-01');following=date(first.year+(first.month==12),first.month%12+1,1)
        from datetime import timedelta
        last=following-timedelta(days=1)
        if first<start or last>end:continue
        try:
            with database.transaction(settings.operator_org_id,settings.operator_actor_id) as db:
                ctx=job_context(db,settings.operator_org_id,settings.operator_actor_id)
                items=create_item_plan(ctx,cities,first,last);results=create_result_plan(ctx,cities,first,last)
                parents=db.all("""SELECT f.id FROM procurement_fact f JOIN buyer b ON b.id=f.buyer_id
                    WHERE f.org_id=:o AND f.classification='official' AND f.provider='PNCP' AND f.is_current
                    AND f.event_date BETWEEN :start AND :end AND f.municipality_ibge=ANY(:cities)
                    AND b.classification='official' AND b.government_level='M' AND b.cnpj=ANY(:cnpjs)
                    ORDER BY f.id LIMIT 2001""",{'o':ctx.org_id,'start':first,'end':last,'cities':cities,'cnpjs':cnpjs})
                linked=[fn(ctx,[str(p['id']) for p in parents]) for fn in (create_linked_contract_plan,create_linked_ata_plan)] if parents else []
        except ValueError:
            output.append({'month':month,'state':'requires_review','code':'REFRESH_SCOPE_REVIEW'});continue
        output.append({'month':month,'new_item_tasks':items['new_tasks'],'new_result_tasks':results['new_tasks'],
            'new_linked_tasks':sum(r.get('initial_tasks',0) for r in linked)})
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--ticks',type=int,default=1,choices=range(1,1001),metavar='1..1000')
    parser.add_argument('--refresh-every',type=int,default=0,choices=range(0,1001),metavar='0..1000')
    parser.add_argument('--start',type=date.fromisoformat,default=date(2025,10,1))
    parser.add_argument('--end',type=date.fromisoformat,default=date(2026,9,30))
    args=parser.parse_args();settings=load_settings()
    if settings.auth_mode!='operational_local' or settings.ai_enabled or make_url(settings.database_url.get_secret_value()).host not in ('localhost','127.0.0.1','::1'):
        parser.error('Use explicitamente o banco operacional local, sem IA paga.')
    database=Database(settings);folder=ROOT/'.runtime/irps-municipal'
    try:
        for number in range(1,args.ticks+1):
            if (folder/'STOP_AT_CAMPAIGN_CHECKPOINT').exists():break
            result=tick(database,settings.operator_org_id,settings.operator_actor_id,args.start,args.end,execute=args.execute)
            event=normalize({'tick':number,'at':datetime.now(timezone.utc).isoformat(),**result})
            (folder/'campaign-last-tick.json').write_text(json.dumps(event,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'tick':number,'pages':result.get('pages'),'advances':result.get('attempts'),
                'state':result.get('state'),'busy':result.get('busy',False)}),flush=True)
            if not args.execute or result.get('busy'):break
            if args.refresh_every and (number%args.refresh_every==0 or result.get('state')=='no_eligible_requests_now'):
                refresh=refresh_known(database,settings,args.start,args.end)
                (folder/'campaign-last-refresh.json').write_text(json.dumps(refresh,ensure_ascii=False,indent=2),encoding='utf-8')
                if sum(r.get('new_item_tasks',0)+r.get('new_result_tasks',0)+r.get('new_linked_tasks',0) for r in refresh):continue
            if result.get('state')=='no_eligible_requests_now' and not result.get('resumable_tasks'):break
            if not result.get('pages'):time.sleep(60)
    finally:database.engine.dispose()


if __name__=='__main__':main()
