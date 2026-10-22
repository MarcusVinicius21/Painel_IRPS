import {useEffect,useState} from 'react';
import {useApi,useResource,post,route,nav,quantity,phases} from '../api';
import type {Row} from '../api';
import {Page,Panel,Field,Notice,DataTable,Action} from '../components/ui';
import {SelectedItem,WorkflowNav,MetricGrid} from '../components/WorkflowUI';
import {PlanningMethods} from '../components/PlanningMethods';
import {MunicipalMatrix} from '../components/MunicipalMatrix';
import {readHistoryFilters} from '../historyIndicators';
import './multi-study.css';

export function MultiStudyPlanning(){
 const c=useApi(),r=route(),id=r.params.get('multi'),saved=!!id&&id!=='novo';
 const group=useResource(saved?'/director/multi-studies/'+id:null),list=useResource('/director/multi-studies'),sources=useResource('/director/studies');
 const [name,setName]=useState('Planejamento com vários itens'),[target,setTarget]=useState(''),[ids,setIds]=useState<string[]>([]),[reason,setReason]=useState(''),[editing,setEditing]=useState(!saved);
 useEffect(()=>{if(!group.data)return;setName(group.data.payload.name);setTarget(group.data.scenario_id);setIds(group.data.payload.items.map((i:Row)=>i.source_study_id));setEditing(false);},[group.data?.id,group.data?.revision]);
 const entries:Row[]=group.data?.payload.items||[],options:Row[]=[...(sources.data?.records||[]),...entries.filter(i=>!sources.data?.records.some((s:Row)=>s.id===i.source_study_id)).map(i=>({id:i.source_study_id,name:i.name}))],active=entries.find(i=>i.source_study_id===r.params.get('origem'))||entries[0];
 const source=useResource(active?'/director/studies/'+active.source_study_id:null),p=source.data?.id===active?.source_study_id?source.data?.payload:null;
 useEffect(()=>{if(target&&c.scenario?.id!==target)void c.select(target).catch(e=>c.setToast(e.message));},[target,c.scenario?.id]);
 const sc=c.scenario?.id===target?c.scenario:null,calc=c.calculation?.scenario_id===target&&c.calculation?.revision===sc?.current_revision?c.calculation:null;
 const params=new URLSearchParams({item_id:active?.planning_item.id||'',item_version:String(active?.planning_item.version||1)});
 (active?.municipalities||[]).forEach((v:string)=>params.append('municipalities',v));
 const lines=useResource(calc&&active?'/calculations/'+calc.id+'/item-lines?'+params:null);
 const choose=(value:string)=>{const query=new URLSearchParams(r.params);query.set('origem',value);location.hash='/inteligencia?'+query;};
 const save=()=>void c.run(async()=>{const body={contract_version:1,request_id:crypto.randomUUID(),name,scenario_id:target,scenario_revision:sc?.current_revision,source_studies:ids,justification:reason,...(saved?{expected_revision:group.data!.revision}:{})};const result=await post('/director/multi-studies'+(saved?'/'+id+'/revisions':''),body);nav('inteligencia',{multi:result.id,origem:result.payload.items[0].source_study_id});},'Estudo conjunto salvo. As quantidades continuam separadas por item.');
 const rows:Row[]=(active?.municipalities||[]).map((ibge:string)=>p?.history?.municipalities.find((v:Row)=>v.municipality.ibge===ibge)||{municipality:c.cities.find(v=>v.ibge===ibge)||{ibge,name:ibge,uf:''},observed_records:null,temporal_windows:[],evidence:[]});
 const context={phase:p?.phase||active?.history_scope.phase||'',start:p?.start||active?.history_scope.start||'',end:p?.end||active?.history_scope.end||'',filters:readHistoryFilters(p?.history_filters||active?.history_scope.history_filters),pending:source.loading,classification:group.data?.payload.classification};
 return <div className="director-workflow stage-planejamento multi-study"><Page title="Planejamento de compras municipais" description="Reúna itens sem misturar unidades, histórico ou metas." actions={<Action to="inteligencia" secondary>Voltar à inteligência</Action>}>
 <WorkflowNav stage="planejamento" selected study={null}/>
 {group.error||sources.error||list.error?<Notice tone="warning">Não foi possível consultar os estudos. {group.error||sources.error||list.error}</Notice>:null}
 {group.loading?<p role="status">Abrindo o estudo com vários itens…</p>:null}
 {group.data?.payload.classification==='synthetic'?<p className="dataset-warning">Demonstração fictícia · sem necessidade ou confirmação oficial.</p>:null}
 <details className="multi-setup" open={editing} onToggle={e=>setEditing(e.currentTarget.open)}><summary>{saved?'Rever os itens e a versão vinculada':'Reunir estudos salvos'}</summary>
 <Panel title="Escolha os estudos e o cenário existente"><div className="form-grid"><Field label="Nome do estudo conjunto"><input value={name} onChange={e=>setName(e.target.value)}/></Field><Field label="Cenário V4 com estes itens"><select value={target} onChange={e=>setTarget(e.target.value)}><option value="">Escolha o cenário</option>{target&&!c.scenarios.some(s=>s.id===target)?<option value={target}>{sc?.title||'Cenário vinculado ao estudo'}</option>:null}{c.scenarios.map(s=><option key={s.id} value={s.id} disabled={saved&&s.id!==group.data?.scenario_id}>{s.title} · versão {s.current_revision}</option>)}</select></Field></div>
 <div className="multi-source-options">{options.map((s:Row)=><label key={s.id}><input type="checkbox" checked={ids.includes(s.id)} onChange={e=>setIds(v=>e.target.checked?[...v,s.id]:v.filter(x=>x!==s.id))}/>{s.name}</label>)}</div>
 {!sources.loading&&!sources.data?.records.length?<Notice>Salve um estudo por item na inteligência antes de reunir os itens.</Notice>:null}
 <Field label="Justificativa do vínculo ou da revisão"><textarea value={reason} onChange={e=>setReason(e.target.value)}/></Field><Notice>O cenário deve conter exatamente os itens e municípios escolhidos. Ajuste essa seleção no módulo V4 existente. Não alteramos nem distribuímos quantidades ao reunir estudos.</Notice>
 <button className="button" disabled={c.busy||(saved&&!group.data)||!sc||!ids.length||name.trim().length<5||reason.trim().length<10||!c.can('scenario.write')} onClick={save}>Salvar estudo conjunto</button>
 </Panel></details>
 {!saved?<Panel title="Retomar estudo conjunto">{list.data?.records.map((g:Row)=><p key={g.id}><a href={'#/inteligencia?multi='+g.id}>{g.name} · versão {g.revision}</a></p>)}{!list.loading&&!list.data?.records.length?<Notice>Nenhum estudo conjunto salvo neste espaço.</Notice>:null}</Panel>:null}
 {group.data&&active?<>
 {!group.data.context_current?<Notice tone="warning">O cenário ou um estudo de origem mudou. Confira os itens e salve uma nova revisão antes de continuar.</Notice>:null}
 <div className="method-options"><SelectedItem item={active.catalogue_entry||{name:active.name,kind:'Objeto livre'}} unit={active.unit} selection technical/><PlanningMethods key={group.data.id+':'+sc?.snapshot.mode} mode={sc?.snapshot.mode} blocked={!sc||!group.data.context_current||c.busy} open={mode=>{if(sc)nav(mode==='A'?'quantidades':'distribuicao',{multi:group.data!.id,origem:active.source_study_id,item:active.planning_item.id});}}/></div>
 <section className="planning-parameters"><div><h2>Item e recorte do planejamento</h2><Field label="Item do estudo conjunto"><select value={active.source_study_id} onChange={e=>choose(e.target.value)}>{entries.map(i=><option key={i.source_study_id} value={i.source_study_id}>{i.name} · {i.unit}</option>)}</select></Field><p>{phases[context.phase]||context.phase} · {context.start} a {context.end} · fonte: {context.filters?.provider||'Todas as fontes do estudo'}</p></div><Notice>Meta deste item: {quantity(active.preliminary_target)} {active.unit}. Metas de itens diferentes não são somadas.</Notice></section>
 <Panel title="Planejamento de quantitativos por município" className="municipal-history-panel">{source.loading?<p role="status">Abrindo o histórico deste item…</p>:source.error?<Notice tone="warning">Não foi possível consultar o item. {source.error}</Notice>:<MunicipalMatrix key={active.source_study_id} rows={rows} planning unit={active.unit} context={context} register={null} v4={{...lines,data:lines.data?{...lines.data,records:lines.data.records.filter((line:Row)=>line.item_id===active.planning_item.id&&line.item_version===active.planning_item.version)}:null}}/>}<p className="subtle">Sugestões e manifestações das origens não são transferidas para o conjunto.</p></Panel>
 <section className="planning-summary"><Panel title="Resumo do item selecionado"><MetricGrid items={[{label:'Meta preliminar deste item',value:active.preliminary_target,detail:active.unit},{label:'Municípios deste item',value:active.municipalities.length},{label:'Quantidade confirmada no conjunto',value:null,detail:'Não transportada dos estudos de origem'}]}/></Panel><div className="planning-summary-action"><button className="button" disabled title="O gerador atual prepara uma minuta por item">Minuta conjunta indisponível</button><small>O gerador atual trabalha por item. Confira cada origem antes de preparar sua minuta.</small>{group.data.context_current?<a className="button secondary" href={'#/inteligencia?estudo='+active.source_study_id+'&etapa=preparacao&retorno_multi='+group.data.id}>Preparar minuta deste item</a>:null}</div></section>
 <p className="multi-quantity-rule">Quantidades e totais permanecem separados por item e unidade. Não existe soma geral de quantidades diferentes.</p><details><summary>Itens, unidades e metas preservadas</summary><DataTable<Row> rows={entries} id={i=>i.source_study_id} caption="Itens do estudo conjunto" columns={[{label:'Item',render:i=>i.name},{label:'Unidade',render:i=>i.unit},{label:'Meta preliminar',render:i=>quantity(i.preliminary_target)},{label:'Municípios',render:i=>i.municipalities.length},{label:'Histórico',render:i=>i.history_scope.start+' a '+i.history_scope.end}]}/></details>
 </>:null}
 </Page></div>;
}
