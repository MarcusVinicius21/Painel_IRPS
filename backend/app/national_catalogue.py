"""Local CSV snapshot import and bounded database search. No network synchronization."""
import csv
import hashlib
import json,unicodedata
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from .db import normalize
from .security import fail


def import_csv(database_url, path, kind, origin='Arquivo fornecido pelo operador; origem oficial corrente não certificada.',expected_sha256=None,expected_records=None):
    if kind not in ('CATMAT','CATSER'):
        raise ValueError('Escolha CATMAT ou CATSER.')
    path = Path(path)
    with path.open('rb') as source:digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if expected_sha256 is not None and digest!=expected_sha256:raise ValueError('Checksum diferente do snapshot oficial validado.')
    code_key, name_key, active_key = ('codigoItem','descricaoItem','statusItem') if kind == 'CATMAT' else ('codigoServico','nomeServico','statusServico')
    with psycopg.connect(database_url.replace('postgresql+psycopg://','postgresql://')) as conn:
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('national:'+kind,))
        prior = conn.execute('SELECT id,row_count,active_count,inactive_count FROM national_catalogue_snapshot WHERE kind=%s AND sha256=%s', (kind,digest)).fetchone()
        if prior:
            return {'snapshot_id':str(prior[0]),'rows':prior[1],'active':prior[2],'inactive':prior[3],'sha256':digest,'duplicate':True,'rejected':0}
        sid = str(uuid4())
        # Staging and snapshot commit atomically. Invalid input never publishes a partial catalogue.
        conn.execute('CREATE TEMP TABLE catalogue_stage(code text PRIMARY KEY,name text NOT NULL,active boolean NOT NULL,group_code text,group_name text,class_code text,class_name text,pdm_code text,pdm_name text,original jsonb) ON COMMIT DROP')
        rows = active = 0
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader = csv.DictReader(f,delimiter=';')
            if not set((code_key,name_key,active_key)).issubset(reader.fieldnames or []):
                raise ValueError('Colunas obrigatórias ausentes no CSV.')
            with conn.cursor().copy('COPY catalogue_stage FROM STDIN') as copy:
                for line, row in enumerate(reader,2):
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError(f'Linha {line}: colunas inconsistentes.')
                    code, name, state = row[code_key],row[name_key],row[active_key]
                    if not code.isascii() or not code.isdigit() or not name.strip() or state not in ('True','False'):
                        raise ValueError(f'Linha {line}: código, descrição ou situação inválidos.')
                    rows += 1; active += state == 'True'
                    copy.write_row((code,name,state=='True',row.get('codigoGrupo'),row.get('nomeGrupo'),row.get('codigoClasse'),row.get('nomeClasse'),row.get('codigoPdm'),row.get('nomePdm'),Jsonb(row)))
        if not rows:raise ValueError('O catálogo está vazio.')
        if expected_records is not None and rows!=expected_records:raise ValueError('A contagem não corresponde ao manifesto oficial.')
        with path.open('rb') as source:
            if hashlib.file_digest(source,'sha256').hexdigest()!=digest:raise ValueError('O arquivo mudou durante a importação. Tente novamente com uma cópia estável.')
        conn.execute('INSERT INTO national_catalogue_snapshot(id,kind,sha256,filename,origin,row_count,active_count,inactive_count) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(sid,kind,digest,path.name,origin,rows,active,rows-active))
        conn.execute('INSERT INTO national_catalogue_entry(snapshot_id,code,name,active,group_code,group_name,class_code,class_name,pdm_code,pdm_name,original) SELECT %s,* FROM catalogue_stage',(sid,))
        actual = conn.execute('SELECT count(*) FROM national_catalogue_entry WHERE snapshot_id=%s',(sid,)).fetchone()[0]
        if actual != rows:raise ValueError('A contagem de importação não foi conciliada.')
        return {'snapshot_id':sid,'rows':rows,'active':active,'inactive':rows-active,'sha256':digest,'duplicate':False,'rejected':0}


def entry(ctx, snapshot, code):
    ctx.require('read')
    row = ctx.db.one('SELECT e.*,s.kind,s.sha256,s.origin,s.imported_at FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id WHERE e.snapshot_id=:s AND e.code=:c',{'s':snapshot,'c':code})
    if not row:fail(404,'Este código não está disponível nesta versão do catálogo.','CATALOGUE_NOT_FOUND')
    row.pop('search_vector',None)
    source=ctx.db.one('SELECT * FROM national_catalogue_snapshot WHERE id=:s',{'s':snapshot})
    row['source_summary']=snapshot_info(source)
    row['official_snapshot']=row['source_summary']['official_snapshot']
    return normalize(row)


def snapshot_info(row):
    try:provenance=json.loads(row['origin'])
    except (ValueError,TypeError):provenance={}
    if not isinstance(provenance,dict):provenance={}
    expected=provenance.get('unique_valid_records')
    verified=bool(provenance.get('official_snapshot') and provenance.get('reconciled') and provenance.get('sha256')==row['sha256'] and expected==row['row_count'])
    return {'id':row['id'],'kind':row['kind'],'sha256':row['sha256'],'imported_at':row['imported_at'],
        'row_count':row['row_count'],'active_count':row['active_count'],'inactive_count':row['inactive_count'],
        'source_url':provenance.get('source_url') if verified else None,'version':provenance.get('snapshot_version') if verified else None,
        'official_snapshot':verified,'source_records':expected if verified else None,'import_complete':verified,
        'import_percent':'100' if verified else None,'denominator':'Códigos únicos do CSV oficial identificado, incluindo inativos.' if verified else 'Origem oficial ainda não certificada.'}


def search(ctx, q='', kind=None, active=None, group=None, classification=None, snapshot=None, offset=0, limit=25):
    ctx.require('read')
    term=''.join(c for c in unicodedata.normalize('NFKD',q.strip().casefold()) if not unicodedata.combining(c))
    params={'q':term,'kind':kind,'active':active,'group':group,'class':classification,'s':snapshot,'o':ctx.org_id}
    snapshot_filter=' WHERE id=CAST(:s AS uuid)' if snapshot else ' WHERE kind=:kind' if kind else ''
    if snapshot and kind:snapshot_filter+=' AND kind=:kind'
    chosen=ctx.db.all('SELECT DISTINCT ON(kind) * FROM national_catalogue_snapshot'+snapshot_filter+' ORDER BY kind,imported_at DESC,id DESC',params)
    filters=['e.snapshot_id=:snapshot']
    if active is not None:filters.append('e.active=:active')
    if group is not None:filters.append('e.group_code=:group')
    if classification is not None:filters.append('e.class_code=:class')
    if q.strip():filters.append('e.code=:q' if q.strip().isdigit() else "e.search_vector @@ plainto_tsquery('portuguese',:q)")
    where=' AND '.join(filters);unfiltered=not q.strip() and active is None and group is None and classification is None
    counts=[]
    for source in chosen:
        scope={**params,'snapshot':source['id']}
        count=source['row_count'] if unfiltered else ctx.db.one('SELECT count(*) AS n FROM national_catalogue_entry e WHERE '+where,scope)['n']
        counts.append((source,count))
    total=sum(count for _,count in counts);remaining_offset=offset;rows=[]
    # Skip entire catalogue partitions by their exact counts. Fetch only the requested rows.
    for source,count in counts:
        if remaining_offset>=count:remaining_offset-=count;continue
        take=limit-len(rows)
        if take<=0:break
        part=ctx.db.all('''WITH page_keys AS MATERIALIZED (
            SELECT e.snapshot_id,e.code FROM national_catalogue_entry e WHERE '''+where+'''
            ORDER BY e.code LIMIT :take OFFSET :skip)
            SELECT e.snapshot_id,e.code,e.name,e.active,e.group_code,e.group_name,e.class_code,e.class_name,e.pdm_code,e.pdm_name,
            (SELECT count(*) FROM national_product_link l JOIN canonical_product p ON p.org_id=l.org_id AND p.id=l.product_id
             WHERE l.org_id=:o AND l.snapshot_id=e.snapshot_id AND l.code=e.code AND p.classification='official'
             AND NOT EXISTS(SELECT 1 FROM canonical_product newer WHERE newer.org_id=p.org_id AND newer.supersedes_id=p.id)) AS reviewed_link_count
            FROM page_keys k JOIN national_catalogue_entry e ON e.snapshot_id=k.snapshot_id AND e.code=k.code ORDER BY e.code''',
            {**params,'snapshot':source['id'],'take':take,'skip':remaining_offset})
        info=snapshot_info(source)
        for row in part:row.update(kind=source['kind'],sha256=source['sha256'],origin=source['origin'],imported_at=source['imported_at'],official_snapshot=info['official_snapshot'])
        rows.extend(part);remaining_offset=0
    snapshots=ctx.db.all('SELECT * FROM national_catalogue_snapshot ORDER BY imported_at DESC,id DESC LIMIT 20')
    return normalize({'records':rows,'total':total,'offset':offset,'limit':limit,
        'next_offset':offset+limit if offset+limit<total else None,'last_offset':((total-1)//limit)*limit if total else 0,
        'selected_snapshots':[snapshot_info(s) for s in chosen],'snapshots':snapshots,'purchase_history_implied':False,
        'search_method':'Código exato ou palavras da descrição; não implica equivalência técnica.'})
