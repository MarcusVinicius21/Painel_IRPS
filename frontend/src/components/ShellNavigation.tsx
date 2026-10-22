import {useState} from 'react';
import {House,BrainCircuit,Lightbulb,ClipboardList,FileText,FolderOpen,MapPinned,PackageSearch,Database,Settings,ChevronDown,BriefcaseBusiness,Bell,Activity} from 'lucide-react';
import {IconProps} from './ui';

export const shellDestinations=[
 ['inicio','Início',House],
 ['inteligencia','Inteligência e Planejamento',BrainCircuit],
 ['oportunidades','Oportunidades',Lightbulb],
 ['licitacao','Planejamento (V4)',ClipboardList],
 ['documentos','Documentos',FolderOpen],
 ['comparar','Municípios',MapPinned],
 ['pesquisa','Histórico de Compras',PackageSearch],
 ['catalogo-inteligente','Catálogo Nacional',Database],
 ['relatorios','Relatórios',FileText],
 ['administracao','Configurações',Settings],
] as const;
const extras=[['negocio','Meu negócio',BriefcaseBusiness],['necessidades','Necessidades',Activity],['fontes','Fontes e cobertura',Database],['alertas','Acompanhamentos',Bell]] as const;
const v4Paths=['licitacao','participantes','itens','quantidades','distribuicao','precos','revisao','relatorios','memoria'];

/** Navigation retains the persisted study; opening a destination never creates or approves data. */
export function ShellNavigation({current,onNavigate,dialog=false}:{current:{path:string;params:URLSearchParams};onNavigate?:()=>void;dialog?:boolean}){
 const study=current.params.get('estudo'),stage=current.params.get('etapa')||'';
 const [irpOpen,setIrpOpen]=useState(false);
 const href=(to:string)=>'#/'+to+(study&&['inicio','inteligencia','licitacao','relatorios'].includes(to)?'?estudo='+encodeURIComponent(study):'');
 const active=(to:string)=>to==='inteligencia'?(current.path==='inteligencia'||current.path==='inicio'&&!!study):to==='inicio'?current.path==='inicio'&&!study:to==='licitacao'?v4Paths.includes(current.path)&&current.path!=='relatorios':current.path===to;
 return <nav className={'shell-navigation'+(dialog?' shell-navigation-dialog':'')} aria-label={dialog?'Destinos do Observatório':'Seções do Observatório'}>
  {shellDestinations.map(([to,label,Icon])=><div className="shell-nav-entry" key={to}>
   <a href={href(to)} onClick={onNavigate} className={active(to)?'active':''} aria-current={active(to)?'page':undefined} title={to==='administracao'?'Consultar acesso, permissões e configuração disponível':to==='comparar'?'Consultar e comparar os municípios cadastrados':undefined}><Icon {...IconProps}/><span>{label}</span></a>
   {to==='licitacao'?<><button className="shell-irp-toggle" aria-expanded={irpOpen} aria-controls={dialog?'irp-dialog-destinations':'irp-rail-destinations'} onClick={()=>setIrpOpen(x=>!x)}><FileText {...IconProps}/><span>IRP</span><ChevronDown {...IconProps} className={irpOpen?'expanded':''}/></button>
    <div className="shell-irp-submenu" id={dialog?'irp-dialog-destinations':'irp-rail-destinations'} hidden={!irpOpen}>{study?[
     ['preparacao','Preparação da IRP'],['manifestacoes','Manifestações'],['consolidacao','Consolidação'],
    ].map(([value,text])=><a key={value} href={'#/inteligencia?estudo='+encodeURIComponent(study)+'&etapa='+value} onClick={onNavigate} aria-current={stage===value?'page':undefined} className={stage===value?'active':''}>{text}</a>):<><p>Selecione um estudo para preparar a IRP.</p><a href="#/inteligencia" onClick={onNavigate}>Selecionar um item</a></>}</div></>:null}
  </div>)}
  <details className="shell-extra-tools"><summary>Outras ferramentas<ChevronDown {...IconProps}/></summary>{extras.map(([to,label,Icon])=><a key={to} href={'#/'+to} onClick={onNavigate} className={current.path===to?'active':''} aria-current={current.path===to?'page':undefined}><Icon {...IconProps}/><span>{label}</span></a>)}</details>
 </nav>;
}
