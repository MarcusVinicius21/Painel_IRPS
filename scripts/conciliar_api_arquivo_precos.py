"""Bounded public API audit; output excludes suppliers and never merges sources."""
import argparse,hashlib,json,sys,time
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import httpx,psycopg
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings

def identity(purchase,item):
    if purchase is None or item is None:raise ValueError('Missing source identity')
    if isinstance(purchase,float) or isinstance(item,float):raise ValueError('Floating point source identity rejected')
    return str(purchase)+':'+str(item)

def reconcile(api,csv):
    def index(rows):
        keys={}
        for row in rows:
            key=identity(row['purchase'],row['item'])
            if key in keys:raise ValueError('Repeated identity; review versions before reconciliation')
            keys[key]=row
        return keys
    a,b=index(api),index(csv);different=[]
    for key in sorted(a.keys()&b.keys()):
        fields=[]
        for field in ('date','quantity','price'):
            left,right=a[key].get(field),b[key].get(field)
            if field!='date':
                left=None if left is None or left=='' else Decimal(str(left))
                right=None if right is None or right=='' else Decimal(str(right))
            if left!=right:fields.append(field)
        if fields:different.append({'key':key,'fields':fields})
    return {'api_records':len(a),'csv_records':len(b),'common':len(a.keys()&b.keys()),
            'only_api':sorted(a.keys()-b.keys()),'only_csv':sorted(b.keys()-a.keys()),'changed_fields':different,'sources_merged':False}

def audit(code,month):
    start=month+'-01'
    import calendar
    end=month+'-'+str(calendar.monthrange(int(month[:4]),int(month[5:]))[1])
    rows=[];pages=[];total=None
    with httpx.Client(timeout=30,follow_redirects=False) as client:
        for page in range(1,11):
            params={'codigoItemCatalogo':code,'dataCompraInicio':start,'dataCompraFim':end,'pagina':page,'tamanhoPagina':100}
            for attempt in range(3):
                response=client.get('https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico',params=params)
                if response.status_code not in (429,502,503,504):break
                time.sleep(min(10,2**attempt))
            response.raise_for_status();body=response.json()
            if total is None:total=body['totalRegistros']
            if body['totalRegistros']!=total:raise ValueError('Source changed during pagination; retry audit')
            if body['totalPaginas']>10:raise ValueError('Explicit audit request budget exceeded')
            pages.append({'url':str(response.url),'status':response.status_code,'sha256':hashlib.sha256(response.content).hexdigest(),'rows':len(body['resultado'])})
            rows.extend({'purchase':x['idCompra'],'item':x['idItemCompra'],'date':x['dataCompra'][:10],
                         'quantity':x.get('quantidade'),'price':x.get('precoUnitario')} for x in body['resultado'])
            if page>=body['totalPaginas']:break
            time.sleep(1)
    if len(rows)!=total:raise ValueError('Pagination reconciliation failed')
    s=load_settings()
    if s.auth_mode!='operational_local':raise ValueError('Select operational read-only audit configuration')
    with psycopg.connect(s.database_url.get_secret_value().replace('+psycopg','')) as c:
        c.execute('SET TRANSACTION READ ONLY');c.execute("SELECT set_config('irps.org_id',%s,true)",(s.operator_org_id,))
        csv=c.execute("SELECT r.source_key,r.body FROM price_monthly_record r JOIN price_monthly_snapshot s ON s.org_id=r.org_id AND s.id=r.snapshot_id WHERE s.kind='servico' AND s.month=%s AND r.code=%s",(start,code)).fetchall()
    originals=[{'purchase':body['purchase_id'],'item':key[len(body['purchase_id'])+1:],'date':body['purchase_date'],'quantity':body.get('quantity'),'price':body.get('unit_price')} for key,body in csv]
    return {'code':code,'month':month,'consulted_at':datetime.now(timezone.utc).isoformat(),'pages':pages,**reconcile(rows,originals)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--code',default='14729');p.add_argument('--month',default='2026-09');p.add_argument('--output',required=True);a=p.parse_args()
    output=(ROOT/a.output).resolve();assert (ROOT/'.runtime').resolve() in output.parents
    result=audit(a.code,a.month);output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
