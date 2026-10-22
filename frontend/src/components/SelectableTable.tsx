import {useState,useRef,useEffect} from 'react';
import {ChevronLeft,ChevronRight,ArrowUpDown} from 'lucide-react';
import {route,param} from '../api';
import {Empty,IconProps} from './ui';
import type {Col,TableSelection} from './ui';

function Checkbox({label,checked,mixed=false,onChange}:{label:string;checked:boolean;mixed?:boolean;onChange:()=>void}){
 const ref=useRef<HTMLInputElement>(null);useEffect(()=>{if(ref.current)ref.current.indeterminate=mixed;},[mixed]);
 return <input ref={ref} type="checkbox" aria-label={label} checked={checked} aria-checked={mixed?'mixed':checked} onChange={onChange}/>;
}

/** Bounded client-side pagination of the complete rows supplied by the caller. No aggregation. */
export function SelectableTable<T>({rows,columns,id,pageSize=8,caption='Registros da demonstração',selection,pageSizes=[8,20,50,118]}:{rows:T[];columns:Col<T>[];id:(r:T)=>string;pageSize?:number;caption?:string;selection?:TableSelection<T>;pageSizes?:number[]}){
 const [pg,setPg]=useState(Number(route().params.get('pagina')||1)),[size,setSize]=useState(pageSize),[sort,setSort]=useState(-1),[ascending,setAscending]=useState(true);
 const pages=Math.max(1,Math.ceil(rows.length/size)),page=Math.max(1,Number.isFinite(pg)?Math.min(pg,pages):1);
 const sortValue=columns[sort]?.sort;
 const ordered=!sortValue?rows:[...rows].sort((a,b)=>{const x=sortValue(a),y=sortValue(b);return (typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y),'pt-BR'))*(ascending?1:-1);});
 const shown=ordered.slice((page-1)*size,page*size),visible=shown.map(id),selected=new Set(selection?.selected||[]);
 const all=visible.length>0&&visible.every(key=>selected.has(key)),some=visible.some(key=>selected.has(key));
 const toggle=(key:string)=>selection?.onChange(selected.has(key)?[...selected].filter(x=>x!==key):[...selected,key]);
 const togglePage=()=>selection?.onChange(all?[...selected].filter(key=>!visible.includes(key)):[...new Set([...selected,...visible])]);
 const move=(n:number)=>{setPg(n);param('pagina',String(n));};
 const numbers=Array.from({length:pages},(_,i)=>i+1).filter(n=>n===1||n===pages||Math.abs(n-page)<=1);
 if(!rows.length)return <Empty/>;
 return <><div className="table-scroll desktop-records" tabIndex={0} role="region" aria-label={caption}><table><caption className="sr-only">{caption}</caption><thead><tr>
  {selection?<th className="table-selection-cell" scope="col"><Checkbox label={selection.pageAction||"Selecionar municípios desta página para o estudo"} checked={all} mixed={!all&&some} onChange={togglePage}/></th>:null}
  {columns.map((c,i)=><th key={c.label} scope="col" aria-sort={sort===i?(ascending?'ascending':'descending'):undefined}>{c.sort?<button className="sort-button" onClick={()=>{setSort(i);setAscending(sort===i?!ascending:true);}}>{c.label}<ArrowUpDown {...IconProps} size={13}/></button>:c.label}</th>)}
 </tr></thead><tbody>{shown.map(r=><tr key={id(r)}>{selection?<td className="table-selection-cell"><Checkbox label={selection.rowAction?selection.rowAction+' '+selection.label(r):'Incluir '+selection.label(r)+' no estudo'} checked={selected.has(id(r))} onChange={()=>toggle(id(r))}/></td>:null}{columns.map(c=><td key={c.label}>{c.render(r)}</td>)}</tr>)}</tbody></table></div>
 <div className="mobile-records">{shown.map(r=><article className="mobile-record" key={id(r)}>{selection?<label className="table-mobile-selection"><Checkbox label={selection.rowAction?selection.rowAction+' '+selection.label(r):'Incluir '+selection.label(r)+' no estudo'} checked={selected.has(id(r))} onChange={()=>toggle(id(r))}/>{selection.mobileAction||'Incluir no estudo'}</label>:null}<dl>{columns.map(c=><div key={c.label}><dt>{c.label}</dt><dd>{c.render(r)}</dd></div>)}</dl></article>)}</div>
 <div className="pagination pagination-expanded"><span>{rows.length.toLocaleString('pt-BR')} registros · página {page} de {pages}</span><div className="pagination-numbers"><button className="icon-button" aria-label="Página anterior" disabled={page<=1} onClick={()=>move(page-1)}><ChevronLeft {...IconProps}/></button>{numbers.map((n,i)=><span key={n}>{i>0&&n-numbers[i-1]>1?<span className="pagination-gap" aria-hidden="true">…</span>:null}<button className="icon-button" aria-label={'Ir para página '+n} aria-current={n===page?'page':undefined} onClick={()=>move(n)}>{n}</button></span>)}<button className="icon-button" aria-label="Próxima página" disabled={page>=pages} onClick={()=>move(page+1)}><ChevronRight {...IconProps}/></button></div><label className="table-page-size">Itens por página<select aria-label="Itens por página" value={size} onChange={e=>{setSize(Number(e.target.value));move(1);}}>{pageSizes.map(n=><option key={n} value={n}>{n}</option>)}</select></label></div></>;
}
