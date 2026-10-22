import {useState} from 'react';
import {post,useApi} from '../api';
import type {Row} from '../api';

export function SaveHistoryAnalysis({history,entry,form,cities,start,end,phase,filters,studyId,progressId,planningSuffix=''}:{history:Row|null;entry:Row|null;form:Row;cities:string[];start:string;end:string;phase:string;filters:Row;studyId?:string|null;progressId?:string|null;planningSuffix?:string}){
 const c=useApi(),[saved,setSaved]=useState<string|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [savedHistory,setSavedHistory]=useState<Row|null>(null);
 const key=JSON.stringify([entry?.snapshot_id,entry?.code,cities,start,end,phase,filters,planningSuffix]);
 const [savedKey,setSavedKey]=useState('');
 const available=history?.municipalities?.some((r:Row)=>(r.observed_records??0)>0);
 async function save(){
  setBusy(true);setError('');setSaved(null);
  try{
   const fields=['name','specification','category','classification','unit','quantity_step','service_period','quantity_basis'];
   const partial=Object.fromEntries(fields.map(k=>[k,String(form[k]??(k==='classification'?'internal':k==='quantity_step'?'1':k==='category'?'material':''))]));
   const result=await post('/director/analyses',{snapshot_id:entry?.snapshot_id||null,code:entry?.code||null,product_id:history?.product.id,municipalities:cities,start,end,phase,history_filters:filters,stage:'historico',form:partial,source_study_id:studyId||null,source_progress_id:progressId||null,expected_history_sha256:history?.snapshot_sha256||null});
   setSaved(result.id);setSavedKey(key);setSavedHistory(history);
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 return <div className="history-analysis-actions"><button className="button secondary" disabled={busy||!available||!c.can('scenario.write')} onClick={()=>void save()} title={available?'Preserva este recorte e suas evidências. Não cria necessidade ou confirmação.':'Consulte registros vinculados antes de salvar uma análise.'}>{busy?'Salvando análise…':'Salvar análise histórica'}</button>{!available?<small>Sem registros associados para salvar.</small>:null}{saved&&savedKey===key&&savedHistory===history?<div className="analysis-save-result" role="status">Análise preservada. <a href={'#/inteligencia?analise='+saved+'&etapa=historico'+planningSuffix}>Abrir análise salva</a><a href={'#/inteligencia?analise='+saved+'&etapa=planejamento'+planningSuffix}>Usar histórico no planejamento</a></div>:null}{error?<p role="alert">{error}</p>:null}</div>;
}
