import {useState} from 'react';
import type {Row} from '../api';
import {Field} from './ui';

/** Localiza opções; nunca remove silenciosamente participantes já selecionados. */
export function TerritorySelector({cities,selected,uf,onUf,onSelect}:{cities:Row[];selected:string[];uf:string;onUf:(v:string)=>void;onSelect:(v:string[])=>void}){
 const [mode,setMode]=useState('todos'),[query,setQuery]=useState('');
 const states=[...new Set(cities.map(c=>String(c.uf)))].sort();
 const visible=cities.filter(c=>selected.includes(c.ibge)||((!uf||c.uf===uf)&&(!query||String(c.name).toLocaleLowerCase('pt-BR').includes(query.toLocaleLowerCase('pt-BR'))||c.ibge.includes(query))));
 return <fieldset className="territory-selector"><legend>Abrangência geográfica</legend>
  <Field label="Abrangência no cadastro"><select value={uf} onChange={e=>{onUf(e.target.value);setMode(e.target.value?'estado':'todos');}}><option value="">Brasil · cadastro disponível</option>{states.map(s=><option key={s} value={s}>{s} · municípios cadastrados</option>)}</select></Field>
  <div className="territory-segments" role="group" aria-label="Localizar municípios"><button type="button" aria-pressed={mode==='todos'} onClick={()=>{setMode('todos');onUf('');setQuery('');}}>Todos</button><button type="button" aria-pressed={mode==='estado'} onClick={()=>setMode('estado')}>Estado</button><button type="button" aria-pressed={mode==='municipios'} onClick={()=>setMode('municipios')}>Municípios</button></div>
  {mode==='estado'?<Field label="Localizar municípios por UF"><select value={uf} onChange={e=>onUf(e.target.value)}><option value="">Todas no cadastro</option>{states.map(s=><option key={s}>{s}</option>)}</select></Field>:null}
  {mode==='municipios'?<Field label="Localizar município"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Nome ou código IBGE"/></Field>:null}
  <Field label="Municípios para o estudo" hint="Localizar não altera a seleção. Até 118 por consulta."><select multiple value={selected} onChange={e=>onSelect(Array.from(e.target.selectedOptions,o=>o.value))}>{visible.map(c=><option key={c.ibge} value={c.ibge}>{c.name}/{c.uf}</option>)}</select></Field>
  <details><summary>Cadastro, seleção e cobertura</summary><p>O recorte usa municípios cadastrados. Isso não comprova cobertura nacional nem vínculo consorcial. Municípios selecionados permanecem visíveis ao mudar a busca.</p></details>
 </fieldset>;
}
