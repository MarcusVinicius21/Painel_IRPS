import {useEffect,useState} from 'react';
import {useApi,useResource,post,quantity,api,businessDate} from '../api';
import type {Row} from '../api';
import {Panel,Field,Notice,DataTable,Action,Badge} from '../components/ui';
import {MetricGrid,ResourceStatus,workflowURL} from '../components/WorkflowUI';

const labels:Record<string,string>={suggestion:'Sugestão do consórcio',communication:'Comunicação com o município',manifestation:'Manifestação recebida',external_act:'Comprovante de ato externo'};
const states:Record<string,Record<string,string>>={suggestion:{proposed:'Proposta para revisão',reviewed:'Sugestão conferida'},communication:{prepared:'Preparada, sem envio comprovado',sent:'Enviada com comprovante',no_response:'Sem resposta registrada'},manifestation:{received:'Resposta recebida',in_review:'Em conferência',confirmed:'Confirmada com documento',adjusted_confirmed:'Ajustada e confirmada',not_participating:'Não participa, com declaração',invalid:'Manifestação inválida'},external_act:{evidence_recorded:'Comprovante registrado para acompanhamento'}};
const display:Record<string,string>={communication_pending:'Comunicação pendente',awaiting_response:'Aguardando manifestação',overdue:'Sem manifestação no prazo',received:'Resposta recebida',in_review:'Em conferência',confirmed:'Confirmada',adjusted_confirmed:'Ajustada e confirmada',not_participating:'Não participa',invalid:'Manifestação inválida',requires_reconfirmation:'Exige nova conferência'};
const emptyForm=()=>({quantity:'',note:'',document_id:'',event_date:businessDate(),channel:'',protocol:'',responsible_name:'',competence_evidence:'',external_act:'publicidade',deadline:''});

export function IRPRegister({study,view='manifestations',draftCount=null}:{study:Row;view?:'suggestions'|'manifestations'|'consolidation';draftCount?:number|null}){
 const c=useApi(),result=useResource('/director/studies/'+study.id+'/register'),docs=useResource('/documents');
 const [kind,setKind]=useState(view==='suggestions'?'suggestion':'manifestation'),[city,setCity]=useState(study.payload.municipalities[0]),[status,setStatus]=useState(view==='suggestions'?'proposed':'received'),[form,setForm]=useState<Row>(emptyForm),[q,setQ]=useState(''),[filter,setFilter]=useState('');
 const [editorOpen,setEditorOpen]=useState(view==='suggestions');
 const [artifact,setArtifact]=useState<Row|null>(null),[reviewNote,setReviewNote]=useState(''),[reviewConfirmed,setReviewConfirmed]=useState(false),[upload,setUpload]=useState<File|null>(null);
 const data=result.data,previous=data?.operations.find((r:Row)=>r.kind===kind&&r.municipality_ibge===city);
 useEffect(()=>{setForm({...emptyForm(),...previous?.payload,quantity:previous?.payload.quantity??'',document_id:previous?.payload.document_id||'',deadline:previous?.payload.deadline||'',event_date:previous?.payload.event_date||businessDate()});setStatus(previous?.payload.status||Object.keys(states[kind])[0]);setReviewConfirmed(false);setReviewNote('');},[kind,city,previous?.id]);
 const set=(key:string,value:string)=>setForm(old=>({...old,[key]:value}));
 const save=()=>void c.run(async()=>{await post('/director/studies/'+study.id+'/operations',{
  kind,municipality_ibge:city,status,expected_revision:previous?.revision||0,scenario_revision:data?.scenario_revision,
  quantity:form.quantity===''?null:form.quantity,document_id:form.document_id||null,event_date:form.event_date||null,deadline:form.deadline||null,
  channel:form.channel,protocol:form.protocol,responsible_name:form.responsible_name,competence_evidence:form.competence_evidence,note:form.note,external_act:kind==='external_act'?form.external_act:null,
 });setArtifact(null);},'Registro salvo com versão e responsável. Confira o consolidado e suas pendências.');
 const selectedDocument=docs.data?.records.find((d:Row)=>d.id===form.document_id);
 const visible=data?.municipalities.filter((r:Row)=>(!filter||r.display_state===filter)&&(!q||(c.cities.find(x=>x.ibge===r.ibge)?.name||r.ibge).toLocaleLowerCase('pt-BR').includes(q.toLocaleLowerCase('pt-BR'))))||[];
 const name=(ibge:string)=>{const city=c.cities.find(x=>x.ibge===ibge);return city?city.name+'/'+city.uf:ibge;};
 const municipal=data?.municipalities.find((r:Row)=>r.ibge===city);
 const history=data?.history.filter((r:Row)=>r.municipality_ibge===city)||[];
 const exportFile=(fmt:string)=>void c.run(async()=>setArtifact(await post('/director/studies/'+study.id+(fmt==='zip'?'/dossier':'/consolidation/'+fmt))),'Relatório interno preparado. Confira a versão e as pendências.');
 return <div className="irp-register" data-view={view}>
  <ResourceStatus resource={result} label="as manifestações"/>
  {data?<>
   {view==='consolidation'?<section className={'consolidation-banner '+(data.all_invitations_resolved?'resolved':'')}><Badge tone={data.all_invitations_resolved?'':'amber'}>{data.all_invitations_resolved?'Respostas conferidas no escopo':'Consolidação parcial'}</Badge><h2>{data.all_invitations_resolved?'Confira o quadro e os documentos de suporte':'Ainda há municípios com resposta ou conferência pendente'}</h2><p>Somente manifestações válidas entram nos quantitativos. O relatório não autoriza publicação ou contratação.</p></section>:null}
   {view!=='suggestions'?<MetricGrid items={view==='manifestations'?[
    {label:'Municípios confirmados',value:data.municipalities.filter((r:Row)=>r.confirmation_current&&r.manifestation_state==='confirmed').length},
    {label:'Municípios ajustados e confirmados',value:data.municipalities.filter((r:Row)=>r.confirmation_current&&r.manifestation_state==='adjusted_confirmed').length},
    {label:'Pendentes de resposta ou conferência',value:data.pending_municipalities},
    {label:'Não participação documentada',value:data.non_participating_municipalities},
    {label:'Total de municípios do estudo',value:data.municipalities.length}
   ]:[
    {label:'Municípios com confirmação atual',value:data.confirmed_municipalities},
    {label:data.consolidated_total==null?'Quantidade confirmada conhecida':'Quantidade consolidada',value:data.confirmed_known_total,detail:study.payload.unit+(data.consolidated_total==null?' · parcial':' · escopo resolvido')},
    {label:'Valor estimado fundamentado',value:null,detail:'Exige preços e quantidades comparáveis'},
    {label:'Versões de minuta neste recorte',value:draftCount},
    {label:'Municípios com pendências',value:data.pending_municipalities}
   ]}/>:null}
   {!data.context_current?<Notice tone="warning">O cenário mudou. As confirmações anteriores exigem nova conferência e não integram o consolidado atual.</Notice>:null}
   <div className={view==='consolidation'?'consolidation-layout':'manifestation-layout'}>
    {view!=='suggestions'?<Panel title={view==='consolidation'?'Consolidação por município e item':'Manifestações dos municípios'}>
     <div className="register-filters"><Field label="Buscar município"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Nome do município…"/></Field><Field label="Situação da manifestação"><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="">Todas</option>{Object.entries(display).map(([k,l])=><option key={k} value={k}>{l}</option>)}</select></Field></div>
     <DataTable<Row> rows={visible} id={r=>r.ibge} pageSize={10} caption="Sugestões e confirmações documentadas por município" columns={[
      {label:'Município',render:r=><><strong>{name(r.ibge)}</strong><small>IBGE {r.ibge}</small></>},
      {label:'Sugestão conferida',render:r=><>{quantity(r.suggested_quantity)}<small>{r.unit} · {states.suggestion[r.suggestion_state]||'Ainda não proposta'}</small></>},
      {label:'Quantidade confirmada',render:r=><>{quantity(r.confirmed_quantity)}<small>{r.unit} · {states.manifestation[r.manifestation_state]||'Manifestação não recebida'}</small></>},
      {label:'Situação',render:r=><Badge tone={r.confirmation_current?'':r.non_participation_current?'':'amber'}>{display[r.display_state]}</Badge>},
      {label:'Documento recebido',render:r=>r.manifestation?.payload.document_id?<a href={'/api/v1/documents/'+r.manifestation.payload.document_id+'/original'}>Abrir comprovante</a>:'Ainda não recebido'},
      {label:'Conferência',render:r=><button className="text-button" onClick={()=>setCity(r.ibge)}>Conferir {name(r.ibge)}</button>} ]}/>
     <Notice>Silêncio não significa recusa. Histórico, meta e necessidade V4 não confirmam participação.</Notice>
    </Panel>:null}
    <aside className="municipal-detail">{view==='consolidation'?<Panel title="Próximos passos"><ol className="next-steps"><li>Revise as manifestações pendentes.</li><li>Confira os documentos e as quantidades.</li><li>Exporte o quadro e o dossiê.</li><li>Protocolo e publicação usam canais oficiais externos.</li></ol><a className="button secondary" href={workflowURL('manifestacoes',study.id)}>Abrir pendências</a></Panel>:null}
     <Panel title={view==='consolidation'?'Ações e documentos finais':name(city)} action={<Badge tone={data.municipalities.find((r:Row)=>r.ibge===city)?.confirmation_current?'':'amber'}>{display[data.municipalities.find((r:Row)=>r.ibge===city)?.display_state]||'Em acompanhamento'}</Badge>}>
      {view==='consolidation'?<><details><summary>Ver contexto e totais</summary><h3>{study.payload.name}</h3><p>Unidade: {study.payload.unit}. Versão do cenário: {data.scenario_revision}.</p><p>Total consolidado: <strong>{quantity(data.consolidated_total)} {study.payload.unit}</strong>.</p><p className="subtle">Sem confirmação completa, o total conhecido permanece parcial. Recusas documentadas não adicionam quantidades.</p></details><div className="export-actions">{[['xlsx','Exportar consolidado Excel'],['pdf','Gerar relatório PDF'],['zip','Preparar dossiê ZIP']].map(([fmt,label])=><button key={fmt} className="button secondary" disabled={c.busy||!c.can('export')} onClick={()=>exportFile(fmt)}>{label}</button>)}</div><a className="button secondary" href={workflowURL('manifestacoes',study.id)}>Revisar manifestações</a><Notice>Assinatura, protocolo e publicação exigem os canais oficiais competentes.</Notice></>:null}
      {view==='manifestations'?<section className="manifest-summary"><h3>Informações da manifestação</h3><dl><div><dt>Quantidade sugerida</dt><dd>{quantity(municipal?.suggested_quantity)} {study.payload.unit}</dd></div><div><dt>Quantidade confirmada</dt><dd>{quantity(municipal?.confirmed_quantity)} {study.payload.unit}</dd></div><div><dt>Situação</dt><dd>{display[municipal?.display_state]||'Em acompanhamento'}</dd></div><div><dt>Data da manifestação</dt><dd>{municipal?.manifestation?.payload.event_date||'Não informada'}</dd></div><div><dt>Responsável identificado</dt><dd>{municipal?.manifestation?.payload.responsible_name||'Ainda não informado'}</dd></div></dl><h3>Documentos recebidos</h3>{municipal?.manifestation?.payload.document_id?<a className="button secondary" href={'/api/v1/documents/'+municipal.manifestation.payload.document_id+'/original'}>Abrir manifestação original</a>:<p>Documento ainda não recebido.</p>}<Notice>Confirmação exige documento, conferência e competência comprovada.</Notice></section>:null}
      {view!=='consolidation'&&c.can('scenario.write')?<details className="municipal-editor" open={editorOpen} onToggle={e=>setEditorOpen(e.currentTarget.open)}><summary>{view==='suggestions'?'Registrar sugestão auditável':'Editar manifestação e comprovantes'}</summary>
       <Field label="Tipo de registro"><select value={kind} onChange={e=>setKind(e.target.value)}>{Object.entries(labels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></Field>
       <Field label="Município do registro"><select value={city} onChange={e=>setCity(e.target.value)}>{study.payload.municipalities.map((code:string)=><option key={code} value={code}>{name(code)}</option>)}</select></Field>
       <Field label="Situação do registro"><select value={status} onChange={e=>setStatus(e.target.value)}>{Object.entries(states[kind]).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></Field>
       {['suggestion','manifestation'].includes(kind)?<Field label="Quantidade do registro" hint={'Unidade: '+study.payload.unit+'. Não altera o V4.'}><input type="number" min="0" step="any" value={form.quantity} onChange={e=>set('quantity',e.target.value)}/></Field>:null}
       <Field label="Documento recebido ou comprovante"><select value={form.document_id} onChange={e=>{set('document_id',e.target.value);setReviewConfirmed(false);}}><option value="">Selecione um documento preservado</option>{docs.data?.records.filter((r:Row)=>r.classification!=='business_private'&&(r.classification==='synthetic')===(study.scenario?.classification==='synthetic')).map((r:Row)=><option key={r.id} value={r.id}>{r.filename} · versão {r.revision}</option>)}</select></Field>
       <ResourceStatus resource={docs} label="os documentos"/>
       <details><summary>Anexar comprovante ao IRPS</summary><Field label="Arquivo recebido"><input type="file" accept=".pdf,.docx,.xlsx,.csv" onChange={e=>setUpload(e.target.files?.[0]||null)}/></Field><button className="button secondary" disabled={!upload||c.busy||!c.can('document.write')} onClick={()=>void c.run(async()=>{const body=new FormData();body.append('file',upload!);body.append('classification',study.scenario.classification==='synthetic'?'synthetic':'internal');const d=await api('/documents',{method:'POST',body});set('document_id',d.id);setUpload(null);},'Documento preservado. Confira o conteúdo antes de confirmar a manifestação.')}>Preservar documento recebido</button></details>
       {selectedDocument?<details><summary>Conferir documento selecionado</summary><a href={'/api/v1/documents/'+selectedDocument.id+'/original'} target="_blank" rel="noreferrer">Abrir original para leitura</a><p>Versão {selectedDocument.revision} · {selectedDocument.review_state==='reviewed'?'Conferido':'Conferência pendente'}.</p><Field label="Parecer sobre o documento"><textarea value={reviewNote} onChange={e=>setReviewNote(e.target.value)}/></Field><label className="checkbox-row"><input type="checkbox" checked={reviewConfirmed} onChange={e=>setReviewConfirmed(e.target.checked)}/>Li o documento e conferi os dados recebidos.</label><button className="button secondary" disabled={c.busy||!c.can('document.review')||!reviewConfirmed||reviewNote.length<10} onClick={()=>void c.run(async()=>{await post('/documents/'+selectedDocument.id+'/review',{revision:selectedDocument.revision,decision:'reviewed',note:reviewNote,corrections:{}});setReviewConfirmed(false);},'Conferência documental registrada. A competência e a quantidade ainda exigem conferência.')}>Registrar conferência documental</button></details>:null}
       <div className="form-grid"><Field label="Data do recebimento ou do ato"><input type="date" value={form.event_date} max={businessDate()} onChange={e=>set('event_date',e.target.value)}/></Field><Field label="Prazo para resposta"><input type="date" value={form.deadline} onChange={e=>set('deadline',e.target.value)}/></Field></div>
       <Field label="Canal formal"><input value={form.channel} onChange={e=>set('channel',e.target.value)}/></Field><Field label="Protocolo"><input value={form.protocol} onChange={e=>set('protocol',e.target.value)}/></Field>
       {kind==='manifestation'?<><Field label="Responsável identificado no documento"><input value={form.responsible_name} onChange={e=>set('responsible_name',e.target.value)}/></Field><Field label="Como a competência foi conferida?"><textarea value={form.competence_evidence} onChange={e=>set('competence_evidence',e.target.value)}/></Field></>:null}
       {kind==='external_act'?<Field label="Ato realizado em outro ambiente"><select value={form.external_act} onChange={e=>set('external_act',e.target.value)}>{Object.entries({publicidade:'Publicidade',assinatura:'Assinatura',edital:'Edital',resultado:'Resultado',ata:'Ata'}).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></Field>:null}
       <Field label="Justificativa e observações da conferência"><textarea value={form.note} onChange={e=>set('note',e.target.value)}/></Field><p className="subtle">Registro versão {previous?.revision||0}. As versões anteriores serão preservadas.</p>
       <button className="button" disabled={c.busy||!data.context_current||form.note.length<10||!c.can('document.write')} onClick={save}>Salvar registro interno</button>
      </details>:null}
     </Panel>
     <Panel title="Histórico e documentos"><Action to="documentos" secondary>Conferir documentos</Action><ul className="executive-list">{history.map((h:Row)=><li key={h.id}><span>{labels[h.kind]} · versão {h.revision}<small>{new Date(h.created_at).toLocaleString('pt-BR')} · {states[h.kind][h.payload.status]}</small></span></li>)}</ul>{data.history_truncated?<p>Exibindo as 500 operações mais recentes. O resumo usa os registros vigentes.</p>:null}</Panel>
    </aside>
   </div>
   {artifact?<a className="button" href={artifact.download_url}>Baixar {artifact.filename}</a>:null}
   {view!=='consolidation'?<button className="text-button" disabled={c.busy||!c.can('export')} onClick={()=>exportFile('zip')}>Preparar dossiê ZIP</button>:null}
  </>:null}
 </div>;
}
