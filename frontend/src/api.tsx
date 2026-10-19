import {createContext,useContext,useState,useEffect,useCallback} from 'react';
import type {ReactNode} from 'react';
export type Row=Record<string,any>;
export type Identity={actor_id:string;org_id:string;name:string;organization:string;kind:string;role:string;permissions:string[];identity_mode:string};
const csrf=()=>decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith('irps_csrf='))?.slice(10)||'');
export async function api(path:string,options:RequestInit={}){
 const headers=new Headers(options.headers);if(options.body&&!(options.body instanceof FormData))headers.set('Content-Type','application/json');
 if(options.method&&options.method!=='GET')headers.set('X-CSRF-Token',csrf());
 let response:Response;
 try{response=await fetch('/api/v1'+path,{...options,headers,credentials:'include'});}catch{throw new Error('Não conseguimos acessar o IRPS agora. Tente novamente em instantes.');}
 const data=await response.json().catch(()=>({}));
 if(!response.ok){if(response.status===401)window.dispatchEvent(new Event('irps-session-ended'));throw new Error(data.detail?.message||'Não foi possível concluir. Confira os dados e tente novamente.');}
 return data;
}
export const post=(path:string,data?:unknown,headers?:HeadersInit)=>api(path,{method:'POST',body:data===undefined?undefined:JSON.stringify(data),headers});
function useCreate(){
 const [identity,setIdentity]=useState<Identity|null>(null),[ready,setReady]=useState(false),[toast,setToast]=useState(''),[busy,setBusy]=useState(false),[revision,setRevision]=useState(0);
 const [cities,setCities]=useState<Row[]>([]),[items,setItems]=useState<Row[]>([]),[itemVersions,setItemVersions]=useState<Row[]>([]),[scenarios,setScenarios]=useState<Row[]>([]),[scenario,setScenario]=useState<Row|null>(null),[calculation,setCalculation]=useState<Row|null>(null);
 const clear=useCallback(()=>{setIdentity(null);setCities([]);setItems([]);setItemVersions([]);setScenarios([]);setScenario(null);setCalculation(null);},[]);
 const load=useCallback(async()=>{try{setIdentity(await api('/auth/context'));}catch{clear();}finally{setReady(true);}},[clear]);
 useEffect(()=>{void load();window.addEventListener('irps-session-ended',clear);return()=>window.removeEventListener('irps-session-ended',clear);},[load,clear]);
 const select=useCallback(async(id:string)=>{const [s,c]=await Promise.all([api('/scenarios/'+id),api('/scenarios/'+id+'/calculations')]);setScenario(s);setCalculation(c.records.find((x:Row)=>x.revision===s.current_revision)||null);},[]);
 const refresh=useCallback(async()=>{const [c,i,s]=await Promise.all([api('/municipalities'),api('/items'),api('/scenarios')]);setCities(c.records);setItems(i.records);setItemVersions(i.versions);setScenarios(s.records);if(s.records.length)await select(s.records[0].id);},[select]);
 useEffect(()=>{if(identity)void refresh().catch(e=>setToast(e.message));},[identity?.actor_id,refresh]);
 async function run(fn:()=>Promise<unknown>,message='Alteração salva.') {if(busy)return;setBusy(true);try{await fn();setRevision(r=>r+1);if(message)setToast(message);}catch(e){setToast((e as Error).message);}finally{setBusy(false);}}
 async function update(snapshot:Row){if(!scenario)return;const clean=structuredClone(snapshot);delete clean.review;delete clean.distribution_confirmation;const s=await api('/scenarios/'+scenario.id,{method:'PUT',headers:{'If-Match':String(scenario.current_revision)},body:JSON.stringify(clean)});setScenario(s);setCalculation(null);return s;}
 async function calculate(){if(!scenario)return;setCalculation(await post('/scenarios/'+scenario.id+'/calculate'));}
 return {identity,ready,toast,setToast,busy,run,revision,cities,items,item:(id:string,version:number)=>itemVersions.find(i=>i.id===id&&i.version===version),scenarios,scenario,calculation,select,refresh,update,calculate,setScenario,setCalculation,load,clear,can:(permission:string)=>!!identity?.permissions.includes(permission)};
}
const Context=createContext<ReturnType<typeof useCreate>|null>(null);
export function ApiProvider({children}:{children:ReactNode}){const value=useCreate();return <Context value={value}>{children}</Context>;}
export function useApi(){const ctx=useContext(Context);if(!ctx)throw Error('ApiProvider ausente');return ctx;}
export function useResource(path:string|null){const {revision,setToast}=useApi();const [data,setData]=useState<Row|null>(null),[error,setError]=useState('');useEffect(()=>{let current=true;setData(null);setError('');if(path)void api(path).then(r=>{if(current)setData(r);}).catch(e=>{if(current){setError(e.message);setToast(e.message);}});return()=>{current=false;};},[path,revision,setToast]);return {data,error,loading:!!path&&!data&&!error};}
export function route(){const [raw,q='']=(location.hash.slice(1)||'/inicio').split('?');return {path:raw.replace(/^\//,''),params:new URLSearchParams(q)};}
export function nav(path:string,params:Record<string,string>={}){location.hash='/'+path+(Object.keys(params).length?'?'+new URLSearchParams(params):'');}
export function param(key:string,value:string){const r=route();r.params.set(key,value);location.hash='/'+r.path+'?'+r.params;}
export const money=(v:unknown)=>v==null?'Não disponível':new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(v));
export const quantity=(v:unknown)=>v==null?'Não disponível':new Intl.NumberFormat('pt-BR',{maximumFractionDigits:8}).format(Number(v));
export const phases:Record<string,string>={publicado_estimado:'Publicado · estimado',homologado:'Homologado',contratado:'Contratado',solicitado:'Solicitado',entregue:'Entregue',consumido:'Consumo comprovado',empenhado:'Empenhado',liquidado:'Liquidado',pago:'Pago',estorno:'Estorno'};
