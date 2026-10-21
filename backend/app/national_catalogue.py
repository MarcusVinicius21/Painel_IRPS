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


def import_csv(database_url, path, kind, origin='Arquivo fornecido pelo operador; origem oficial corrente não certificada.'):
    if kind not in ('CATMAT','CATSER'):
        raise ValueError('Escolha CATMAT ou CATSER.')
    path = Path(path)
    with path.open('rb') as source:digest = hashlib.file_digest(source, 'sha256').hexdigest()
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
    return normalize(row)


def search(ctx, q='', kind=None, active=None, group=None, classification=None, snapshot=None, offset=0, limit=25):
    ctx.require('read')
    term=''.join(c for c in unicodedata.normalize('NFKD',q.strip().casefold()) if not unicodedata.combining(c))
    params={'q':term,'kind':kind,'active':active,'group':group,'class':classification,'s':snapshot,'offset':offset,'limit':limit+1,'fetch':offset+limit+1}
    snapshot_filter=' WHERE id=CAST(:s AS uuid)' if snapshot else ' WHERE kind=:kind' if kind else ''
    if snapshot and kind:snapshot_filter+=' AND kind=:kind'
    filters=['e.snapshot_id=s.id']
    if active is not None:filters.append('e.active=:active')
    if group is not None:filters.append('e.group_code=:group')
    if classification is not None:filters.append('e.class_code=:class')
    if q.strip():filters.append('e.code=:q' if q.strip().isdigit() else "e.search_vector @@ plainto_tsquery('portuguese',:q)")
    # Each snapshot uses its (snapshot_id,code) index before the outer merge.
    # A blank first page must not sort the entire 348k-row national catalogue.
    rows=ctx.db.all('''WITH chosen AS MATERIALIZED (
        SELECT DISTINCT ON(kind) * FROM national_catalogue_snapshot'''+snapshot_filter+''' ORDER BY kind,imported_at DESC,id DESC)
        SELECT e.snapshot_id,e.code,e.name,e.active,e.group_code,e.group_name,e.class_code,e.class_name,e.pdm_code,e.pdm_name,
            s.kind,s.sha256,s.origin,s.imported_at
        FROM chosen s CROSS JOIN LATERAL (
            SELECT * FROM national_catalogue_entry e WHERE '''+' AND '.join(filters)+'''
            ORDER BY e.code LIMIT :fetch) e
        ORDER BY s.kind,e.code LIMIT :limit OFFSET :offset''',params)
    snapshots=ctx.db.all('SELECT * FROM national_catalogue_snapshot ORDER BY imported_at DESC,id DESC LIMIT 20')
    return normalize({'records':rows[:limit],'next_offset':offset+limit if len(rows)>limit else None,'snapshots':snapshots,'purchase_history_implied':False})
