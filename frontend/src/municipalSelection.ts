import {useState} from 'react';
import {route} from './api';

export function readMunicipalSelection(scope:string[]){
 const params=route().params;return params.has('incluir')?scope.filter(id=>params.get('incluir')!.split(',').includes(id)):scope;
}
/** Study candidates only. Never edits historical scope, quantities or formal participation. */
export function useMunicipalSelection(scope:string[],context:string){
 const key=context+'|'+scope.join(',');
 const [state,setState]=useState<{key:string;ids:string[]}|null>(null);
 const selected=state?.key===key?state.ids:readMunicipalSelection(scope);
 const change=(ids:string[])=>{const next=scope.filter(id=>ids.includes(id));setState({key,ids:next});const r=route();r.params.set('incluir',next.join(','));window.history.replaceState(null,'','#/'+r.path+'?'+r.params);};
 const suffix=route().params.has('incluir')?'&incluir='+encodeURIComponent(selected.join(',')):'';
 return {selected,change,suffix};
}
