import {CheckCircle2,AlertCircle,Package,Users,Clock} from 'lucide-react';
import type {ReactNode} from 'react';
import type {Row} from '../api';
import {quantity} from '../api';
import {Panel,Notice,Badge} from './ui';
import {workflowURL} from './WorkflowUI';
import './preparation.css';
export function DraftChecklist({draft,study,versions,onOpen,reviewContent}:{draft:Row|null;study:Row;versions:Row[];onOpen:(id:string)=>void;reviewContent?:ReactNode}){
 const go=(id:string)=>{const el=document.getElementById(id);const details=el?.closest('details');if(details)details.open=true;el?.scrollIntoView({block:'center',behavior:'instant'});el?.focus();};
 const errors:string[]=draft?.validation.errors||[],pending:string[]=draft?.validation.pending||[];
 return <Panel title="Validação da IRP" action={<Badge tone="amber">{draft?`${errors.length} bloqueios · ${pending.length} pendências`:'Prévia pendente'}</Badge>} className="draft-checklist"><p>Confira os dados e as pendências antes de gerar os arquivos.</p><div className="draft-checks">
 <div><span className="draft-check-icon" aria-hidden="true">{draft?.payload.request.coherence_confirmed&&!errors.length?<CheckCircle2 size={17}/>:<AlertCircle size={17}/>}</span><strong>Conferência do objeto</strong><Badge tone={draft?.payload.request.coherence_confirmed&&!errors.length?'':'amber'}>{draft?errors.length?'Revisar':'Conferência registrada':'Pendente'}</Badge><small>A conferência humana não representa aprovação jurídica.</small></div>
 <div><Package className="draft-check-icon" aria-hidden="true" size={17}/><strong>Unidade de quantidade</strong><Badge>{study.payload.unit||'Não informada'}</Badge><small>Item e versão preservados no estudo.</small></div>
 <div><Users className="draft-check-icon" aria-hidden="true" size={17}/><strong>Municípios do estudo</strong><Badge>{study.payload.municipalities.length}</Badge><small>Inclusão no estudo não confirma participação.</small></div>
 <div><Clock className="draft-check-icon" aria-hidden="true" size={17}/><strong>Campos pendentes</strong><Badge tone="amber">{draft?pending.length:'A conferir'}</Badge><small>{draft?'Pendências informadas na validação da minuta.':'Prepare a prévia para conferir as pendências.'}</small></div>
 <div><AlertCircle className="draft-check-icon" aria-hidden="true" size={17}/><strong>Inconsistências detectadas</strong><Badge tone={errors.length?'amber':''}>{draft?errors.length:'A conferir'}</Badge></div>
 </div>
 {draft?.stale?<Notice tone="warning">Esta versão ficou desatualizada. Refaça a minuta com o estudo atual.</Notice>:null}
 <details open={errors.length>0}><summary>Ver detalhes das validações</summary>{errors.map(t=><div className="draft-issue" key={t}><p>{t}</p><button className="text-button" onClick={()=>go(/município/i.test(t)?'irp-municipality':/conferência|especificação/i.test(t)?'irp-coherence':'irp-object')}>Conferir campo</button></div>)}{pending.map(t=><div className="draft-issue" key={t}><p>{t}</p>{/Número|Prazo|Locais/.test(t)?<button className="text-button" onClick={()=>go(/Número/.test(t)?'irp-procedure_reference':/Prazo/.test(t)?'irp-deadline':'irp-delivery')}>Conferir informação</button>:<small>Exige conferência responsável; não há aprovação automática.</small>}</div>)}</details>
 <section className="draft-summary"><h3>Resumo da minuta</h3><dl><div><dt>Objeto</dt><dd>{draft?.payload.request.object||study.payload.name}</dd></div><div><dt>Referência interna</dt><dd>{study.internal_reference}</dd></div><div><dt>Meta preliminar</dt><dd>{quantity(study.payload.preliminary_target)} {study.payload.unit}</dd></div><div><dt>Municípios do estudo</dt><dd>{study.payload.municipalities.length} · sem confirmação automática</dd></div><div><dt>Referência do procedimento</dt><dd>{draft?.payload.request.procedure_reference||'Não informada'}</dd></div><div><dt>Versão do cenário</dt><dd>{draft?.payload.scenario_revision||study.scenario_revision}</dd></div></dl><button className="button secondary" onClick={()=>go('irp-object')}>Editar informações</button><a className="button secondary" href={workflowURL('planejamento',study.id)}>Conferir planejamento</a></section>
 <Notice>Minuta interna. Assinatura, número oficial e publicação dependem dos canais competentes.</Notice>
 {versions.length?<details><summary>Versões documentais preservadas</summary>{versions.map(v=><p key={v.id}><button className="text-button" onClick={()=>onOpen(v.id)}>{v.request.kind} · {new Date(v.created_at).toLocaleString('pt-BR')} · {v.validation.errors.length?'Com bloqueios':'Para revisão'}</button></p>)}</details>:null}
 {reviewContent}
 </Panel>;
}
