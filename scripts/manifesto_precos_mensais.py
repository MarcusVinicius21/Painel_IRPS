"""Private, resumable annual source ledger; one writer and immutable hash-named archives."""
import argparse,contextlib,csv,hashlib,io,json,os,sys,time,uuid,zipfile
from datetime import date,datetime,timezone
from pathlib import Path
import httpx,psycopg
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.monthly_prices import month_sequence
from monthly_import_support import OFFICIAL,private_path,digest

@contextlib.contextmanager
def single_writer(folder):
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'writer.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:
            lock.seek(0)
            if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock,fcntl.LOCK_UN)

def save(path,data):
    tmp=path.with_suffix('.tmp-'+uuid.uuid4().hex);tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');os.replace(tmp,path)

def fresh():
    return {'window':['2025-10-01','2026-09-30'],'files':[{'kind':kind,'month':month[:7],'url':OFFICIAL+month[:7].replace('-','/')+'/'+kind+'_'+month[:7].replace('-','_')+'.csv.zip','state':'not_started','versions':[]} for month in month_sequence(date(2025,10,1),date(2026,9,30)) for kind in ['material','servico']],'events':[]}

def event(data,item,state,**fields):
    item.update(state=state,**fields);data['events'].append({'kind':item['kind'],'month':item['month'],'state':state,'at':datetime.now(timezone.utc).isoformat(),**fields})

def sync_database(data):
    s=load_settings()
    if s.auth_mode!='operational_local':raise ValueError('Operational local configuration required')
    with psycopg.connect(s.database_url.get_secret_value().replace('+psycopg','')) as c:
        c.execute('SET TRANSACTION READ ONLY');c.execute("SELECT set_config('irps.org_id',%s,true)",(s.operator_org_id,))
        for item in data['files']:
            rows=c.execute('SELECT id,archive_sha256,source_rows,accepted_rows,rejected_rows,duplicate_rows,imported_at FROM price_monthly_snapshot WHERE kind=%s AND month=%s ORDER BY imported_at,id',(item['kind'],item['month']+'-01')).fetchall()
            if not rows:continue
            sid,sha,source,accepted,rejected,duplicates,at=rows[-1]
            actual=c.execute('SELECT count(*) FROM price_monthly_record WHERE snapshot_id=%s',(sid,)).fetchone()[0]
            state='reconciled' if actual==accepted and source==accepted+rejected+duplicates and rejected==0 else 'review_required'
            previous={v['sha256']:v for v in item['versions']}
            for old in rows:
                version=previous.setdefault(old[1],{'sha256':old[1]});version.update(snapshot_id=str(old[0]),state=state if old[0]==sid else 'replaced_by_revision')
            item['versions']=list(previous.values())
            if item.get('snapshot_id')!=str(sid) or item['state']!=state:event(data,item,state,snapshot_id=str(sid),sha256=sha,source_rows=source,accepted_rows=accepted,rejected_rows=rejected,duplicate_rows=duplicates,imported_at=at.isoformat())

def download(data,item,folder,path,refresh=False):
    if item['state']=='reconciled' and not refresh:return
    if not refresh and item['state']=='validated' and item.get('uncompressed_bytes') and item.get('path') and private_path(item['path']).exists() and digest(private_path(item['path']))==item.get('sha256'):
        return
    part=folder/(item['kind']+'-'+item['month']+'-'+uuid.uuid4().hex+'.part')
    with httpx.stream('GET',item['url'],timeout=httpx.Timeout(120,connect=20),follow_redirects=False) as response:
        response.raise_for_status()
        content_type=response.headers.get('content-type','').split(';')[0]
        if content_type not in ('application/zip','application/octet-stream','application/x-zip-compressed'):raise ValueError('Unexpected official archive Content-Type')
        size=0
        with part.open('xb') as stream:
            for chunk in response.iter_bytes(1024*1024):
                size+=len(chunk)
                if size>1024**3:raise ValueError('Archive exceeds one-GiB download bound')
                stream.write(chunk)
        if response.headers.get('content-length') and size!=int(response.headers['content-length']):raise ValueError('Incomplete HTTP body')
    sha=digest(part);final=folder/(item['kind']+'-'+item['month']+'-'+sha+'.zip')
    if not final.exists():part.rename(final)
    else:part.unlink()  # Only this invocation's newly created nonce temporary file.
    event(data,item,'downloaded',path=str(final.relative_to(ROOT)),sha256=sha,bytes=size,http_status=200,content_type=content_type);save(path,data)
    with zipfile.ZipFile(final) as archive:
        entries=archive.infolist()
        if len(entries)!=1 or not entries[0].filename.endswith('.csv') or entries[0].file_size>4*1024**3 or archive.testzip():raise ValueError('Archive CRC/scope/size failed')
        with archive.open(entries[0]) as source:
            reader=csv.DictReader(io.TextIOWrapper(source,encoding='utf-8-sig'),delimiter=';')
            if not {'id_compra','id_item_compra','codigo_item_catalogo','data_compra','preco_unitario','quantidade'}.issubset(reader.fieldnames or []):raise ValueError('Invalid official CSV schema')
        event(data,item,'validated',uncompressed_bytes=entries[0].file_size,crc=entries[0].CRC,validated_at=datetime.now(timezone.utc).isoformat())
    if not any(v['sha256']==sha for v in item['versions']):item['versions'].append({k:item[k] for k in ['sha256','path','bytes','uncompressed_bytes','crc','state','url']})
    save(path,data)

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',default='.runtime/irps-12-meses/sources');p.add_argument('--download-month');p.add_argument('--pair-output');p.add_argument('--refresh',action='store_true',help='Recheck approved official files; preserves every prior hash. Does not import.');a=p.parse_args();folder=private_path(a.folder);path=folder/'manifest.json'
    if a.refresh and not a.download_month:raise ValueError('Refresh requires one approved month')
    with single_writer(folder):
        data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else fresh();sync_database(data);save(path,data)
        if a.download_month:
            pair=[i for i in data['files'] if i['month']==a.download_month]
            if len(pair)!=2:raise ValueError('Month outside campaign')
            for item in pair:
                try:download(data,item,folder,path,a.refresh)
                except Exception as exc:
                    event(data,item,'failed',error_type=type(exc).__name__);save(path,data);raise
            if a.pair_output:private_path(a.pair_output).write_text(json.dumps(pair,indent=2),encoding='utf-8')
        print(json.dumps({'files':len(data['files']),'reconciled':sum(i['state']=='reconciled' for i in data['files']),'states':{i['kind']+':'+i['month']:i['state'] for i in data['files']}}))
if __name__=='__main__':main()
