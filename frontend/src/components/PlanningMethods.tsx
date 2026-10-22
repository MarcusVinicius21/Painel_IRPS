import {UsersRound,Scale} from 'lucide-react';
import {useState} from 'react';
import {Panel} from './ui';

type Mode='A'|'B';
/** This choice only directs navigation. Scenario updates stay in the existing V4 editors. */
export function PlanningMethods({mode,blocked,reason,open}:{mode?:string;blocked:boolean;reason?:string;open:(mode:Mode)=>void}){
 const [choice,setChoice]=useState<Mode>(mode==='B'?'B':'A');
 return <>{(['A','B'] as const).map(value=><Panel key={value} className={'planning-method'+(choice===value?' planning-method-selected':'')}><div className="panel-heading"><h2><label className="planning-method-selector"><input type="radio" name="planning-editor" value={value} checked={choice===value} onChange={()=>setChoice(value)}/><span className="planning-method-icon" aria-hidden="true">{value==='A'?<UsersRound size={19}/>:<Scale size={19}/>}</span><span>{value==='A'?'Modo A — Necessidades municipais independentes':'Modo B — Quantidade global justificada'}</span></label></h2></div>
 <p>{value==='A'?'Considere a necessidade calculada de cada município.':'Distribua uma meta fundamentada com critérios conferidos.'}</p>
 <ul>{(value==='A'?['Preserva os parâmetros de cada município.','Retirar uma cidade não aumenta as demais.','Exige entradas validadas para calcular.','Consolida necessidades calculadas, não compras passadas.']:['Exige meta justificada e fontes.','Pesos, pisos e tetos precisam de conferência.','Depende de confirmação antes da distribuição.','Histórico não define a meta global automaticamente.']).map(text=><li key={text}>{text}</li>)}</ul>
 <button className="button secondary" disabled={blocked} title={reason} onClick={()=>{setChoice(value);open(value);}}>{value==='A'?'Abrir cálculo individual V4':'Abrir critérios do modo B'}</button>
 <small className="planning-method-saved">Cenário salvo: {mode==='B'?'Modo B':'Modo A'}. Escolha acima apenas a navegação.</small>{reason?<small>{reason}</small>:null}
 </Panel>)}</>;
}
