
const views=[['municipios','Histórico por município'],['precos','Preços praticados'],['fontes','Fontes e documentos'],['similares','Itens similares'],['anual','Histórico anual']] as const;

/** Presentation only: every view reads the same preserved historical scope. */
export function HistoryTabs({value,onChange,panelId}:{value:string;onChange:(value:string)=>void;panelId:string}){
 return <div className="history-view-controls"><div className="workflow-tabs" role="tablist" aria-label="Visões do histórico" aria-orientation="horizontal">
  {views.map(([key,label],index)=><button key={key} id={panelId+'-'+key} type="button" role="tab" aria-selected={value===key} aria-controls={panelId} tabIndex={value===key?0:-1} onClick={()=>onChange(key)} onKeyDown={e=>{
   const target=e.key==='Home'?0:e.key==='End'?views.length-1:e.key==='ArrowRight'?(index+1)%views.length:e.key==='ArrowLeft'?(index+views.length-1)%views.length:null;
   if(target==null)return;e.preventDefault();onChange(views[target][0]);e.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[target]?.focus();
  }}>{label}</button>)}
 </div></div>;
}
