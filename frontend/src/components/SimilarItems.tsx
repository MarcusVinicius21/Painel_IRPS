import {useState} from 'react';
import {useResource} from '../api';
import type {Row} from '../api';
import {Notice,Empty} from './ui';
import './similar-items.css';

export function SimilarItems({product,ambiguous=false}:{product:string;ambiguous?:boolean}){
 const [offset,setOffset]=useState(0),resource=useResource(product?'/director/products/'+encodeURIComponent(product)+'/similar?offset='+offset+'&limit=20':null),data=resource.data;
 if(!product)return <Empty title={ambiguous?'Há mais de uma equivalência vinculada':'Sem equivalência revisada para este item'} description={ambiguous?'Escolha o produto no campo Histórico tecnicamente vinculado após conferir as evidências.':'A semelhança do nome não comprova equivalência técnica.'}/>;
 if(resource.loading)return <p role="status">Conferindo equivalências revisadas…</p>;
 if(resource.error)return <Notice tone="warning">Não foi possível conferir as equivalências. {resource.error}</Notice>;
 if(!data)return null;
 return <section className="similar-items-content" aria-label="Equivalência técnica revisada">
  <Notice>{data.notice}</Notice>{data.classification==='synthetic'?<p role="note">Equivalência fictícia para testes.</p>:null}
  <h3>{data.name}</h3><p>Unidade: {data.unit}. Embalagem: {data.package_signature||'Não informada'}.</p>
  <details><summary>Responsável, versão e provas da equivalência</summary><p>Versão da revisão: {data.review.version_id}</p><p>Responsável identificado: {data.review.reviewed_by} · Data: {data.review.reviewed_at}</p><p>Justificativa: {data.review.justification}</p><p>Evidência da revisão: {data.review.evidence}</p></details>
  {data.records.length?<ul>{data.records.map((r:Row)=><li key={r.id+':'+r.version}><strong>{r.name}</strong><small>Item {r.id} · Versão {r.version} · Unidade original: {r.unit}</small>{r.fact_id?<a href={'#/processo?id='+encodeURIComponent(r.fact_id)} target="_blank" rel="noopener noreferrer">Abrir registro deste item · versão {r.version}</a>:<p>Sem registro atual disponível para esta versão.</p>}{/^https?:\/\//i.test(r.url||'')?<a href={r.url} target="_blank" rel="noopener noreferrer">Conferir documento de origem</a>:null}<small>Consulta: {r.consulted_at||'Não informada'}</small></li>)}</ul>:<Empty title="Sem membros disponíveis nesta página" description="Volte à página anterior para conferir a equivalência."/>}
  <div className="actions"><button className="button secondary" disabled={offset===0} onClick={()=>setOffset(n=>Math.max(0,n-20))}>Página anterior de equivalências</button><span>{offset+1}–{Math.min(offset+20,data.total)} de {data.total} membros revisados</span><button className="button secondary" disabled={offset+20>=data.total} onClick={()=>setOffset(n=>n+20)}>Próxima página de equivalências</button></div>
 </section>;
}
