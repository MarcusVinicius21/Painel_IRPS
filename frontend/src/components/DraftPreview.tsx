import {useState,useRef} from 'react';
import {useApi,useResource,post} from '../api';
import type {Row} from '../api';
import {Panel,Notice,Empty,Badge} from './ui';
import {ResourceStatus} from './WorkflowUI';

export function DraftPreview({draft,artifact,onArtifact}:{draft:Row|null;artifact:Row|null;onArtifact:(r:Row)=>void}){
 const [zoom,setZoom]=useState(100),paper=useRef<HTMLDivElement>(null);
 const c=useApi(),preview=useResource(draft?'/irp-drafts/'+draft.id+'/preview':null);
 const kinds:Record<string,string>={procedimento:'Procedimento de IRP',formulario:'Formulário municipal',planilha:'Planilha de itens e municípios',especificacoes:'Anexo de especificações',municipios:'Municípios potencialmente convidados',quantitativos:'Quadro de quantitativos'};
 return <Panel title="Visualização do documento" className="document-preview-panel"><div className="preview-toolbar" aria-label="Controles da prévia"><button className="icon-button" aria-label="Diminuir zoom da prévia" title={!draft?'Prepare uma prévia para alterar o zoom':undefined} disabled={!draft||zoom<=75} onClick={()=>setZoom(z=>z-25)}>−</button><output aria-live="polite">{zoom}%</output><button className="icon-button" aria-label="Aumentar zoom da prévia" title={!draft?'Prepare uma prévia para alterar o zoom':undefined} disabled={!draft||zoom>=150} onClick={()=>setZoom(z=>z+25)}>+</button><button className="button secondary" onClick={()=>void paper.current?.requestFullscreen()}>Tela cheia</button><span>Paginação no PDF</span></div><ResourceStatus resource={preview} label="a prévia"/>{draft?<>
  <h3>Prévia · {kinds[draft.payload.request.kind]}</h3><Badge tone="amber">Minuta em revisão</Badge>
  {draft.stale||preview.data?.stale?<Notice tone="warning">O cenário ou os registros mudaram. Prepare uma nova prévia antes de exportar.</Notice>:null}
  {draft.validation.errors.map((t:string)=><Notice key={t} tone="warning">{t}</Notice>)}
  {preview.data?<div className="document-paper" ref={paper}><div style={{zoom:zoom/100}}><div className="paper-identity"><span className="approved-brand" role="img" aria-label="CONSORMULTI"/></div>{preview.data.sections.map(([kind,value]:[string,any],i:number)=>kind==='title'?<h3 key={i}>{value}</h3>:kind==='h'?<h4 key={i}>{value}</h4>:kind==='table'?<div key={i} className="paper-table-scroll" role="region" aria-label="Quantitativos da minuta" tabIndex={0}><table><caption className="sr-only">Quantidades e origens preservadas na minuta</caption><thead><tr>{value.headers.map((v:string,j:number)=><th scope="col" key={j}>{v}</th>)}</tr></thead><tbody>{value.rows.map((r:string[],j:number)=><tr key={j}>{r.map((v,k)=><td key={k}>{v}</td>)}</tr>)}</tbody></table></div>:<p key={i}>{value}</p>)}</div></div>:null}
  <div className="actions">{['docx','pdf'].map(fmt=><button key={fmt} className="button secondary" disabled={c.busy||!c.can('export')||draft.stale||preview.data?.stale||draft.validation.errors.length>0} onClick={()=>void c.run(async()=>onArtifact(await post('/irp-drafts/'+draft.id+'/exports/'+fmt)),'Arquivo de minuta gerado para revisão.')}>Gerar {fmt.toUpperCase()}</button>)}</div>
  {artifact?<a className="button" href={artifact.download_url}>Baixar {artifact.filename}</a>:null}
  <p className="subtle">Prévia do conteúdo gerado. A paginação final está no arquivo exportado.</p>
 </>:<div className="document-paper blank-paper" ref={paper}><div className="paper-identity"><span className="approved-brand" role="img" aria-label="CONSORMULTI"/></div><Empty title="Prepare a prévia da minuta" description="Confira o objeto, o modelo e a unidade no formulário ao lado."/></div>}</Panel>;
}
