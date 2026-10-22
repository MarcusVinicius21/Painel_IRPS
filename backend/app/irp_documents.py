"""Deterministic draft generation. Only structured reviewed fields enter the body.

The optional local letterhead is sanitized on configuration, never altered in place.
No reference body, signature, legal clause or municipal confirmation is copied.
"""
from copy import deepcopy
from pathlib import Path
import posixpath
import io,hashlib,zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from .security import fail
from .db import encoded,identifier
from . import director

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ET.register_namespace('w',W);ET.register_namespace('r',R)
def tag(name):return '{'+W+'}'+name


def sanitize_letterhead(source, target):
    """Keep institutional headers, footers and images; remove the original body and metadata."""
    from .documents import checked_zip
    raw=Path(source).read_bytes();z=checked_zip(raw)
    body=ET.fromstring(z.read('word/document.xml')).find(tag('body'))
    section=deepcopy(body.find(tag('sectPr')))
    document=ET.Element(tag('document'));new=ET.SubElement(document,tag('body'))
    if section is not None:new.append(section)
    keep={n:z.read(n) for n in z.namelist() if n.startswith(('word/header','word/footer','word/media/','word/theme/')) or n in ('word/styles.xml','word/fontTable.xml','word/numbering.xml','word/_rels/document.xml.rels') or n.startswith(('word/_rels/header','word/_rels/footer'))}
    # Contact details embedded in the supplied footer have not been validated.
    # The institutional header is retained; the derived footer is explicit and neutral.
    for name in list(keep):
        if name.startswith('word/footer') and name.endswith('.xml'):
            footer=ET.Element(tag('ftr'));p=ET.SubElement(footer,tag('p'));r=ET.SubElement(p,tag('r'))
            ET.SubElement(r,tag('t')).text='IRPS / CONSORMULTI | MINUTA EM REVISÃO | Página '
            field=ET.SubElement(p,tag('fldSimple'),{tag('instr'):'PAGE'});r=ET.SubElement(field,tag('r'));ET.SubElement(r,tag('t')).text='1'
            keep[name]=ET.tostring(footer,encoding='utf-8',xml_declaration=True)
    # The reference's own body-related relationships and inactive content are excluded.
    relns='{http://schemas.openxmlformats.org/package/2006/relationships}'
    ET.register_namespace('',relns[1:-1])
    for name,data in list(keep.items()):
        if name.endswith('.rels'):
            rels=ET.fromstring(data)
            for rel in list(rels):
                if name.startswith('word/_rels/footer') or rel.attrib.get('TargetMode')=='External' or not rel.attrib.get('Type','').rsplit('/',1)[-1] in ('header','footer','image','styles','fontTable','theme','numbering') or (name=='word/_rels/document.xml.rels' and rel.attrib.get('Type','').endswith('/image')):
                    rels.remove(rel)
            keep[name]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    referenced=set()
    for name,data in keep.items():
        if name.endswith('.rels'):
            for rel in ET.fromstring(data):
                relationship_target=rel.attrib.get('Target','')
                base=posixpath.dirname(posixpath.dirname(name))
                referenced.add(posixpath.normpath(posixpath.join(base,relationship_target)))
    for name in list(keep):
        if name.startswith('word/media/') and name not in referenced:del keep[name]
    keep['word/document.xml']=ET.tostring(document,encoding='utf-8',xml_declaration=True)
    keep['_rels/.rels']=f'<Relationships xmlns="{relns[1:-1]}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>'.encode()
    ct=ET.fromstring(z.read('[Content_Types].xml'))
    for node in list(ct):
        part=node.attrib.get('PartName')
        if part and part.lstrip('/') not in keep:ct.remove(node)
    ET.register_namespace('','http://schemas.openxmlformats.org/package/2006/content-types')
    keep['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as writer:
        for name,data in keep.items():writer.writestr(name,data)
    Path(target).parent.mkdir(parents=True,exist_ok=True);Path(target).write_bytes(output.getvalue())
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'derived_sha256':hashlib.sha256(output.getvalue()).hexdigest(),'original_preserved':True,
            'original_body_excluded':True,'unverified_contact_footer_excluded':True,'header_preserved':True}


TITLES={'procedimento':'Minuta do procedimento de intenção de registro de preços','formulario':'Minuta do formulário de manifestação de interesse',
        'planilha':'Planilha preliminar de itens e municípios','especificacoes':'Anexo de especificações para revisão',
        'municipios':'Quadro de municípios potencialmente convidados','quantitativos':'Quadro preliminar de quantitativos'}


def sections(draft):
    p=draft['payload'];s=p['study'];req=p['request'];validation=draft['validation']
    cities=p['municipalities']
    if req['kind']=='formulario':cities=[c for c in cities if c['ibge']==req['municipality_ibge']]
    rows=[];v4={r['ibge']:r for r in p['calculation_lines']};register={r['ibge']:r for r in p.get('register',{}).get('municipalities',[])}
    histories={r['municipality']['ibge']:r for r in (s.get('history') or {}).get('municipalities',[])}
    for city in cities:
        line=v4.get(city['ibge']);history=histories.get(city['ibge'])
        registered=register.get(city['ibge'],{})
        rows.append([city['name']+'/'+city['uf'],city['ibge'],str(history['observed_quantity']) if history and history['observed_quantity'] is not None else 'Não disponível',
                     str(line['quantity']) if line and line['quantity'] is not None else 'Dados insuficientes',
                     str(registered['suggested_quantity']) if registered.get('suggested_quantity') is not None else 'A revisar',
                     str(registered['confirmed_quantity']) if registered.get('confirmed_quantity') is not None else 'Não confirmada'])
    parts=[('title',TITLES[req['kind']]),('p',('DADOS FICTÍCIOS DE TESTE | ' if p['scenario_classification']=='synthetic' else '')+'MINUTA EM REVISÃO • Não publicada • Não assinada'),
        ('p','Documento preparatório. A geração não confirma a participação dos municípios e não autoriza contratação.'),
        ('h','Identificação do estudo'),('p',f"Referência informada: {req['procedure_reference'] or 'A definir pelo controle autorizado'}"),
        ('p',f"Cenário {p['scenario_id']} • versão {p['scenario_revision']} • estudo {draft['study_id']}"),
        ('h','Objeto'),('p',req['object']),('h','Item e especificação'),('p',s['name']),('p',s['specification']),
        ('p',f"Unidade de quantidade: {s['unit']} • versão técnica: {s['planning_item']['version']}"),
        ('p',f"Catálogo: {(s.get('catalogue_entry') or {}).get('kind','Objeto livre')} • código {s.get('code') or 'não catalogado'}"),
        ('p',f"Meta preliminar: {s['preliminary_target'] if s['preliminary_target'] is not None else 'Não informada'} {s['unit']}. Não distribuída entre municípios."),
        ('p',s['target_justification'] or 'Não há meta preliminar informada.')]
    if s.get('service_period'):
        parts += [('p','Período de prestação: '+s['service_period']),('p','O que uma unidade representa: '+s['quantity_basis'])]
    parts += [('h','Municípios e quantidades em estados distintos'),('table',{'headers':['Município','IBGE','Histórico observado','Necessidade V4','Sugestão IRP','Confirmação'], 'rows':rows}),
        ('p',f"Histórico da situação {s['phase']}, entre {s['start']} e {s['end']}. Quantidades documentadas não comprovam consumo nem necessidade futura."),
        ('p','Municípios listados são potenciais participantes selecionados para estudo. O vínculo consorcial e a competência precisam de validação documental.'),
        ('h','Condições a conferir'),('p','Prazo e canal: '+(req['deadline'] or 'A definir e validar.')),
        ('p','Entrega: '+(req['delivery'] or 'Locais e condições a confirmar.'))]
    if req['kind']=='formulario':
        parts += [('p','Órgão e CNPJ: ____________________'),('p','Unidade requisitante e responsável: ____________________'),
                  ('p','Quantidade formalmente solicitada e justificativa: ____________________'),('p','Local, período e fonte de recursos: ____________________'),
                  ('p','Autoridade competente e assinatura: campo a preencher pelo canal formal. Nenhuma assinatura foi gerada.')]
    if req['note']:parts += [('p',req['note'])]
    parts += [('h','Revisões e ações externas obrigatórias')]+[('p','• '+v) for v in validation['pending']]
    parts += [('p','As cláusulas jurídicas e a numeração oficial não foram criadas automaticamente. A versão final depende de validação institucional.'),
        ('h','Rastreabilidade'),('p','Contexto SHA-256: '+p['context_sha256']),('p','Modelo derivado: '+p['template_version']),
        ('p','Conferência técnica registrada: '+req['coherence_evidence'])]
    for city in histories.values():
        for evidence in city['evidence'][:10]:
            parts.append(('p',f"Fonte {evidence['provider']} • fato {evidence['fact_id']} • consulta {evidence['consulted_at']} • {evidence['url']}"))
    return parts


def docx_bytes(parts, template=None):
    files={}
    if template and Path(template).is_file():
        with zipfile.ZipFile(template) as z:files={n:z.read(n) for n in z.namelist()}
        root=ET.fromstring(files['word/document.xml']);body=root.find(tag('body'));section=deepcopy(body.find(tag('sectPr')))
        for child in list(body):body.remove(child)
    else:
        root=ET.Element(tag('document'));body=ET.SubElement(root,tag('body'));section=ET.Element(tag('sectPr'))
        ET.SubElement(section,tag('pgSz'),{tag('w'):'11906',tag('h'):'16838'})
        ET.SubElement(section,tag('pgMar'),{tag(k):'1000' for k in ('top','right','bottom','left')})
        files['[Content_Types].xml']=b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
        files['_rels/.rels']=f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>'.encode()
    def paragraph(parent,text,kind='p'):
        p=ET.SubElement(parent,tag('p'));props=ET.SubElement(p,tag('pPr'))
        if kind in ('title','h'):
            ET.SubElement(props,tag('pStyle'),{tag('val'):'Title' if kind=='title' else 'Heading1'});ET.SubElement(props,tag('keepNext'))
        ET.SubElement(props,tag('spacing'),{tag('after'):'60' if kind.startswith('cell') else '120'})
        r=ET.SubElement(p,tag('r'));rp=ET.SubElement(r,tag('rPr'))
        ET.SubElement(rp,tag('color'),{tag('val'):'000000'});ET.SubElement(rp,tag('rFonts'),{tag('ascii'):'Arial',tag('hAnsi'):'Arial'})
        ET.SubElement(rp,tag('sz'),{tag('val'):'32' if kind=='title' else '24' if kind=='h' else '18' if kind.startswith('cell') else '21'})
        if kind in ('title','h','cell_header'):ET.SubElement(rp,tag('b'))
        ET.SubElement(r,tag('t')).text=str(text)
    for kind,value in parts:
        if kind!='table':paragraph(body,value,kind);continue
        table=ET.SubElement(body,tag('tbl'));props=ET.SubElement(table,tag('tblPr'))
        ET.SubElement(props,tag('tblW'),{tag('w'):'0',tag('type'):'auto'})
        ET.SubElement(props,tag('tblLayout'),{tag('type'):'fixed'})
        borders=ET.SubElement(props,tag('tblBorders'))
        for side in ('top','left','bottom','right','insideH','insideV'):ET.SubElement(borders,tag(side),{tag('val'):'single',tag('sz'):'4',tag('color'):'D9D9D9'})
        grid=ET.SubElement(table,tag('tblGrid'))
        for width in (2000,1000,1600,1600,1500,1500):ET.SubElement(grid,tag('gridCol'),{tag('w'):str(width)})
        for idx,row in enumerate([value['headers']]+value['rows']):
            tr=ET.SubElement(table,tag('tr'));trpr=ET.SubElement(tr,tag('trPr'))
            if idx==0:ET.SubElement(trpr,tag('tblHeader'))
            for col,text in enumerate(row):
                cell=ET.SubElement(tr,tag('tc'));cp=ET.SubElement(cell,tag('tcPr'))
                ET.SubElement(cp,tag('tcW'),{tag('w'):str((2000,1000,1600,1600,1500,1500)[col]),tag('type'):'dxa'})
                paragraph(cell,text,'cell_header' if idx==0 else 'cell')
    if section is not None:body.append(section)
    files['word/document.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    # Normalize OPC relationships/content types through a maintained OOXML writer.
    # Zip/XML validity alone is insufficient for Word/LibreOffice interoperability.
    from docx import Document
    normalized=io.BytesIO();doc=Document(io.BytesIO(out.getvalue()))
    for name in ('Title','Heading 1'):
        if name in doc.styles:
            props=doc.styles[name].element.find(tag('pPr'))
            if props is not None:
                for border in list(props.findall(tag('pBdr'))):props.remove(border)
    doc.save(normalized)
    return normalized.getvalue()


def pdf_bytes(parts):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,CondPageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    out=io.BytesIO();styles=getSampleStyleSheet();styles['Title'].textColor=colors.black;styles['Heading2'].textColor=colors.black
    flow=[]
    for kind,value in parts:
        if kind=='table':
            rows=[[Paragraph(escape(str(c)),styles['BodyText']) for c in row] for row in [value['headers']]+value['rows']]
            table=Table(rows,colWidths=[110,65,85,90,80,90],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF2F2')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            flow += [table,Spacer(1,10)]
        else:
            if kind=='h':flow.append(CondPageBreak(80))
            flow.append(Paragraph(escape(str(value)),styles['Title' if kind=='title' else 'Heading2' if kind=='h' else 'BodyText']));flow.append(Spacer(1,6))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(35,24,'IRPS / CONSORMULTI • Minuta em revisão • Página '+str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,leftMargin=35,rightMargin=35,topMargin=40,bottomMargin=40).build(flow,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()


def export(ctx,runtime,did,fmt):
    ctx.require('export');row=director.draft(ctx,did)
    from . import scenarios
    scenarios.get_scenario(ctx,row['payload']['scenario_id'],lock=True)
    row=director.draft(ctx,did)
    if row['validation']['errors']:fail(422,'Corrija as incoerências indicadas na minuta antes de exportar.','IRP_BLOCKED')
    if row['stale']:fail(409,'O cenário mudou. Confira o estudo antes de gerar outra minuta.','VERSION_CONFLICT')
    from .draft_review import guard_export
    guard_export(ctx,did)
    parts=sections(row);template=Path(runtime)/'irp-letterhead.docx'
    data=docx_bytes(parts,template) if fmt=='docx' else pdf_bytes(parts)
    aid=identifier();key=f'exports/{ctx.org_id}/{aid}.{fmt}';path=Path(runtime)/key;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    filename=f'IRPS_minuta_{row["payload"]["request"]["kind"]}_v{row["payload"]["scenario_revision"]}.{fmt}'
    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document' if fmt=='docx' else 'application/pdf'
    sha=hashlib.sha256(data).hexdigest();p=row['payload']
    ctx.db.execute('INSERT INTO artifact(org_id,id,classification,storage_key,filename,media_type,sha256,scenario_id,revision,created_by) VALUES (:o,:i,:classification,:s,:f,:m,:h,:sid,:v,:a)',
        {'o':ctx.org_id,'i':aid,'classification':p['scenario_classification'],'s':key,'f':filename,'m':mime,'h':sha,'sid':p['scenario_id'],'v':p['scenario_revision'],'a':ctx.actor_id})
    ctx.audit('irp.draft_exported',did,{'artifact_id':aid,'format':fmt,'sha256':sha,'letterhead_applied':fmt=='docx' and template.is_file()})
    return {'id':aid,'filename':filename,'sha256':sha,'state':'needs_review','download_url':'/api/v1/artifacts/'+aid+'/download','letterhead_applied':fmt=='docx' and template.is_file()}


def dossier(ctx,runtime,sid):
    """Export only this organization's structured study and current derived drafts.

    Uploaded originals are listed by hash and ID; they are never silently repackaged.
    Commercial quotations and credentials are not queried.
    """
    ctx.require('export');ctx.require('document.read')
    from .irp_register import summary
    study=director.study(ctx,sid)
    from . import scenarios,draft_review
    scenarios.get_scenario(ctx,study['scenario_id'],lock=True)
    study=director.study(ctx,sid);register=summary(ctx,sid)
    candidates=ctx.db.all('''SELECT * FROM irp_draft WHERE org_id=:o AND study_id=:s
        ORDER BY created_at DESC,id DESC LIMIT 501''',{'o':ctx.org_id,'s':sid})
    if len(candidates)>500:fail(422,'Escolha um estudo com menos de 500 minutas para exportar o dossiê.')
    current={}
    for draft in candidates:
        p=draft['payload'];req=p['request'];key=(req['kind'],req.get('municipality_ibge') or '')
        if key not in current:current[key]=draft
    output=io.BytesIO();manifest=[];template=Path(runtime)/'irp-letterhead.docx'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('LEIA-ME.txt','Dossiê interno IRPS / CONSORMULTI\nMinutas em revisão. Não publica, assina ou homologa atos.\nOs originais recebidos ficam preservados no IRPS; este pacote lista suas referências.\nCustos comerciais privados não fazem parte deste dossiê.\n')
        z.writestr('estudo-e-evidencias.json',encoded(study));z.writestr('manifestacoes-e-sugestoes.json',encoded(register))
        # Current structured reports accompany the evidence, including explicit pending rows.
        from .irp_consolidation import export as consolidation
        for fmt in ('xlsx','pdf'):
            artifact=consolidation(ctx,runtime,sid,fmt)
            data=(Path(runtime)/'exports'/str(ctx.org_id)/(artifact['id']+'.'+fmt)).read_bytes()
            name='consolidacao/quadro-municipal-e-item.'+fmt;z.writestr(name,data)
            manifest.append({'file':name,'sha256':hashlib.sha256(data).hexdigest(),'state':'internal_partial' if register['consolidated_total'] is None else 'internal_review'})
        for (kind,city),draft in current.items():
            if draft_review.state(ctx,draft['id'])['export_blocked'] or draft['validation']['errors'] or not study['context_current'] or draft['payload']['scenario_revision']!=study['scenario']['current_revision'] or draft['payload'].get('register')!=register:
                manifest.append({'id':str(draft['id']),'kind':kind,'included':False,'reason':'Minuta bloqueada ou contexto alterado.'});continue
            name=f'minutas/{kind}'+('_'+city if city else '')
            for fmt,data in [('docx',docx_bytes(sections(draft),template)),('pdf',pdf_bytes(sections(draft)))]:
                filename=name+'.'+fmt;z.writestr(filename,data)
                manifest.append({'draft_id':str(draft['id']),'file':filename,'sha256':hashlib.sha256(data).hexdigest(),'state':'needs_review'})
        index={'study_id':sid,'scenario_revision':study['scenario']['current_revision'],'context_current':study['context_current'],
            'files':manifest,'original_documents_embedded':False,'private_quotations_included':False}
        z.writestr('indice.json',encoded(index))
    data=output.getvalue();aid=identifier();key=f'exports/{ctx.org_id}/{aid}.zip';path=Path(runtime)/key;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    filename='IRPS_dossie_interno_'+str(sid)+'.zip';sha=hashlib.sha256(data).hexdigest()
    ctx.db.execute('INSERT INTO artifact(org_id,id,classification,storage_key,filename,media_type,sha256,scenario_id,revision,created_by) VALUES (:o,:i,:classification,:s,:f,\'application/zip\',:h,:sid,:v,:a)',
        {'o':ctx.org_id,'i':aid,'classification':study['scenario']['classification'],'s':key,'f':filename,'h':sha,'sid':study['scenario_id'],'v':study['scenario']['current_revision'],'a':ctx.actor_id})
    ctx.audit('irp.dossier_exported',sid,{'artifact_id':aid,'sha256':sha,'original_documents_embedded':False})
    return {'id':aid,'filename':filename,'sha256':sha,'download_url':'/api/v1/artifacts/'+aid+'/download',
        'drafts_included':sum('draft_id' in f for f in manifest),'consolidation_reports_included':2,'manifest':index}


def consolidation_export(ctx,runtime,sid,fmt):
    from .irp_consolidation import export
    return export(ctx,runtime,sid,fmt)
