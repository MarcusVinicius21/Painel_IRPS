import type {Row} from '../api';
import {quantity} from '../api';

export function CatalogueOrigin({item}:{item:Row}){
 let source:Row={};
 try{const parsed=typeof item.origin==='string'?JSON.parse(item.origin):item.origin;if(parsed&&typeof parsed==='object')source=parsed;}catch{/* Older origins remain available in the API, without exposing raw metadata. */}
 const url=typeof source.source_url==='string'&&source.source_url.startsWith('https://')?source.source_url:null;
 return <div className="catalogue-origin"><p>Fonte: {item.official_snapshot?'Compras.gov.br · arquivo oficial validado':'Origem ainda não certificada'}.</p>
  {url?<p><a href={url} target="_blank" rel="noreferrer">Abrir arquivo de origem</a></p>:null}
  <p>Versão publicada: {source.snapshot_version||'não informada'}.</p>
  {source.unique_valid_records!=null?<p>{quantity(source.unique_valid_records)} códigos neste arquivo. {source.reconciled?'Contagem conferida na importação.':'Contagem a conferir.'}</p>:null}
  <p>Identificador do arquivo: {item.sha256?.slice(0,16)||'não informado'}.</p>
  <p>Importado em {item.imported_at?new Date(item.imported_at).toLocaleString('pt-BR'):'data não informada'}.</p>
  <p>A situação do código não comprova compras, consumo ou necessidade futura.</p>
 </div>;
}
