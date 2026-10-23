import {money,quantity} from '../api';
import type {Row} from '../api';
import {DataTable,Notice} from './ui';

export function HistoryDetails({rows,view,unit}:{rows:Row[];view:string;unit:string}){
 if(view==='anual')return <><Notice>Totais anuais observados no recorte. Anos sem consulta suficiente permanecem sem informação.</Notice><DataTable<Row> rows={rows} id={r=>r.municipality.ibge} caption="Histórico anual documentado por município" columns={[{label:'Município',render:r=>r.municipality.name},{label:'Anos encontrados',render:r=>r.annual?.length?r.annual.map((a:Row)=><p key={a.year}>{a.year}: {quantity(a.observed_quantity)} {unit}<small>{a.comparable_records} registros comparáveis · total parcial</small></p>):'Informação insuficiente'},{label:'Média mensal',render:()=> 'Indisponível sem cobertura temporal comprovada'}]}/></>;
 const records=rows.flatMap(r=>r.evidence.filter((e:Row)=>view!=='precos'||!r.excluded_from_totals?.some((x:Row)=>x.fact_id===e.fact_id)).map((e:Row)=>({...e,municipality_name:r.municipality.name})));
 if(!records.length)return <Notice>{view==='precos'?'Ainda não há preços comparáveis associados ao item neste recorte.':'Ainda não há documentos vinculados ao item neste recorte.'} Confira o vínculo técnico e as fontes.</Notice>;
 return <DataTable<Row> rows={records} id={r=>r.fact_id} caption={view==='precos'?'Preços documentados dos registros comparáveis':'Fontes e documentos por registro'} columns={[
  {label:'Município e item',render:r=><>{r.municipality_name}<small>{r.description}</small><small>{r.buyer_name||'Órgão a conferir'}{r.buyer_cnpj?' · CNPJ '+r.buyer_cnpj:''}</small></>},
  {label:'Data e situação',render:r=><>{r.event_date}<small>Mesma fase do recorte selecionado</small></>},
  {label:'Quantidade e unidade',render:r=><>{quantity(r.quantity)} {r.unit}</>},
  {label:'Preço unitário documentado',render:r=>money(r.unit_price)},
  {label:'Documento e consulta',render:r=><><a href={r.url} target="_blank" rel="noreferrer">Abrir fonte · {r.provider}</a><small>{new Date(r.consulted_at).toLocaleString('pt-BR')} · item versão {r.item_version}</small></>}
 ]}/>;
}
