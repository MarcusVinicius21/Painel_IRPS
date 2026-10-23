import {useState} from 'react';
import {useApi,useResource,post} from '../api';
import type {Row} from '../api';
import {Panel,Notice,Field} from './ui';

/** Exact source identities; never matches descriptions to CATMAT automatically. */
export function ObservedItems({onSelect}:{onSelect:(item:Row,product:string)=>void}){
 const c=useApi(),[query,setQuery]=useState(''),[term,setTerm]=useState('');
 const data=useResource('/director/observed-items?q='+encodeURIComponent(term));
 return <Panel title="Itens encontrados nas fontes oficiais">
  <Notice>A localização do órgão não comprova compra da prefeitura. Confira o comprador na fonte.</Notice>
  <form className="search-form" onSubmit={e=>{e.preventDefault();setTerm(query);}}><Field label="Buscar nos itens consultados"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Descrição do produto ou serviço"/></Field><button className="button secondary">Buscar itens</button></form>
  {data.loading?<p role="status">Consultando os itens disponíveis…</p>:data.error?<Notice tone="warning">{data.error}</Notice>:!data.data?.records.length?<p>Nenhum item encontrado neste recorte. Confira as fontes consultadas.</p>:<ul className="observed-item-list">{data.data.records.map((item:Row)=><li key={item.id} data-fact-id={item.id}><strong>{item.description}</strong><p>{item.municipality_name} · {item.unit} · {item.event_date}</p><div className="actions"><a href={item.source_url} target="_blank" rel="noreferrer">Ver item na fonte oficial</a><button className="button secondary" disabled={c.busy} onClick={()=>void c.run(async()=>{const p=await post('/director/observed-items/'+item.id+'/identity');onSelect(item,p.id);},'Item identificado pela fonte e versão. Confira o histórico.')}>Analisar este item</button></div></li>)}</ul>}
  <p className="subtle">A análise preserva a identidade original. Outros itens não são agrupados automaticamente.</p>
 </Panel>;
}
