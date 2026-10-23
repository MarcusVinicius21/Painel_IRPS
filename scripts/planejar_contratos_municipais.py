"""Preview or persist bounded contract plans using the evidenced municipal buyer census."""
import argparse,json,sys
from datetime import date,timedelta
from pathlib import Path
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.sources import job_context
from app.opportunity_schemas import HistoricalScope
from app.municipal_contracts import create_contract_plan,create_linked_contract_plan,create_ata_plan,create_linked_ata_plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--kind',choices=('contracts','contract-updates','contracts-linked','atas','atas-updates','atas-linked'),default='contracts')
    parser.add_argument('--months',nargs='+')
    args=parser.parse_args();folder=ROOT/'.runtime/irps-municipal'
    scope=json.loads((folder/'census.json').read_text(encoding='utf-8'))['scope']
    buyers=json.loads((folder/'buyers.json').read_text(encoding='utf-8'))
    cnpjs=sorted({b['cnpj'] for b in buyers if b['state']=='verified' and not b['conflicting_evidence']
        and b['identities'] and all(i['municipal_buyer'] for i in b['identities'])})
    if not cnpjs:parser.error('Não há CNPJ municipal com identidade comprovada no censo.')
    months=args.months or scope['months'];cities=[c['ibge'] for c in scope['municipalities']]
    if len(set(months))!=len(months) or set(months)-set(scope['months']):parser.error('Selecione competências únicas do manifesto.')
    if not args.execute:
        print(json.dumps({'executed':False,'kind':args.kind,'municipalities':cities,'organization_cnpjs':cnpjs,'months':months}));return
    settings=load_settings()
    if settings.auth_mode!='operational_local' or settings.ai_enabled or make_url(settings.database_url.get_secret_value()).host not in ('localhost','127.0.0.1','::1'):
        parser.error('Use o banco operacional local, sem IA paga.')
    database=Database(settings);plans=[]
    try:
        for month in months:
            first=date.fromisoformat(month+'-01');following=date(first.year+(first.month==12),first.month%12+1,1)
            body=HistoricalScope(municipalities=cities,start=first,end=following-timedelta(days=1),
                publications=False,items=False,results=False,contracts=args.kind in ('contracts','contracts-linked'),
                contract_updates=args.kind=='contract-updates',atas=args.kind.startswith('atas'),organization_cnpjs=cnpjs,size=20,max_pages=2000)
            with database.transaction(settings.operator_org_id,settings.operator_actor_id) as db:
                ctx=job_context(db,settings.operator_org_id,settings.operator_actor_id)
                if args.kind in ('contracts-linked','atas-linked'):
                    parents=db.all("""SELECT f.id FROM procurement_fact f JOIN buyer b ON b.id=f.buyer_id
                        WHERE f.org_id=:o AND f.classification='official' AND f.provider='PNCP' AND f.is_current
                        AND f.event_date BETWEEN :start AND :end AND f.municipality_ibge=ANY(:cities)
                        AND b.classification='official' AND b.government_level='M' AND b.cnpj=ANY(:cnpjs)
                        ORDER BY f.id LIMIT 2001""",{'o':settings.operator_org_id,'start':first,'end':following-timedelta(days=1),'cities':cities,'cnpjs':cnpjs})
                    if not parents:
                        print(json.dumps({'month':month,'state':'no_saved_eligible_publications','municipal_completeness':None}));continue
                    result=(create_linked_contract_plan if args.kind=='contracts-linked' else create_linked_ata_plan)(ctx,[str(p['id']) for p in parents])
                elif args.kind.startswith('atas'):result=create_ata_plan(ctx,body,updated=args.kind=='atas-updates')
                else:result=create_contract_plan(ctx,body)
            plans.append({'month':month,**result})
            (folder/(args.kind+'-plans.json')).write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(plans[-1],ensure_ascii=False),flush=True)
    finally:database.engine.dispose()


if __name__=='__main__':main()
