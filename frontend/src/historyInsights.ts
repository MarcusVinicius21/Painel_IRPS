import type {Row} from './api';

export type InsightEvidence={factId:string;provider:string;url:string|null;date:string|null;consultedAt:string|null};
export type HistoryInsight={
 id:'municipalities'|'processes'|'dates'|'comparison';label:string;text:string;
 status:'partial'|'unavailable';formula:string;minimum:string;limitation:string;
 evidence:InsightEvidence[];evidenceTruncated:boolean;
};
const count=(n:unknown):n is number=>typeof n==='number'&&Number.isSafeInteger(n)&&n>=0;
const day=(v:unknown):v is string=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;
const formatDay=(v:string)=>v.split('-').reverse().join('/');

// Presentation of existing aggregates only. Never count preview links as facts,
// sum municipal process counts, recompute quantities or modify archived snapshots.
export function historyInsights(history:Row|null|undefined):HistoryInsight[]{
 const s=history?.contract_version===2?history.summary:null,scope=history?.scope;
 const valid=!!s&&typeof s.phase==='string'&&day(s.start)&&day(s.end)&&s.start<=s.end&&
  (!scope||(scope.phase===s.phase&&scope.start===s.start&&scope.end===s.end));
 const cities=new Set<string>(Array.isArray(scope?.municipalities)?scope.municipalities:[]);
 const rows:Row[]=valid&&Array.isArray(history?.municipalities)?history.municipalities.filter((r:Row)=>r.municipality&&(!cities.size||cities.has(r.municipality.ibge))):[];
 const observed=rows.filter(r=>count(r.observed_records)&&r.observed_records>0);
 const evidence=new Map<string,InsightEvidence>();
 for(const r of observed)for(const e of Array.isArray(r.evidence)?r.evidence:[]){
  if(typeof e.fact_id==='string')evidence.set(e.fact_id,{factId:e.fact_id,provider:e.provider||'Fonte não informada',url:typeof e.url==='string'?e.url:null,date:day(e.event_date)?e.event_date:null,consultedAt:typeof e.consulted_at==='string'?e.consulted_at:null});
 }
 const all=[...evidence.values()],partial='Recorte parcial. Não comprova consumo ou necessidade futura.';
 const make=(id:HistoryInsight['id'],label:string,text:string|null,formula:string,minimum:string,reason:string):HistoryInsight=>({
  id,label,text:text??reason,status:text===null?'unavailable':'partial',formula,minimum,
  limitation:valid?partial:'Resumo verificável indisponível neste estudo. Os dados preservados não foram recalculados.',
  evidence:valid?all.slice(0,8):[],evidenceTruncated:all.length>8||rows.some(r=>r.evidence_truncated===true)
 });
 const municipalities=valid&&count(s.selected_municipalities)&&s.selected_municipalities>0&&count(s.municipalities_with_records)&&count(s.observed_records)&&s.municipalities_with_records<=s.selected_municipalities&&s.municipalities_with_records<=s.observed_records
  ?`${s.municipalities_with_records} de ${s.selected_municipalities} municípios selecionados têm registros.`:null;
 const processes=valid&&count(s.distinct_processes)&&s.distinct_processes>0&&count(s.observed_records)&&s.distinct_processes<=s.observed_records
  ?`${s.distinct_processes} ${s.distinct_processes===1?'processo identificado':'processos identificados'}${s.process_identity_complete?' no recorte.':'; identificação parcial.'}`:null;
 const dates=valid&&observed.length>0&&count(s.municipalities_with_records)&&observed.length===s.municipalities_with_records&&observed.every(r=>day(r.first_observed)&&day(r.last_observed)&&r.first_observed<=r.last_observed&&r.first_observed>=s.start&&r.last_observed<=s.end)
  ?{first:observed.map(r=>r.first_observed as string).sort()[0],last:observed.map(r=>r.last_observed as string).sort().at(-1)!}:null;
 const comparison=valid&&count(s.observed_records)&&s.observed_records>0&&count(s.comparable_records)&&count(s.excluded_records)&&s.comparable_records+s.excluded_records===s.observed_records
  ?`${s.comparable_records} de ${s.observed_records} registros comparáveis. ${s.excluded_records} fora dos totais.`:null;
 return [
  make('municipalities','Municípios identificados',municipalities,'Contagem global de municípios com fatos atuais, dentro do recorte selecionado.','Resumo global válido e número conhecido de municípios selecionados.','Sem contagem municipal verificável.'),
  make('processes','Processos identificados',processes,'Contagem global de obrigações identificáveis, fornecida pelo histórico. Não somamos contagens municipais.','Identidades de processo confiáveis. A identificação pode ser parcial.','Sem processos identificáveis informados.'),
  make('dates','Datas observadas',dates?(dates.first===dates.last?`Registros em ${formatDay(dates.first)}.`:`De ${formatDay(dates.first)} a ${formatDay(dates.last)}.`):null,'Menor primeira ocorrência e maior última ocorrência dos municípios com registros. Usa datas agregadas completas, não a prévia de documentos.','Datas válidas para todos os municípios identificados, dentro do período consultado.','Sem datas suficientes para delimitar os registros.'),
  make('comparison','Comparabilidade',comparison,'Registros comparáveis e excluídos do resumo global. Os dois grupos devem corresponder ao total observado.','Contagens globais conhecidas e consistentes; mesma fase e regras de unidade, embalagem e versão.','Sem registros suficientes para conferir comparabilidade.')
 ];
}
