import {useEffect,useState} from 'react';
import {Search,PackageSearch,ArrowUpRight} from 'lucide-react';
import {api,post,useApi,useResource,money,quantity,phases} from '../api';
import type {Row} from '../api';
import {Page,Panel,Field,Notice,Empty,Badge,DataTable,Link,IconProps} from '../components/ui';
import './portfolio.css';

type Filters={group:string;q:string;kind:string;technical:string;active:string;subgroup:string;municipalities:string[];start:string;end:string;phase:string};
const initial:Filters={group:'01',q:'',kind:'',technical:'',active:'',subgroup:'',municipalities:[],start:'2025-10-01',end:'2026-09-30',phase:'homologado'};
const tabs=[['descricao','Descrição'],['precos','Preços nacionais'],['municipal','Compras dos municípios'],['fornecedores','Fornecedores verificados'],['fontes','Fontes e cobertura']];
const status:Record<string,string>={available:'Consultas disponíveis',partial:'Informação parcial',not_collected:'Ainda não consultado',blocked:'Consulta bloqueada',needs_review:'Precisa de conferência',optional:'Complemento opcional'};
const technical=(v:string)=>v==='DIRECT_TECHNICAL'?'Correspondência técnica direta':'Candidato para revisão técnica';
function ResourceState({resource,children,empty='Não encontramos registros neste recorte.'}:{resource:ReturnType<typeof useResource>;children:React.ReactNode;empty?:string}){
 if(resource.loading)return <p role="status">Consultando informações locais…</p>;
 if(resource.error)return <Notice tone="amber">{resource.error} Os demais dados continuam disponíveis.</Notice>;
 if(!resource.data)return <Empty title="Escolha um item" description={empty}/>;
 return <>{children}</>;
}
function ServerPages({offset,next,onChange,label}:{offset:number;next:number|null;onChange:(n:number)=>void;label:string}){
 return <nav className="pagination" aria-label={label}><button className="button secondary" disabled={!offset} onClick={()=>onChange(Math.max(0,offset-25))}>Anterior</button><span>Resultados a partir de {offset+1}</span><button className="button secondary" disabled={next==null} onClick={()=>next!=null&&onChange(next)}>Próxima</button></nav>;
}
export function Portfolio(){
 const ctx=useApi();const [filters,setFilters]=useState<Filters>(initial),[draft,setDraft]=useState<Filters>(initial),[ready,setReady]=useState(false);
 const [tab,setTab]=useState('descricao'),[selected,setSelected]=useState<Row|null>(null),[offset,setOffset]=useState(0),[historyOffset,setHistoryOffset]=useState(0);
 const [pricePage,setPricePage]=useState(1),[priceCursors,setPriceCursors]=useState<Record<number,string>>({}),[codeOnly,setCodeOnly]=useState(false),[buyer,setBuyer]=useState(''),[buyerDraft,setBuyerDraft]=useState('');
 const [comparison,setComparison]=useState(false);
 useEffect(()=>{let active=true;void api('/portfolio/preferences').then(r=>{if(active){const saved={...initial,...r.payload,kind:r.payload.kind||'',technical:r.payload.technical||'',active:r.payload.active==null?'':String(r.payload.active),subgroup:r.payload.subgroup||''};setFilters(saved);setDraft(saved);setReady(true);}}).catch(e=>{if(active){ctx.setToast(e.message);setReady(true);}});return()=>{active=false;};},[ctx.setToast]);
 const groups=useResource('/portfolio/groups');
 const codeQuery=new URLSearchParams({group:filters.group,q:filters.q,offset:String(offset),limit:'25'});
 if(filters.active)codeQuery.set('active',filters.active);if(filters.subgroup)codeQuery.set('subgroup',filters.subgroup);
 if(filters.kind)codeQuery.set('kind',filters.kind);if(filters.technical)codeQuery.set('technical',filters.technical);
 const codes=useResource(ready?'/portfolio/codes?'+codeQuery:null);
 const historyQuery=new URLSearchParams({group:filters.group,start:filters.start,end:filters.end,phase:filters.phase,offset:String(historyOffset),limit:'25'});
 filters.municipalities.forEach(c=>historyQuery.append('municipalities',c));if(buyer)historyQuery.set('buyer',buyer);
 if(codeOnly&&selected){historyQuery.set('code',selected.code);historyQuery.set('snapshot',selected.snapshot_id);}
 if(tab==='fornecedores')historyQuery.set('suppliers_only','true');
 const history=useResource(ready&&['municipal','fornecedores'].includes(tab)?'/portfolio/history?'+historyQuery:null);
 const compareQuery=new URLSearchParams(historyQuery);compareQuery.delete('offset');compareQuery.delete('suppliers_only');compareQuery.set('offset','0');
 const compared=useResource(ready&&comparison&&tab==='municipal'?'/portfolio/comparison?'+compareQuery:null);
 const priceQuery=new URLSearchParams({kind:selected?.kind==='CATSER'?'servico':'material',code:selected?.code||'',start:filters.start,end:filters.end,page:String(pricePage)});
 if(priceCursors[pricePage])priceQuery.set('cursor',priceCursors[pricePage]);
 const prices=useResource(tab==='precos'&&selected?'/catalogue-intelligent/consolidated-prices?'+priceQuery:null);
 const source=useResource(tab==='fontes'?'/portfolio/sources':null);
 const coverageQuery=new URLSearchParams({start:filters.start,end:filters.end});filters.municipalities.forEach(c=>coverageQuery.append('municipalities',c));
 const coverage=useResource(tab==='fontes'?'/portfolio/coverage?'+coverageQuery:null);
 const enrichment=useResource(tab==='descricao'&&selected?'/national-catalogue/'+selected.snapshot_id+'/'+selected.code:null);
 const group=groups.data?.records.find((g:Row)=>g.code===filters.group);
 const apply=(next:Filters)=>{setFilters(next);setDraft(next);setOffset(0);setHistoryOffset(0);setSelected(null);setCodeOnly(false);setPricePage(1);setPriceCursors({});void ctx.run(async()=>{await post('/portfolio/preferences',{...next,kind:next.kind||null,technical:next.technical||null,active:next.active===''?null:next.active==='true'});},'Filtros salvos.');};
 const choose=(row:Row)=>{setSelected(row);setPricePage(1);setPriceCursors({});setCodeOnly(false);};
 return <Page title="Portfólio CONSORMULTI" description="Escolha um grupo, confira preços e explore compras municipais." icon={<PackageSearch {...IconProps}/>} actions={<Link className="button secondary" to="inteligencia">Consultar catálogo nacional <ArrowUpRight {...IconProps}/></Link>}>
  <Notice>Candidatos técnicos não representam oferta confirmada. Compras observadas não comprovam necessidade futura.</Notice>
  <div className="portfolio-layout">
   <aside className="portfolio-groups"><Panel title="Vinte frentes de atuação"><ResourceState resource={groups}>
    <nav aria-label="Grupos do portfólio">{groups.data?.records.map((g:Row)=><button type="button" key={g.code} aria-pressed={g.code===filters.group} onClick={()=>apply({...filters,group:g.code,q:'',subgroup:''})}><span>{g.code}</span><div><strong>{g.name}</strong><small>{quantity(Number(g.direct_codes)+Number(g.review_codes))} códigos candidatos</small></div></button>)}</nav>
    {!groups.loading&&!groups.error&&!groups.data?.records.length?<Empty title="Portfólio ainda não preparado" description="O catálogo nacional continua disponível."/>:null}
   </ResourceState></Panel></aside>
   <div className="portfolio-content">
    <Panel title={group?.name||'Escolha um grupo'}>
     <p>{group?.scope}</p><p className="subtle">{group?.commercial_confirmed||'0'} códigos com confirmação comercial registrada.</p>
     <form className="portfolio-filters" onSubmit={e=>{e.preventDefault();apply(draft);}}>
      <Field label="Código ou descrição"><input value={draft.q} onChange={e=>setDraft({...draft,q:e.target.value})} placeholder="Ex.: automóvel, café ou um código"/></Field>
      <Field label="Catálogo"><select value={draft.kind} onChange={e=>setDraft({...draft,kind:e.target.value})}><option value="">Materiais e serviços</option><option>CATMAT</option><option>CATSER</option></select></Field>
      <Field label="Correspondência"><select value={draft.technical} onChange={e=>setDraft({...draft,technical:e.target.value})}><option value="">Diretos e para revisão</option><option value="DIRECT_TECHNICAL">Direta técnica</option><option value="NEEDS_TECH_REVIEW">Revisão técnica</option></select></Field>
      <Field label="Situação do código"><select value={draft.active} onChange={e=>setDraft({...draft,active:e.target.value})}><option value="">Ativos e inativos</option><option value="true">Ativos</option><option value="false">Inativos</option></select></Field>
      <Field label="Subgrupo técnico"><select value={draft.subgroup} onChange={e=>setDraft({...draft,subgroup:e.target.value})}><option value="">Todos os subgrupos</option>{(group?.subgroups||[]).map((v:string)=><option key={v} value={v}>{v.replaceAll('_',' ')}</option>)}</select></Field>
      <Field label="Desde"><input type="date" value={draft.start} onChange={e=>setDraft({...draft,start:e.target.value})}/></Field>
      <Field label="Até"><input type="date" value={draft.end} onChange={e=>setDraft({...draft,end:e.target.value})}/></Field>
      <Field label="Situação da compra"><select value={draft.phase} onChange={e=>setDraft({...draft,phase:e.target.value})}>{['publicado_estimado','homologado','contratado','empenhado','liquidado','pago'].map(v=><option key={v} value={v}>{phases[v]}</option>)}</select></Field>
      <Field label="Municípios" hint="Sem seleção: todos os municípios cadastrados."><select multiple value={draft.municipalities} onChange={e=>setDraft({...draft,municipalities:Array.from(e.target.selectedOptions,x=>x.value)})}>{ctx.cities.map(c=><option key={c.ibge} value={c.ibge}>{c.name}/{c.uf}</option>)}</select></Field>
      <button className="button" disabled={!ready||ctx.busy}><Search {...IconProps}/>Aplicar e salvar filtros</button>
     </form>
    </Panel>
    <nav className="portfolio-tabs" aria-label="Informações do grupo">{tabs.map(([id,title])=><button type="button" key={id} className={tab===id?'active':''} aria-pressed={tab===id} onClick={()=>setTab(id)}>{title}</button>)}</nav>
    {tab==='descricao'?<Panel title="Códigos e especificações"><ResourceState resource={codes}>
     <p>{quantity(codes.data?.total)} códigos neste filtro. A confirmação comercial continua separada.</p>
     <DataTable<Row> rows={codes.data?.records||[]} id={r=>r.snapshot_id+':'+r.code} pageSize={25} caption="Códigos candidatos do portfólio" columns={[
      {label:'Código e descrição',render:r=><><strong>{r.kind} {r.code}</strong><p>{r.name}</p><small>{r.active?'Ativo':'Inativo'} · {r.subgroup}</small></>},
      {label:'O que foi conferido',render:r=><><Badge>{technical(r.technical_status)}</Badge><p>{r.reason}</p><small>Oferta comercial pendente</small></>},
      {label:'Consultar',render:r=><button className="button secondary" onClick={()=>choose(r)}>Abrir ficha {r.code}</button>},]}/>
     <ServerPages offset={offset} next={codes.data?.next_offset??null} onChange={setOffset} label="Páginas do catálogo prioritário"/>
     {!codes.data?.records.length?<Empty title="Nenhum candidato neste filtro" description="Pesquise no catálogo nacional ou ajuste o grupo. Nenhum código foi apagado."/>:null}
    </ResourceState>{selected?<section className="portfolio-selected" aria-label="Item selecionado"><h3>{selected.kind} {selected.code}</h3><p>{selected.name}</p><p>{selected.reason}</p><ResourceState resource={enrichment}>{enrichment.data?<p>Descrição preservada do catálogo nacional. Unidade de fornecimento: confira o registro da compra.</p>:null}</ResourceState><button className="button" onClick={()=>setTab('precos')}>Consultar preços nacionais</button><button className="button secondary" onClick={()=>{setCodeOnly(true);setTab('municipal');}}>Histórico vinculado a este código</button><Link className="button secondary" to={'inteligencia?codigo='+encodeURIComponent(selected.code)+'&catalogo='+encodeURIComponent(selected.snapshot_id)}>Abrir planejamento existente</Link></section>:null}</Panel>:null}
    {tab==='precos'?<Panel title="Preços nacionais documentados"><Notice>Preços nacionais não são automaticamente compras dos municípios selecionados. Unidade e especificação exigem conferência.</Notice>{!selected?<Empty title="Escolha um código na guia Descrição" description="A consulta usa o código e a versão escolhidos."/>:<><h3>{selected.kind} {selected.code}</h3><ResourceState resource={prices}><DataTable<Row> rows={prices.data?.records||[]} id={r=>r.source_key+':'+r.source_record_sha256} pageSize={10} caption="Preços nacionais oficiais consolidados" columns={[
      {label:'Data e órgão',render:r=><>{r.purchase_date}<p>{r.agency||r.purchasing_unit||'Órgão não informado'}</p></>},
      {label:'Descrição e unidade',render:r=><>{r.description}<small>{r.unit||'Unidade não informada'}</small></>},
      {label:'Quantidade documentada',render:r=>quantity(r.quantity)}, {label:'Preço da unidade',render:r=>money(r.unit_price)},
      {label:'Fonte',render:r=><a target="_blank" rel="noreferrer" href={r.source_url}>Arquivo oficial · {r.source_month}</a>},]}/>
      {!prices.data?.records.length?<Empty title="Não encontramos preço neste recorte" description="O histórico municipal permanece disponível na outra guia."/>:null}
      <div className="pagination"><button className="button secondary" disabled={pricePage<=1} onClick={()=>setPricePage(p=>p-1)}>Preços anteriores</button><span>Página {pricePage}</span><button className="button secondary" disabled={!prices.data?.has_next_page} onClick={()=>{setPriceCursors(c=>({...c,[pricePage+1]:prices.data?.next_cursor}));setPricePage(p=>p+1);}}>Próximos preços</button></div>
     </ResourceState></>}</Panel>:null}
    {['municipal','fornecedores'].includes(tab)?<Panel title={tab==='municipal'?'Registros municipais e documentos':'Fornecedores com evidência'}>
     <Notice>{codeOnly?'Somente vínculos comprovados com o código selecionado.':'Candidatos do grupo por descrição. Não estão associados automaticamente a um código CATMAT/CATSER.'} Fase: {phases[filters.phase]}.</Notice>
     <div className="portfolio-inline"><Field label="CNPJ do órgão comprador"><input value={buyerDraft} maxLength={14} inputMode="numeric" onChange={e=>setBuyerDraft(e.target.value.replace(/\D/g,''))} placeholder="Todos os órgãos municipais"/></Field><button className="button secondary" disabled={buyerDraft.length!==0&&buyerDraft.length!==14} onClick={()=>{setBuyer(buyerDraft);setHistoryOffset(0);}}>Filtrar órgão</button><button className="button secondary" disabled={!selected} onClick={()=>{setCodeOnly(v=>!v);setHistoryOffset(0);}}>{codeOnly?'Ver candidatos do grupo':'Restringir ao código selecionado'}</button><button className="button secondary" onClick={()=>setComparison(v=>!v)}>Comparar identidades</button></div>
     <ResourceState resource={history}><DataTable<Row> rows={(history.data?.records||[]).filter((r:Row)=>tab!=='fornecedores'||r.supplier)} id={r=>r.id} pageSize={25} caption="Compras municipais observadas, sem soma entre fases" columns={[
      {label:'Município e órgão',render:r=><><strong>{r.municipality_name}</strong><p>{r.buyer_name}</p><small>CNPJ {r.buyer_cnpj}</small></>},
      {label:'Item e situação',render:r=><><p>{r.description}</p><small>{r.phase==='empenhado'&&!r.financial_execution_proven?'Instrumento de empenho PNCP; execução não comprovada':phases[r.phase]} · {r.event_date}</small><Badge>{r.group_match_state==='description_candidate_requires_review'?'Candidato: revisar vínculo':'Vínculo documentado'}</Badge><small>Processo {r.obligation_id}</small></>},
      {label:'Quantidade e unidade',render:r=><>{quantity(r.quantity)}<small>{r.unit||'Unidade não informada'}</small></>},
      {label:'Valor documentado',render:r=><>{r.currency==='BRL'?money(r.amount):'Moeda precisa de conferência'}<small>Preço unitário: {r.currency==='BRL'?money(r.unit_price):'Não comparável'}</small></>},
      {label:'Fornecedor e fonte',render:r=><>{r.supplier?<p>{r.supplier.name} · {r.supplier.cnpj}<small>{r.supplier_role}</small></p>:<p>Fornecedor não identificado nesta situação.</p>}<a target="_blank" rel="noreferrer" href={r.source_url}>Abrir evidência oficial</a><small>Consultado em {new Date(r.consulted_at).toLocaleString('pt-BR')}</small><Link to={'processo?id='+r.id}>Ver registro no IRPS</Link></>},]}/>
      {!history.data?.records.length?<Empty title="Sem vínculo encontrado neste recorte" description="Isso não comprova ausência de compras. Consulte candidatos do grupo ou confira a cobertura."/>:null}
      <ServerPages offset={historyOffset} next={history.data?.next_offset??null} onChange={setHistoryOffset} label="Páginas do histórico municipal"/>
     </ResourceState>
     {comparison&&tab==='municipal'?<ResourceState resource={compared}><Panel title="Comparação por item, versão e unidade"><Notice>Não há total geral entre especificações diferentes. Quantidade observada não é necessidade V4.</Notice><DataTable<Row> rows={compared.data?.records||[]} id={r=>[r.municipality_ibge,r.buyer_cnpj,r.item_id,r.item_version,r.unit,r.phase,r.provider,r.currency].join(':')} pageSize={25} caption="Comparação de identidades municipais" columns={[
      {label:'Identidade',render:r=><>{r.buyer_name}<p>{r.description}</p><small>Versão {r.item_version} · {r.unit}</small></>},
      {label:'Quantidade observada',render:r=>quantity(r.observed_quantity)}, {label:'Valor documentado',render:r=>r.currency==='BRL'?money(r.documented_amount):'Moeda a conferir'},
      {label:'Preço comparável',render:r=>money(r.comparable_unit_price_median)},{label:'Meses observados',render:r=><>{r.observed_months.join(', ')}<small>Cobertura parcial; sem previsão.</small></>},]}/></Panel></ResourceState>:null}
    </Panel>:null}
    {tab==='fontes'?<><Panel title="Fontes e caminhos de consulta"><ResourceState resource={source}>{source.data?.records.map((r:Row)=><article className="portfolio-source" key={r.provider}><Badge>{status[r.state]||'Conferir fonte'}</Badge><h3>{r.provider.replaceAll('_',' ')}</h3><p>{r.message}</p><a target="_blank" rel="noreferrer" href={r.url}>Abrir fonte de referência</a></article>)}</ResourceState><Link className="button secondary" to="coleta-oportunidades">Retomar coletas existentes</Link><p>Use a fila existente. Não abra uma segunda coleta para o mesmo recorte.</p></Panel><Panel title="Doze meses de consultas por município"><Notice>Percentuais medem somente requisições planejadas, não todas as compras ou o mercado.</Notice><ResourceState resource={coverage}><DataTable<Row> rows={coverage.data?.records||[]} id={r=>r.municipality_ibge+r.month+r.provider} pageSize={12} caption="Cobertura das consultas municipais por mês e fonte" columns={[
      {label:'Município e mês',render:r=><>{ctx.cities.find(c=>c.ibge===r.municipality_ibge)?.name||r.municipality_ibge}<small>{r.month}</small></>},
      {label:'Fonte e recorte',render:r=><>{r.provider}<small>{r.period_basis==='validity_overlap'?'Vigência da ata':r.period_basis.includes('discovery')?'Descoberta pelo documento de origem':'Período específico da fonte'}</small></>},
      {label:'Estado',render:r=><Badge>{status[r.coverage_status]||'Precisa de conferência'}</Badge>},
      {label:'Última consulta',render:r=>r.last_sync?new Date(r.last_sync).toLocaleString('pt-BR'):'Não consultado'},
      {label:'Requisições comprovadas',render:r=><>{r.verified_requests} de {r.expected_pages??'total não verificado'}<small>{r.request_reconciliation_pct==null?'Sem percentual confiável':quantity(r.request_reconciliation_pct)+'% do recorte de consultas'}</small></>},]}/></ResourceState></Panel></>:null}
   </div>
  </div>
 </Page>;
}
