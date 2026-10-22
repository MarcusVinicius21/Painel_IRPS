"""Read-only raster previews of authorized, actually exported IRP PDFs."""
import io,shutil,subprocess,tempfile
from pathlib import Path
from pypdf import PdfReader
from . import director,exports
from .security import fail


def checked(ctx,runtime,did,aid):
    draft=director.draft(ctx,did)
    path,artifact=exports.authorized_file(ctx,runtime,aid)
    if artifact['media_type']!='application/pdf':fail(422,'Escolha um PDF exportado desta minuta.','PDF_REQUIRED')
    proof=ctx.db.one('''SELECT id FROM audit_event WHERE org_id=:o AND action='irp.draft_exported'
        AND resource_id=:d AND metadata->>'artifact_id'=:a AND metadata->>'format'='pdf' LIMIT 1''',{'o':ctx.org_id,'d':str(did),'a':str(aid)})
    if not proof:fail(404,'Este PDF não pertence à minuta selecionada.','NOT_FOUND')
    if draft['stale'] or draft['validation']['errors']:fail(409,'A minuta mudou ou tem bloqueios. Prepare e exporte a versão atual.','VERSION_CONFLICT')
    if path.stat().st_size>10_000_000:fail(422,'Este arquivo excede o limite da prévia. Use o download autorizado.')
    try:pages=len(PdfReader(path).pages)
    except Exception:fail(422,'Não foi possível ler este PDF. Gere o arquivo novamente.','PDF_UNREADABLE')
    if pages<1 or pages>200:fail(422,'A quantidade de páginas excede o limite da prévia.')
    return path,artifact,pages


def metadata(ctx,runtime,did,aid):
    _,artifact,pages=checked(ctx,runtime,did,aid)
    return {'pages':pages,'filename':artifact['filename'],'sha256':artifact['sha256'],
        'download_url':'/api/v1/artifacts/'+str(aid)+'/download','internal_draft':True}


def page(ctx,runtime,did,aid,number):
    path,_,pages=checked(ctx,runtime,did,aid)
    if number<1 or number>pages:fail(404,'Esta página não existe no PDF.','PAGE_NOT_FOUND')
    binary=shutil.which('pdftoppm')
    if not binary:fail(503,'O visualizador não está disponível. Use o download do PDF.','PDF_RENDERER_UNAVAILABLE')
    with tempfile.TemporaryDirectory(prefix='irps-pdf-') as work:
        target=Path(work)/'page'
        try:
            subprocess.run([binary,'-f',str(number),'-l',str(number),'-singlefile','-scale-to','1400','-png',str(path),str(target)],
                check=True,capture_output=True,timeout=20)
            data=target.with_suffix('.png').read_bytes()
        except (OSError,subprocess.SubprocessError):fail(503,'Não foi possível abrir a página. Use o download autorizado.','PDF_RENDER_FAILED')
    if not data.startswith(b'\x89PNG'):fail(503,'A página não pôde ser exibida. Use o download do PDF.')
    return data
