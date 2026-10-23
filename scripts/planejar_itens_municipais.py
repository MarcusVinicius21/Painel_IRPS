"""Plan item pagination from saved publications; preview unless --execute is explicit."""
from pathlib import Path
from datetime import date,timedelta
import argparse,json,sys
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.sources import job_context
from app.municipal_items import create_item_plan
from app.municipal_results import create_result_plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--months',nargs='+')
    parser.add_argument('--kind',choices=('items','results'),default='items')
    args=parser.parse_args()
    folder=ROOT/'.runtime/irps-municipal'
    scope=json.loads((folder/'census.json').read_text(encoding='utf-8'))['scope']
    months=args.months or scope['months']
    if len(set(months))!=len(months) or set(months)-set(scope['months']):parser.error('Selecione competências únicas do manifesto.')
    cities=[r['ibge'] for r in scope['municipalities']]
    if not args.execute:
        print(json.dumps({'executed':False,'kind':args.kind,'months':months,'municipalities':cities,
            'scope':'Somente publicações oficiais já salvas; não comprova cobertura integral.'},ensure_ascii=False));return
    settings=load_settings()
    if settings.auth_mode!='operational_local' or settings.ai_enabled or make_url(settings.database_url.get_secret_value()).host not in ('127.0.0.1','localhost','::1'):
        parser.error('Use a configuração operacional local sem IA paga.')
    database=Database(settings);plans=[]
    try:
        for month in months:
            first=date.fromisoformat(month+'-01');following=date(first.year+(first.month==12),first.month%12+1,1)
            with database.transaction(settings.operator_org_id,settings.operator_actor_id) as db:
                result=(create_item_plan if args.kind=='items' else create_result_plan)(job_context(db,settings.operator_org_id,settings.operator_actor_id),cities,first,following-timedelta(days=1))
            plans.append({'month':month,**result})
            (folder/(args.kind+'-plans.json')).write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(plans[-1],ensure_ascii=False),flush=True)
    finally:database.engine.dispose()


if __name__=='__main__':main()
