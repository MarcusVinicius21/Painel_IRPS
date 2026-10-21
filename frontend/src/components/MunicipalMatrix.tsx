import type {ReactNode} from 'react';
import type {Row} from '../api';
import {quantity} from '../api';
import {DataTable,Badge} from './ui';

function Value({value,reason='Informação insuficiente'}:{value:unknown;reason?:string}){return value==null?<span aria-label={reason} title={reason}>—</span>:<>{quantity(value)}</>;}
export function MunicipalMatrix({rows,planning=false,unit,register,v4,context}:{rows:Row[];planning?:boolean;unit:string;context:{phase:string;start:string;end:string};register:Row|null;v4:{loading:boolean;error:string;data:Row|null}}){
 const evidence=(r:Row,label?:ReactNode)=><details><summary>{label||'Detalhes'}</summary><p>{r.first_observed||'Data indisponível'} a {r.last_observed||'—'}. Quantidade observada: {quantity(r.observed_quantity)} {unit}.</p>{r.evidence.map((e:Row)=><p key={e.fact_id}><a href={e.url} target="_blank" rel="noreferrer">{e.provider} · {e.event_date}</a><small>{e.description} · consulta {e.consulted_at}</small></p>)}{!r.evidence.length?<p>Sem evidências tecnicamente vinculadas a este código.</p>:null}</details>;
 const registered=(r:Row)=>register?.municipalities.find((x:Row)=>x.ibge===r.municipality.ibge);
 const calc=(r:Row)=>v4.data?.records?.find((l:Row)=>l.ibge===r.municipality.ibge);
 const city={label:'Município · IBGE',sort:(r:Row)=>r.municipality.name,render:(r:Row)=><><strong>{r.municipality.name} · {r.municipality.uf}</strong><small>{r.municipality.ibge}</small></>};
 function exportTable(){const fields=['classification','municipality_ibge','municipality','phase','period_start','period_end','observed_records','distinct_processes','quantity_1_month','quantity_3_months','quantity_6_months','quantity_12_months','last_observed','unit','evidence_urls'];const safe=(v:unknown)=>{let t=String(v??'');if(/^[=+@-]/.test(t))t="'"+t;return '"'+t.replaceAll('"','""')+'"';};const values=rows.map(r=>[r.coverage_state==='demonstration'?'synthetic':r.observed_records==null?'not_available':'official',r.municipality.ibge,r.municipality.name,context.phase,context.start,context.end,r.observed_records,r.distinct_processes,...[1,3,6,12].map(n=>r.temporal_windows.find((w:Row)=>w.months===n)?.observed_quantity),r.last_observed,unit,r.evidence.map((e:Row)=>e.url).join(' | ')]);const blob=new Blob(['\ufeff'+[fields,...values].map(row=>row.map(safe).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='IRPS_historico_municipal_parcial.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 const columns=planning?[
  city,{label:'Histórico observado · 12 meses',render:(r:Row)=><Value value={r.temporal_windows.find((w:Row)=>w.months===12)?.observed_quantity}/>},
  {label:'Necessidade calculada · V4',render:(r:Row)=>v4.loading?'Carregando…':v4.error?'Erro de consulta':calc(r)?.quantity!=null?<Value value={calc(r).quantity}/>:<span title="Dados insuficientes para cálculo">Dados insuficientes para cálculo</span>},
  {label:'Entradas pendentes',render:(r:Row)=><Badge tone="amber">{calc(r)?.quantity!=null?'Conferir memória':'Revisar dados'}</Badge>},
  {label:'Sugestão do consórcio',render:(r:Row)=><Value value={registered(r)?.suggested_quantity}/>},
  {label:'Confirmação municipal',render:(r:Row)=><Value value={registered(r)?.confirmed_quantity}/>},
  {label:'Unidade',render:()=>unit||'A conferir'},
  {label:'Situação e evidências',render:(r:Row)=>evidence(r)}
 ]:[city,{label:'Registros / processos',render:(r:Row)=><><Value value={r.observed_records}/><small>Processos: <Value value={r.distinct_processes}/></small></>},
 ...[1,3,6,12].map(months=>({label:months===1?'Último mês (qtd)':`Últimos ${months} meses (qtd)`,render:(r:Row)=><Value value={r.temporal_windows.find((x:Row)=>x.months===months)?.observed_quantity}/>})),
 {label:'Última ocorrência',render:(r:Row)=>r.last_observed?new Date(r.last_observed+'T12:00:00').toLocaleDateString('pt-BR'):'—'},
 {label:'Preço comparável',render:()=> <span title="Mediana indisponível sem comparabilidade e cobertura verificadas">—</span>},
 {label:'Cobertura / fontes',render:(r:Row)=>evidence(r,<Badge tone="amber">{r.coverage_state==='demonstration'?'Fictício':r.coverage_state==='scope_complete'?'Escopo conferido':'Não verificada'}</Badge>)}
 ];
 return <>{!planning?<button className="button secondary export-history" onClick={exportTable}>Exportar tabela</button>:null}<DataTable<Row> rows={rows} columns={columns} pageSize={8} id={r=>r.municipality.ibge} caption="Histórico municipal em janelas e necessidade V4"/><p className="matrix-key">— Informação insuficiente; não significa quantidade zero. {unit?'Unidade: '+unit+'.':'Unidade a conferir.'} Sem vínculo revisado, não há média de preço.</p></>;
}
