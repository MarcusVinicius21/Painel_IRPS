import type {Row} from './api';
import {money,quantity,phases} from './api';

export type HistoryFilters={provider:string|null;only_comparable:boolean};
export const readHistoryFilters=(value?:Partial<HistoryFilters>|null):HistoryFilters=>({provider:value?.provider||null,only_comparable:value?.only_comparable===true});
export const providerLabel=(value:string)=>({PNCP:'PNCP · publicações',PNCP_ITENS:'PNCP · itens publicados',PNCP_RESULTADOS:'PNCP · resultados de itens',PNCP_CONTRATOS:'PNCP · contratos'} as Record<string,string>)[value]||value;
export type HistoricalSummary={
 filters?:HistoryFilters;
 municipalities_with_records:number; distinct_processes:number|null;
 observed_quantity:string|null; documented_amount:string|null;
 unit:string; phase:string; start:string; end:string;
 process_identity_complete:boolean; partial:boolean; limitation:string;
};
export type HistoricalWindow={months:number;observed_quantity:string|null;start:string;end:string;scope_covers_requested_window:boolean};

// Old study snapshots remain immutable. Never reconstruct a total from capped evidence.
export function historyIndicators(history:Row|null|undefined){
 const summary:HistoricalSummary|null=history?.contract_version===2?history.summary:null;
 const notice=history&&!summary?'Estudo anterior: resumo agregado indisponível. Os registros preservados continuam abaixo.':summary?.limitation;
 const context=summary?`${phases[summary.phase]||summary.phase} · ${summary.start} a ${summary.end}${summary.filters?' · '+(summary.filters.provider?providerLabel(summary.filters.provider):'Todas as fontes')+(summary.filters.only_comparable?' · apenas comparáveis':''):''}`:undefined;
 return {notice,items:[
  {label:'Municípios com registros',value:summary?.municipalities_with_records??null,detail:context},
  {label:'Processos identificados',value:summary?.distinct_processes??null,detail:summary&&!summary.process_identity_complete?'Identificação parcial dos processos':context},
  {label:'Quantidade documentada',value:summary?.observed_quantity==null?null:quantity(summary.observed_quantity),detail:summary?`${summary.unit} · total observado parcial`:undefined},
  {label:'Valor documentado',value:summary?.documented_amount==null?null:money(summary.documented_amount),detail:summary?'Em reais · valor conhecido parcial':undefined}
 ]};
}
