import {useEffect,useState} from 'react';
import './official-prices.css';
import {api,ApiError,businessDate,money,quantity} from '../api';
import type {Row} from '../api';
import {Panel,Field,Notice,DataTable} from './ui';

/** Code-scoped Compras.gov query; never aggregates PNCP or fills V4 inputs. */
export function OfficialPrices({entry}:{entry:Row}){
 const [source,setSource]=useState('online');const [cursors,setCursors]=useState<Record<number,string>>({});
 const endToday=businessDate();const [draftStart,setDraftStart]=useState(endToday.slice(0,4)+'-01-01'),[draftEnd,setDraftEnd]=useState(endToday);
 const [period,setPeriod]=useState({start:draftStart,end:draftEnd}),[page,setPage]=useState(1),[retry,setRetry]=useState(0);
 const [result,setResult]=useState<Row|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState(''),[validation,setValidation]=useState(false),[retryAt,setRetryAt]=useState(0),[clock,setClock]=useState(Date.now());
 const kind=entry.kind==='CATSER'?'servico':'material';
 const url='/catalogue-intelligent/'+(source==='online'?'reference-prices':'monthly-prices')+'?'+new URLSearchParams({kind,code:entry.code,code_type:'codigoItemCatalogo',start:period.start,end:period.end,page:String(page),...(source==='monthly'&&cursors[page]?{cursor:cursors[page]}:{})});
 useEffect(()=>{let current=true;const abort=new AbortController();setLoading(true);setResult(null);setError('');setValidation(false);setRetryAt(0);
  void api(url,{signal:abort.signal}).then(data=>{if(current){setResult(data);if(data.next_cursor)setCursors(old=>({...old,[page+1]:data.next_cursor}));if(data.source_error?.retry_after)setRetryAt(Date.now()+data.source_error.retry_after*1000);}}).catch(e=>{if(current){setError(e.message);setValidation(e instanceof ApiError&&[400,422].includes(e.status));if(e instanceof ApiError&&e.payload?.source_error){setResult(e.payload);setRetryAt(Date.now()+(e.payload.source_error.retry_after||0)*1000);}}}).finally(()=>{if(current)setLoading(false);});
  return()=>{current=false;abort.abort();};
 },[url,retry]);
 useEffect(()=>{if(retryAt<=Date.now())return;const t=window.setInterval(()=>{setClock(Date.now());if(Date.now()>=retryAt)clearInterval(t);},1000);return()=>clearInterval(t);},[retryAt]);
 const wait=Math.max(0,Math.ceil((retryAt-clock)/1000));
 return <Panel title="Preços praticados — Compras.gov.br" className="official-prices">
  <p>{entry.kind} {entry.code} · Consulta nacional por código. Independente do vínculo PNCP.</p>
  <Field label="Consultar preços em"><select value={source} onChange={e=>{setSource(e.target.value);setPage(1);}}><option value="online">API oficial · sob demanda</option><option value="monthly">Arquivos mensais já importados</option></select></Field>
  <form className="form-grid" onSubmit={e=>{e.preventDefault();setPage(1);setPeriod({start:draftStart,end:draftEnd});setRetry(r=>r+1);}}>
   <Field label="Preços desde"><input type="date" required value={draftStart} max={draftEnd} onChange={e=>setDraftStart(e.target.value)}/></Field>
   <Field label="Preços até"><input type="date" required value={draftEnd} max={endToday} min={draftStart} onChange={e=>setDraftEnd(e.target.value)}/></Field>
   <button className="button secondary" disabled={loading||wait>0}>Consultar preços oficiais</button>
  </form>
  <p className="subtle">Até 366 dias por consulta · 10 registros por página. Confira unidade, embalagem e especificação.</p>
  {loading?<p role="status">Consultando preços no Compras.gov.br… O histórico PNCP continua disponível abaixo.</p>:null}
  {validation?<Notice tone="warning">Revise o período da consulta. {error}</Notice>:error||result?.source_error?<Notice tone="warning">Não foi possível atualizar esta fonte agora. {result?.state==='partial'?'Mostramos a última consulta preservada, sem atualização confirmada.':''}<br/>{error||result?.source_error?.message}<details><summary>Detalhes da consulta</summary>{result?.source_error?.code} · Resposta da fonte: {result?.source_error?.upstream_http_status??'não recebida'}</details><button className="button secondary" disabled={wait>0||loading} onClick={()=>setRetry(r=>r+1)}>{wait?`Aguarde ${wait}s`:'Tentar novamente'}</button></Notice>:null}
  {result?<><p role="status">{result.state==='not_collected'?'Período ainda não importado':result.state==='source_unavailable'?'Fonte indisponível · sem consulta preservada':result.state==='partial'?'Consulta preservada · atualização pendente':result.state==='empty_valid_response'?'Consulta concluída · sem preços neste recorte':'Preços oficiais encontrados'} · {period.start} a {period.end} · Página {page}{result.total_pages_reported!=null?' de '+quantity(result.total_pages_reported):''} · {result.total_records_reported!=null?quantity(result.total_records_reported)+' registros informados pela fonte':'Total não informado'}</p>
   {result.coverage?<details className="monthly-coverage"><summary>Meses consultados: {result.coverage.months_reconciled.length} de {result.coverage.months_requested.length} com os dois arquivos conferidos</summary><p>Arquivos completos não comprovam todas as compras dos municípios. Meses ausentes não significam zero compras.</p><table><caption>Cobertura dos arquivos mensais</caption><thead><tr><th>Mês</th><th>Materiais</th><th>Serviços</th></tr></thead><tbody>{result.coverage.months.map((m:Row)=><tr key={m.month}><th>{m.month.slice(0,7)}</th>{['material','servico'].map(k=><td key={k}>{({reconciled:'Arquivo conferido',not_collected:'Ainda não importado',review_required:'Precisa de conferência',provisional:'Mês em andamento'} as Record<string,string>)[m.files[k].state]||'Conferência pendente'}{m.files[k].accepted_rows!=null?' · '+quantity(m.files[k].accepted_rows)+' linhas':''}</td>)}</tr>)}</tbody></table></details>:null}
   {result.source_kind==='monthly_file'?<Notice>Arquivo mensal do Compras.gov.br. Somente estes meses foram consultados: {result.scope.imported_months.map((m:string)=>m.slice(0,7)).join(', ')||'nenhum'}. Não somamos essas linhas aos resultados da API ou do PNCP. Revisões do mesmo item precisam de conferência.</Notice>:null}
   {result.state==='empty_valid_response'?<Notice>A fonte consultada não retornou preços para o código, período e filtros. Isso não significa que o item nunca foi comprado.</Notice>:null}
   {result.records?.length?<DataTable<Row> rows={result.records} id={r=>String(r.purchase_id)+':'+String(r.item_number)+':'+(r.source_record_sha256||'')} pageSize={10} caption="Preços públicos do Compras.gov.br" columns={[
    {label:'Item e origem',render:r=><><strong>{r.description||'Descrição não informada'}</strong><small>{entry.kind} {r.catalogue_code} · Compra {r.purchase_id||'não informada'} · Item {r.item_number??'não informado'}</small><details><summary>Especificação e embalagem</summary><p>{r.specification||'Especificação adicional não informada.'}</p>{Object.entries(r.package||{}).map(([k,v])=><p key={k}>{['capacidadeUnidadeFornecimento','capacidade_unidade_fornecimento'].includes(k)?'Capacidade':['siglaUnidadeMedida','sigla_unidade_medida'].includes(k)?'Medida':'Fornecimento'}: {String(v)}</p>)}</details>{r.review_reasons?.map((reason:string)=><small key={reason}>{reason}</small>)}<a href={r.source_url||result.url} target="_blank" rel="noreferrer">Abrir consulta oficial</a></>},
    {label:'Quantidade e unidade',render:r=><>{quantity(r.quantity)}<small>{r.unit||'Unidade não informada pela fonte'}</small></>},
    {label:'Preço unitário',render:r=><strong>{money(r.unit_price)}</strong>},
    {label:'Comprador e local',render:r=><>{r.agency||'Órgão não informado'}<small>UASG {r.uasg||'não informada'} · {r.purchasing_unit||'Unidade compradora não informada'}</small><small>{r.municipality_name||'Município a conferir'} · {r.state||'UF não informada'} · Código {r.municipality_code??'não informado'}</small></>},
    {label:'Datas',render:r=><>Compra: {r.purchase_date||'não informada'}<small>Resultado: {r.result_date||'não informado'}</small></>}
   ]}/>:null}
   <div className="actions"><button className="button secondary" disabled={loading||page===1||wait>0} onClick={()=>setPage(p=>p-1)}>Preços anteriores</button><button className="button secondary" disabled={loading||!result.has_next_page||(source==='online'&&page>=100)||wait>0} onClick={()=>setPage(p=>p+1)}>Próximos preços</button></div>
   <details><summary>Fonte, período e conferência</summary><p>{result.consulted_at?'Consultado em '+new Date(result.consulted_at).toLocaleString('pt-BR'):'Consulta ainda não comprovada.'} {result.cache_hit?'Consulta preservada reutilizada.':''}</p>{result.url?<a href={result.url} target="_blank" rel="noreferrer">Ver fonte pública do Compras.gov.br</a>:null}<p>Identificador da evidência: {result.original_response_sha256?.slice(0,16)||'não disponível'}.</p><p>O mesmo código pode ter apresentações diferentes. Não somamos quantidades ou calculamos uma média automática.</p><p>Esses resultados não comprovam cobertura municipal, pagamento, entrega ou consumo.</p></details>
  </>:null}
 </Panel>;
}
