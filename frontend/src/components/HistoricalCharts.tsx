import type {HistoricalWindow} from '../historyIndicators';
import type {Row} from '../api';
import {quantity} from '../api';
import {phases} from '../api';
import {providerLabel,readHistoryFilters} from '../historyIndicators';
import {Panel} from './ui';

export function HistoricalCharts({history,rows,unit,className=''}:{history:Row|null;rows:Row[];unit:string;className?:string}){
 const windows:HistoricalWindow[]=history?.contract_version===2?(history.temporal_windows||[]):[];
 const summary=history?.contract_version===2?history.summary:null;
 const series=history?.contract_version===2&&history.observed_series?.version===1?history.observed_series:null;
 const filters=readHistoryFilters(summary?.filters||history?.scope?.filters);
 const source=filters.provider?providerLabel(filters.provider):'Todas as fontes do recorte';
 const labelUnit=summary?.unit||unit;
 const volumes=[1,3,6,12].map(months=>{
  const matches=windows.filter(w=>w.months===months),window=matches.length===1?matches[0]:null;
  let value:number|null=null,negative:number|null=null;
  if(window?.observed_quantity!=null&&String(window.observed_quantity).trim()!==''&&labelUnit){const parsed=Number(window.observed_quantity);if(Number.isFinite(parsed)){if(parsed>=0)value=parsed;else negative=parsed;}}
  return {months,window,value,negative};
 });
 const max=Math.max(0,...volumes.filter(v=>v.value!==null).map(v=>v.value!));
 return <section className={'historical-charts '+className} aria-label="Gráficos e indicadores do item">
  <Panel scrollable title="Quantidade observada por período" className="volume-windows-panel"><div className="chart-surface">
   {windows.length?<><p className="volume-partial">Totais parciais · janelas sobrepostas</p><dl className="volume-windows">{volumes.map(({months,window,value,negative})=>{
    const period=window?`${window.start} a ${window.end}${window.scope_covers_requested_window?'':' · período reduzido'}`:'Período não informado';
    const text=value===null?(negative!==null?quantity(negative)+' '+labelUnit:'Não disponível'):quantity(value)+' '+labelUnit;
    const description=`${months} ${months===1?'mês':'meses'}: ${text}. Total observado parcial. ${period}. ${source}.`;
    return <div key={months}><dt>{months} {months===1?'mês':'meses'}</dt><dd><span className="volume-value">{text}</span>{value===null?<span className="volume-missing">{negative!==null?'Valor negativo: confira a fonte':window?.observed_quantity!=null?'Confira a quantidade na fonte':'Sem quantidade informada'}</span>:<span className="volume-track" role="img" tabIndex={0} aria-label={description} title={description}><span className={'volume-bar'+(value===0?' volume-zero':'')} style={{height:(max>0?value/max*100:0)+'%'}} aria-hidden="true"/>{value===0?<span className="volume-zero-label">Zero documentado</span>:null}</span>}</dd></div>;
   })}</dl><p className="volume-context">{summary?`${phases[summary.phase]||summary.phase} · ${summary.start} a ${summary.end}`:'Recorte a conferir'} · {source}</p><details className="volume-limits"><summary>Períodos, fonte e limites</summary><p>As janelas se sobrepõem. Não some as barras nem interprete como meses independentes.</p><p>{source} · {filters.only_comparable?'Apenas registros comparáveis':'Totais apenas comparáveis'}. Unidade: {labelUnit||'Não informada'}.</p><p>Sem cobertura suficiente, não calculamos média mensal ou previsão de compra.</p><ul>{volumes.map(({months,window,value,negative})=><li key={months}>{months} {months===1?'mês':'meses'}: {value===null?(negative!==null?quantity(negative)+' '+labelUnit+' · confira a fonte':'Não disponível'):quantity(value)+' '+labelUnit}. {window?`${window.start} a ${window.end}${window.scope_covers_requested_window?'':' · período reduzido'}`:'Período não informado'}. Total observado parcial.</li>)}</ul></details></>:<p>Sem quantidades comparáveis.<small>{history?.contract_version===2?'Os registros consultados não informam quantidades comparáveis.':history?'Estudo anterior sem resumo agregado. As evidências preservadas continuam disponíveis.':'O código ainda exige vínculo técnico revisado.'}</small></p>}
  </div></Panel>
  <Panel scrollable title="Evolução mensal das ocorrências" className="observed-monthly"><div className="chart-surface">{series?<ObservedSeries monthly entries={series.monthly.map((r:Row)=>({...r,label:r.month}))} unit={labelUnit} context={series} source={source}/>:<p>Sem série mensal comparável.<small>Períodos não consultados não representam zero compras.</small></p>}</div></Panel>
  <Panel scrollable title="Municípios e cobertura" className="observed-geography"><div className="chart-surface">{series?<><ObservedSeries entries={series.states.map((r:Row)=>({...r,label:r.uf}))} unit={labelUnit} context={series} source={source}/><details><summary>Ver municípios e fontes</summary><ul>{series.municipalities.map((r:Row)=><li key={r.municipality.ibge}>{r.municipality.name}/{r.municipality.uf}: {r.observed_quantity==null?'Não disponível':quantity(r.observed_quantity)+' '+labelUnit}. {r.comparable_records} registros comparáveis.</li>)}</ul></details></>:<p>{rows.length} municípios no recorte<small>{history?'Confira as evidências de cada município.':'Sem histórico revisado para este código.'}</small></p>}</div></Panel>
 </section>;
}

function ObservedSeries({entries,unit,context,source,monthly=false}:{entries:Row[];unit:string;context:Row;source:string;monthly?:boolean}){
 const value=(r:Row)=>r.observed_quantity!=null&&String(r.observed_quantity).trim()!==''&&unit&&Number.isFinite(Number(r.observed_quantity))&&Number(r.observed_quantity)>=0?Number(r.observed_quantity):null;
 const max=Math.max(0,...entries.map(r=>value(r)??0));
 if(monthly)return <><MonthlyObservedLine entries={entries} unit={unit}/><details className="monthly-source-table"><summary>Ver valores mensais e fontes</summary><ObservedSeries entries={entries} unit={unit} context={context} source={source}/></details><p className="series-context">Observações parciais. Sem média móvel ou previsão.</p></>;
 return <><p className="series-context">{phases[context.phase]||context.phase} · {context.start} a {context.end} · {source}<br/>Quantidades observadas parciais · {unit}</p><ul className="observed-series" aria-label="Quantidades documentadas">{entries.map(r=>{const n=value(r),text=n===null?'Não disponível':quantity(r.observed_quantity)+' '+unit;return <li key={r.label}><span>{r.label}</span><span className="series-track" role="img" tabIndex={0} aria-label={`${r.label}: ${text}. ${r.comparable_records} registros comparáveis. Cobertura não comprovada.`}>{n===null?<span className="series-unknown">Sem quantidade informada</span>:<><span className="series-bar" aria-hidden="true" style={monthly?{height:(max?n/max*100:0)+'%',width:'60%'}:{width:(max?n/max*100:0)+'%'}}/><span className="series-value">{text}{n===0?' · zero documentado':''}</span></>}</span></li>})}</ul><details className="series-evidence"><summary>Origem e limites dos números</summary><p>{context.limitation}</p><p>Sem cobertura comprovada. Não calculamos percentuais de participação.</p><ul>{entries.map(r=><li key={r.label}>{r.label}: {r.comparable_records} registros. Fontes: {r.providers.map(providerLabel).join(', ')||'Não informadas'}. Consultas: {r.consulted_at.join(', ')||'Não informadas'}. Evidências: {r.fact_ids.join(', ')||'Sem registros'}. Documentos: {r.source_ids.join(', ')||'Sem documentos'}. {(r.sources||[]).map((s:Row)=><span key={s.id}> {/^[hH][tT][tT][pP][sS]?:\/\//.test(s.url||'')?<a href={s.url} target="_blank" rel="noopener noreferrer">Abrir fonte · {providerLabel(s.provider)}</a>:null}</span>)}</li>)}</ul></details></>;
}

/** Geometria de apresentação: não completa meses sem fatos nem calcula demanda. */
function MonthlyObservedLine({entries,unit}:{entries:Row[];unit:string}){
 const valid=entries.filter(r=>/^\d{4}-\d{2}$/.test(r.label)&&Number(r.label.slice(5))>=1&&Number(r.label.slice(5))<=12&&r.observed_quantity!=null&&Number.isFinite(Number(r.observed_quantity))&&Number(r.observed_quantity)>=0);
 const points=valid.map(r=>({label:String(r.label),observed_quantity:r.observed_quantity,serial:Number(r.label.slice(0,4))*12+Number(r.label.slice(5))-1,n:Number(r.observed_quantity)})).sort((a,b)=>a.serial-b.serial);
 if(!points.length)return <p>Sem quantidades mensais comparáveis. Meses ausentes não representam zero.</p>;
 const first=points[0].serial,last=points[points.length-1].serial,max=Math.max(1,...points.map(p=>p.n));
 const x=(n:number)=>first===last?175:32+(n-first)/(last-first)*288,y=(n:number)=>78-n/max*62;
 return <svg className="monthly-observed-line" viewBox="0 0 350 108" role="img" aria-label={`Série mensal parcial: ${points.length} pontos documentados em ${unit}. Lacunas não são ligadas nem preenchidas.`}>
  {[0,.5,1].map(t=><g key={t}><line x1="32" x2="320" y1={y(t*max)} y2={y(t*max)} className="monthly-grid"/><text x="27" y={y(t*max)+3} textAnchor="end">{quantity(t*max)}</text></g>)}
  {points.slice(1).map((p,i)=>p.serial===points[i].serial+1?<line className="monthly-observation-segment" key={p.label} x1={x(points[i].serial)} y1={y(points[i].n)} x2={x(p.serial)} y2={y(p.n)}/>:null)}
  {points.map(p=><circle key={p.label} className="monthly-observation-point" cx={x(p.serial)} cy={y(p.n)} r="3"><title>{p.label}: {quantity(p.observed_quantity)} {unit} · parcial</title></circle>)}
  <text x={x(first)} y="97" textAnchor="middle">{points[0].label}</text>{last!==first?<text x={x(last)} y="97" textAnchor="middle">{points[points.length-1].label}</text>:null}
 </svg>;
}
