import {useEffect,useState} from 'react';
import {api,nav,post,quantity,money,useApi,businessDate} from '../api';
import type {Row} from '../api';
import {Action,Badge,DataTable,Empty,Field,Notice,Page,Panel,Stats} from '../components/ui';

const today=()=>businessDate();
const defaultStart='2024-01-01';
const coverageLabel=(state:string)=>({demonstration:'Dados de demonstração',not_collected:'Ainda não consultado',
 pending:'Consulta pendente',failed:'Consulta falhou',consulted:'Consulta concluída neste recorte',
 partial:'Parte das consultas concluída',scope_complete:'Consultas deste recorte concluídas'} as Record<string,string>)[state]||'Cobertura não verificada';

export function Catalogue(){
 const context=useApi();const [cities,setCities]=useState<string[]>(context.identity?.identity_mode==='operational_local'?[]:['3131307','3101607','3169703']);
 useEffect(()=>{if(context.identity?.identity_mode==='operational_local'&&!cities.length&&context.cities.length)setCities(context.cities.slice(0,2).map(c=>c.ibge));},[context.cities,context.identity?.identity_mode]);
 const [start,setStart]=useState(defaultStart);const [end,setEnd]=useState(today);
 const [phase,setPhase]=useState('publicado_estimado');const [products,setProducts]=useState<Row[]>([]);
 const [coverage,setCoverage]=useState<Row|null>(null);const [candidates,setCandidates]=useState<Row[]>([]);
 const [selected,setSelected]=useState<Row|null>(null);const [name,setName]=useState('');const [category,setCategory]=useState('');
 const [justification,setJustification]=useState('');const [evidence,setEvidence]=useState('');const [loading,setLoading]=useState(false);
 const [priceKind,setPriceKind]=useState('material');const [priceCode,setPriceCode]=useState('');const [codeType,setCodeType]=useState('codigoItemCatalogo');
 const [priceStart,setPriceStart]=useState(()=>{const value=new Date();value.setMonth(value.getMonth()-6);return value.toISOString().slice(0,10);});
 const [priceEnd,setPriceEnd]=useState(today);
 const [referencePrices,setReferencePrices]=useState<Row|null>(null);
 const [history,setHistory]=useState<Row|null>(null);const [historyLoading,setHistoryLoading]=useState(false);
 const [historyError,setHistoryError]=useState('');
 const [error,setError]=useState('');const [coverageError,setCoverageError]=useState('');
 const coveragePeriodTooLong=(new Date(end).getTime()-new Date(start).getTime())/86400000>1826;
 const refresh=async()=>{if(!cities.length)return;setLoading(true);setError('');setCoverageError('');setHistory(null);
  const params=new URLSearchParams({phase,start,end});
  for(const city of cities)params.append('municipalities',city);
  const coverageParams=new URLSearchParams({start,end});for(const city of cities)coverageParams.append('municipalities',city);
  const [p,c,s]=await Promise.allSettled([api('/catalogue-intelligent/products?'+params),
   coveragePeriodTooLong?Promise.resolve(null):api('/coverage/inventory?'+coverageParams),
   api('/catalogue-intelligent/candidates')]);
  if(p.status==='fulfilled')setProducts(p.value.records||[]);else{setProducts([]);setError((p.reason as Error).message);}
  if(c.status==='fulfilled'){setCoverage(c.value);if(coveragePeriodTooLong)setCoverageError('Cobertura não verificada para todo o período. Escolha até cinco anos para conferir as consultas.');}
  else{setCoverage(null);setCoverageError('Cobertura não verificada para todo o período. '+(c.reason as Error).message);}
  if(s.status==='fulfilled')setCandidates(s.value.records||[]);else{setCandidates([]);setError(previous=>[previous,(s.reason as Error).message].filter(Boolean).join(' '));}
  setLoading(false);};
 const showHistory=async(product:Row)=>{setHistoryError('');setHistory(null);
  if(coveragePeriodTooLong){setHistoryError('Para ver o histórico por município, escolha até cinco anos.');return;}
  setHistoryLoading(true);try{
  const params=new URLSearchParams({phase,start,end});for(const city of cities)params.append('municipalities',city);
  setHistory(await api('/catalogue-intelligent/products/'+product.id+'/history?'+params));
 }catch(reason){setHistoryError((reason as Error).message);}finally{setHistoryLoading(false);}};
 useEffect(()=>{if(cities.length)void refresh();},[cities.join('|')]);
 const reprocess=()=>void context.run(async()=>{let offset=0;let scanned=0;do{
  const page=await post('/catalogue-intelligent/reprocess?limit=500&offset='+offset);scanned+=page.scanned;
  offset=page.next_offset??-1;
 }while(offset>=0&&scanned<20000);await refresh();},'Itens reanalisados. As fontes e revisões anteriores foram preservadas.');
 const review=()=>void context.run(async()=>{if(!selected)return;
  await post('/catalogue-intelligent/products',{name,category,justification,evidence,
   members:selected.members.map((member:Row)=>({id:member.id,version:member.version})),confirmed:true});
  setSelected(null);await refresh();},'Produto revisado. A análise de viabilidade continua necessária.');
 const openOpportunities=()=>{let saved:Row={};try{saved=JSON.parse(sessionStorage.getItem('irps-opportunity-filters')||'{}');}catch{/* New recorte. */}
  sessionStorage.setItem('irps-opportunity-filters',JSON.stringify({...saved,dataset:'official',grouping:'canonical',phase,start,end,
   municipalities:cities,modalities:[]}));nav('oportunidades');};
 const checkPrices=()=>void context.run(async()=>{const params=new URLSearchParams({kind:priceKind,code:priceCode,
   code_type:priceKind==='servico'?'codigoItemCatalogo':codeType,start:priceStart,end:priceEnd});
   setReferencePrices(await api('/catalogue-intelligent/reference-prices?'+params));},'Consulta de preços concluída. Compare a especificação e a unidade antes de usar os valores.');
 const rows=(coverage?.records||[]).filter((row:Row)=>row.tasks||row.status==='connector_pending');
 return <Page title="Catálogo inteligente e cobertura" description="Agrupe itens somente após conferir unidade, embalagem e fonte. Veja o que foi consultado em cada município, sem presumir que todo o histórico foi encontrado." actions={<><Action to="oportunidades" secondary>Ver oportunidades</Action><Action to="coleta-oportunidades">Atualizar histórico</Action></>}>
  <Panel title="Escolha o recorte"><div className="opportunity-filter-grid">
   <Field label="Municípios" hint="Selecione os municípios que quer conferir."><select multiple value={cities} onChange={event=>setCities(Array.from(event.target.selectedOptions,option=>option.value))}>{context.cities.filter(city=>city.uf==='MG').map(city=><option key={city.ibge} value={city.ibge}>{city.name}/MG</option>)}</select></Field>
   <Field label="De"><input type="date" value={start} max={today()} onChange={event=>setStart(event.target.value)}/></Field>
   <Field label="Até"><input type="date" value={end} max={today()} onChange={event=>setEnd(event.target.value)}/></Field>
   <Field label="Situação"><select value={phase} onChange={event=>setPhase(event.target.value)}><option value="publicado_estimado">Publicado · estimado</option><option value="homologado">Homologado</option><option value="contratado">Contratado</option></select></Field>
  </div><div className="actions"><button className="button" disabled={loading||!cities.length} onClick={()=>void refresh()}>Conferir fontes e produtos</button><button className="button secondary" onClick={openOpportunities}>Ver oportunidades por produto</button></div></Panel>
  {error?<Notice tone="warning">{error}</Notice>:null}{loading?<p role="status">Conferindo as evidências do recorte…</p>:null}
  <Panel title="Produtos revisados"><Notice>O resumo considera somente os municípios selecionados. Compras anteriores não definem necessidades futuras.</Notice>
   {!products.length?<Empty title="Ainda não há produtos revisados" description="Reanalise os itens coletados e confira as sugestões antes de agrupá-los."/>:
    <DataTable<Row> rows={products} id={row=>row.id} caption="Produtos canônicos revisados" columns={[
     {label:'Produto',render:row=><><strong>{row.name}</strong><small>{row.category} · {row.unit}{row.package_signature?' · '+row.package_signature:''}</small></>},
     {label:'Histórico observado',render:row=><>{quantity(row.observed_records)} registros<small>{quantity(row.municipalities.length)} municípios · {quantity(row.active_months)} meses</small></>},
     {label:'Quantidade',render:row=><>{quantity(row.observed_quantity)}<small>{row.quantity_complete?'Nos registros exibidos':'Total parcial ou itens não comparáveis'}</small></>},
     {label:'Valor conhecido',render:row=>money(row.known_amount)},
     {label:'Detalhes',render:row=><button className="text-button" onClick={()=>void showHistory(row)}>Ver por município</button>}]}/>}
  </Panel>
  {historyLoading?<p role="status">Buscando registros por município…</p>:null}
  {historyError?<Notice tone="warning">Não foi possível abrir o histórico. {historyError}</Notice>:null}
  {history?<Panel title={'Histórico por município · '+history.product.name}>
   <Notice>{history.product.classification==='synthetic'?'Dados fictícios para teste.':'Registros de fontes públicas consultadas.'} Situação: {phase==='publicado_estimado'?'publicado · estimado':phase==='homologado'?'homologado':'contratado'}. Período: {start} a {end}. {history.product.unit}{history.product.package_signature?' · '+history.product.package_signature:''}. A coleta pode estar incompleta.</Notice>
   <DataTable<Row> rows={history.municipalities||[]} id={row=>row.municipality.ibge} caption="Registros observados por município no recorte" columns={[
    {label:'Município',render:row=><>{row.municipality.name}/{row.municipality.uf}<small>{row.observed_records?'Registros encontrados':'Sem registros encontrados neste recorte'} · {coverageLabel(row.coverage_state)}</small></>},
    {label:'Registros',render:row=><>{quantity(row.observed_records)} linhas<small>{row.distinct_processes==null?'Processos não identificados':quantity(row.distinct_processes)+' processos identificados'} · {row.observed_months.length} meses observados · {row.observed_years.join(', ')||'ano indisponível'}</small></>},
    {label:'Quantidade documentada',render:row=><>{quantity(row.observed_quantity)}<small>{row.observed_quantity==null?'Quantidade indisponível':history.product.unit}{!row.quantity_complete&&row.observed_quantity!=null?' · total parcial':''}{row.excluded_from_totals.length?' · há itens não comparáveis':''}</small></>},
    {label:'Valor documentado',render:row=><>{money(row.documented_amount)}<small>{row.unit_prices.length===1?'Preço unitário: '+money(row.unit_prices[0]):row.unit_prices.length>1?'Compare os preços nos documentos':'Preço unitário indisponível'}</small></>},
    {label:'Período e fonte',render:row=><>{row.first_observed||'Data indisponível'} a {row.last_observed||'—'}<small>{history.product.classification==='synthetic'?'Fonte fictícia de teste':row.evidence.length?<a href={row.evidence[0].url} target="_blank" rel="noreferrer">Abrir documento</a>:'Sem documento neste recorte'}</small></>}]}/>
   <div className="actions"><button className="button secondary" onClick={()=>{
    const matching=context.scenario?.snapshot.items.find((ref:Row)=>history.product.members.some((member:Row)=>member.id===ref.id&&member.version===ref.version));
    const city=context.scenario?.snapshot.participants.find((code:string)=>cities.includes(code));
    nav(matching?'quantidades':'itens',matching?{item:matching.id,...(city?{cidade:city}:{})}:{});
   }}>{context.scenario?.snapshot.items.some((ref:Row)=>history.product.members.some((member:Row)=>member.id===ref.id&&member.version===ref.version))?'Ver junto ao cálculo V4':'Escolher item no planejamento'}</button></div>
   <p className="subtle">Meses com registros não comprovam compras recorrentes. Sem consulta completa, ausência de registro não significa ausência de compra.</p>
  </Panel>:null}
  <Panel title="Sugestões que precisam de revisão" action={context.can('sources.sync')?<button className="button secondary" disabled={context.busy} onClick={reprocess}>Reanalisar itens coletados</button>:undefined}>
   <p className="subtle">As sugestões não juntam produtos automaticamente. Confira especificação, unidade e embalagem no documento de origem.</p>
   {!candidates.length?<Empty title="Nenhuma sugestão pronta" description="Colete itens oficiais ou refine os registros antes de criar grupos."/>:
    <DataTable<Row> rows={candidates} id={row=>row.members.map((member:Row)=>member.id).join('|')} caption="Possíveis equivalências técnicas" columns={[
     {label:'Descrição',render:row=><>{row.name}<small>{row.catalogue_code?'Código '+row.catalogue_code:'Sem código oficial informado'} · {row.package_signature||'embalagem não informada'}</small></>},
     {label:'Itens e cidades',render:row=><>{quantity(row.members.length)} itens<small>{quantity(row.municipalities.length)} municípios</small></>},
     {label:'Conferência',render:row=><Badge tone="amber">Revisão necessária</Badge>},
     {label:'Ação',render:row=><button className="text-button" onClick={()=>{setSelected(row);setName(row.name);setCategory('A confirmar');}}>Conferir itens</button>}]}/>}
  </Panel>
  {selected?<Panel title="Conferir antes de agrupar"><Notice tone="warning">Aproxime somente itens tecnicamente equivalentes. Esta revisão não aprova compra ou fornecimento.</Notice>
    <ul className="plain-list">{selected.members.map((member:Row)=><li key={member.id+member.version}>{member.original_description} · {member.original_unit} · <a href={member.source_url} target="_blank" rel="noreferrer">Ver fonte</a></li>)}</ul>
    <div className="form-grid"><Field label="Nome do produto"><input value={name} onChange={event=>setName(event.target.value)} minLength={5}/></Field><Field label="Categoria"><input value={category} onChange={event=>setCategory(event.target.value)} minLength={3}/></Field></div>
    <Field label="Por que estes itens são equivalentes?"><textarea value={justification} onChange={event=>setJustification(event.target.value)} minLength={20}/></Field>
    <Field label="Documento ou evidência conferida"><textarea value={evidence} onChange={event=>setEvidence(event.target.value)} minLength={10}/></Field>
    <div className="actions"><button className="button" disabled={context.busy||!context.can('opportunity.manage')||name.length<5||category.length<3||justification.length<20||evidence.length<10} onClick={review}>Confirmar equivalência</button><button className="button secondary" onClick={()=>setSelected(null)}>Cancelar</button></div>
  </Panel>:null}
  <Panel title="Compare preços públicos"><p className="subtle">Consulta pontual ao Compras.gov.br por código oficial. Ela ajuda na pesquisa de referência, mas não cobre todas as compras municipais.</p>
   <div className="opportunity-filter-grid"><Field label="Tipo"><select value={priceKind} onChange={event=>{setPriceKind(event.target.value);setCodeType('codigoItemCatalogo');}}><option value="material">Material</option><option value="servico">Serviço</option></select></Field>
    <Field label="Código do catálogo"><input inputMode="numeric" pattern="[0-9]+" value={priceCode} onChange={event=>setPriceCode(event.target.value)} placeholder="Ex.: 206504"/></Field>
    {priceKind==='material'?<Field label="Tipo de código"><select value={codeType} onChange={event=>setCodeType(event.target.value)}><option value="codigoItemCatalogo">Item específico</option><option value="codigoPdm">Família do material</option></select></Field>:null}
    <Field label="Preço desde"><input type="date" value={priceStart} max={today()} onChange={event=>setPriceStart(event.target.value)}/></Field>
    <Field label="Preço até"><input type="date" value={priceEnd} max={today()} onChange={event=>setPriceEnd(event.target.value)}/></Field>
   </div><button className="button secondary" disabled={context.busy||!context.can('sources.sync')||!/^\d{1,12}$/.test(priceCode)} onClick={checkPrices}>Consultar preços</button>
   {referencePrices?<><Notice>Confira data, local, unidade e descrição. Estes preços não são automaticamente comparáveis aos itens do seu planejamento.</Notice>
    <DataTable<Row> rows={referencePrices.records||[]} id={row=>[row.purchase_id,row.item_number].join(':')} caption="Preços documentados na consulta" columns={[
     {label:'Descrição',render:row=><>{row.description}<small>{row.unit||'Unidade não informada'} · {row.purchase_date||'Data não informada'}</small></>},
     {label:'Órgão e local',render:row=><>{row.agency||'Órgão não informado'}<small>{row.state||'Local não informado'}</small></>},
     {label:'Quantidade',render:row=>quantity(row.quantity)},
     {label:'Preço unitário',render:row=>money(row.unit_price)}]}/><a href={referencePrices.url} target="_blank" rel="noreferrer">Abrir consulta original no Compras.gov.br</a></>:null}
  </Panel>
  <Panel title="O que a coleta comprovou"><Notice>O percentual abaixo mede páginas planejadas e conciliadas no recorte. Ele não mede todas as compras do município, nem a completude de resultados, pagamentos ou consumo.</Notice>
   {coverageError?<Notice tone="warning">{coverageError}</Notice>:null}
   <DataTable<Row> rows={rows} id={row=>[row.municipality_ibge,row.provider,row.modality].join(':')} caption="Cobertura por município, fonte, modalidade e situação" columns={[
    {label:'Município',render:row=><>{row.municipality_name}<small>{row.municipality_ibge}</small></>},
    {label:'Fonte e situação',render:row=><>{row.source_label}<small>{row.phase} · {row.modality?'modalidade '+row.modality:'todas ou não aplicável'}</small></>},
    {label:'Consultas',render:row=><>{quantity(row.completed_tasks)} de {quantity(row.tasks)} tarefas<small>{row.request_completion_ratio==null?'Sem percentual verificável':(Number(row.request_completion_ratio)*100).toFixed(0)+'% das páginas planejadas'}</small></>},
    {label:'Evidência',render:row=>row.proof?.length?<a href={row.proof[0].url} target="_blank" rel="noreferrer">Abrir consulta</a>:'Ainda não consultada'}]}/>
  </Panel>
  <Panel title="Órgãos identificados no recorte"><Notice>Estes órgãos aparecem nos registros consultados. Um órgão ausente pode ter dados em outra fonte ou período.</Notice>
   <DataTable<Row> rows={coverage?.buyer_inventory||[]} id={row=>[row.buyer_id,row.provider,row.phase,row.modality].join(':')} caption="Órgãos, CNPJ e situações observados" columns={[
    {label:'Órgão',render:row=><>{row.name}<small>CNPJ {row.cnpj||'não informado'} · {row.municipality_ibge}</small></>},
    {label:'Fonte e situação',render:row=><>{row.provider}<small>{row.phase} · {row.modality?'modalidade '+row.modality:'modalidade não informada'}</small></>},
    {label:'Registros',render:row=><>{quantity(row.observed_facts)}<small>{quantity(row.observed_processes)} processos observados</small></>},
    {label:'Período observado',render:row=><>{row.earliest||'Não informado'} a {row.latest||'Não informado'}</>} ]}/>
  </Panel>
 </Page>;
}
