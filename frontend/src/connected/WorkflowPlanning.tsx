import {useEffect,useState} from 'react';
import {useApi,useResource,route} from '../api';
import {Notice} from '../components/ui';
import {Planning} from './Planning';

/** Reopening a V4 route must select the persisted study scenario, never the latest unrelated one. */
export function WorkflowPlanning({path}:{path:string}){
 const c=useApi(),id=route().params.get('estudo'),study=useResource(id?'/director/studies/'+id:null),[error,setError]=useState('');
 useEffect(()=>{let current=true;setError('');if(study.data&&c.scenario?.id!==study.data.scenario_id)void c.select(study.data.scenario_id).catch(e=>{if(current)setError(e.message);});return()=>{current=false;};},[study.data?.scenario_id,c.scenario?.id,c.select]);
 if(!id)return <Planning path={path}/>;
 if(study.error||error)return <Notice tone="warning">Não foi possível abrir o cenário deste estudo. {study.error||error}</Notice>;
 if(study.loading||c.scenario?.id!==study.data?.scenario_id)return <p role="status">Abrindo o cenário preservado no estudo…</p>;
 return <><div className="workflow-return"><a className="button secondary" href={'#/inteligencia?etapa=planejamento&estudo='+id}>Voltar ao estudo de origem</a><span>{study.data?.payload.name}<small>Parâmetros V4 do cenário vinculado. O histórico não preenche as necessidades.</small></span></div>{study.data&&!study.data.context_current?<Notice tone="warning">O cenário mudou. O estudo original permanece preservado e exige nova conferência documental.</Notice>:null}<Planning path={path}/></>;
}
