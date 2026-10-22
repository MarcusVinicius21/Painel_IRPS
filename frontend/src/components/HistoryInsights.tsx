import {useState} from 'react';
import {Building2,Layers3,CalendarDays,PackageCheck} from 'lucide-react';
import type {Row} from '../api';
import {phases} from '../api';
import {historyInsights} from '../historyInsights';
import {providerLabel,readHistoryFilters} from '../historyIndicators';
import {Panel,Action,Dialog,IconProps} from './ui';

export function HistoryInsights({history,studyId,planningSuffix='',demonstration=false}:{history:Row|null|undefined;studyId:string;planningSuffix?:string;demonstration?:boolean}){
 const [inspect,setInspect]=useState(false),insights=historyInsights(history);
 const s=history?.contract_version===2?history.summary:null,filters=readHistoryFilters(s?.filters||history?.scope?.filters);
 const source=filters.provider?providerLabel(filters.provider):'Todas as fontes do recorte';
 const icons=[Building2,Layers3,CalendarDays,PackageCheck];
 return <Panel title="O que o histórico mostra" className="product-analysis-panel history-insights" action={<span className="insight-heading-actions"><span className="badge insight-documental">Regras documentais</span><Action to={'inteligencia?estudo='+encodeURIComponent(studyId)+'&etapa=historico&aba=fontes'+planningSuffix} secondary>Ver fontes</Action></span>}>
  <ul className="product-analysis-empty">{insights.map((insight,i)=>{const Icon=icons[i];return <li key={insight.id} data-insight={insight.id} data-status={insight.status}><span className="analysis-symbol"><Icon {...IconProps}/></span><div><strong>{insight.label}</strong><span className="insight-status">{insight.status==='partial'?'Parcial':'Indisponível'}</span><p>{insight.text}</p></div></li>})}</ul>
  <button type="button" className="insight-method-button" onClick={()=>setInspect(true)}>Métodos e evidências</button>
  {inspect?<Dialog title="Como chegamos a estas informações" onClose={()=>setInspect(false)}>
   {demonstration?<p role="note">Demonstração fictícia. Os dados abaixo foram gerados para testes.</p>:null}
   <p>{s?`${phases[s.phase]||s.phase} · ${s.start} a ${s.end} · Unidade: ${s.unit||'Não informada'}`:'Recorte sem resumo verificável.'}</p>
   <p>{source}. {filters.only_comparable?'Apenas registros comparáveis.':'Os totais excluem registros incompatíveis.'}</p>
   <p>As informações são parciais. Não representam toda a demanda dos municípios.</p>
   <p>Tendência e sazonalidade: indisponíveis. Sem série mensal comparável com cobertura contínua comprovada.</p>
   <ol className="insight-method-list">{insights.map(insight=><li key={insight.id}><h3>{insight.label}</h3><p>{insight.text} {insight.status==='partial'?'Informação parcial.':'Informação indisponível.'}</p><p><strong>Método: </strong>{insight.formula}</p><p><strong>Condição mínima: </strong>{insight.minimum}</p><p>{insight.limitation}</p>
    {insight.evidence.length?<><p>Prévia de evidências; os indicadores não são calculados pela quantidade de links.</p><ul>{insight.evidence.map(e=><li key={e.factId}>{/^https?:\/\//i.test(e.url||'')?<a href={e.url!} target="_blank" rel="noopener noreferrer">Abrir fonte · {providerLabel(e.provider)}</a>:<span>{providerLabel(e.provider)} · endereço indisponível</span>}<small>Data: {e.date||'Não informada'} · Consulta: {e.consultedAt||'Não informada'}</small><small>Identificador do registro: {e.factId}</small></li>)}</ul>{insight.evidenceTruncated?<p>Esta prévia é limitada. Confira os registros na análise do histórico.</p>:null}</>:<p>Sem documentos disponíveis nesta prévia. Confira as fontes do histórico.</p>}
   </li>)}</ol>
   <Action to={'inteligencia?estudo='+encodeURIComponent(studyId)+'&etapa=historico&aba=fontes'+planningSuffix} secondary>Conferir registros e documentos</Action>
  </Dialog>:null}
 </Panel>;
}
