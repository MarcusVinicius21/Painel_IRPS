import {useEffect,useState} from 'react';
import {api,useApi} from '../api';import type {Row} from '../api';
import {Panel,Notice,DataTable,Badge} from '../components/ui';
export function LicinexusStatus(){
 const ctx=useApi(),[data,setData]=useState<Row|null>(null),[error,setError]=useState('');
 useEffect(()=>{let active=true;const load=()=>void api('/portfolio/licinexus').then(r=>{if(active){setData(r);setError('');}}).catch(e=>{if(active)setError(e.message);});load();const timer=setInterval(load,15000);return()=>{active=false;clearInterval(timer);};},[ctx.revision]);
 const states:Record<string,string>={queued:'Na fila',running:'Consultando fonte',completed:'Consulta concluída',failed:'Precisa de conferência',retry_wait:'Aguardando nova tentativa'};
 return <Panel title="Consultas complementares Licinexus">
  <Notice>Origem oficial: PNCP. Itens, homologações e contratos permanecem separados. Não há saldo de estoque comprovado.</Notice>
  {error?<Notice tone="amber">{error} Os demais dados continuam disponíveis.</Notice>:!data?<p role="status">Conferindo consultas complementares…</p>:<>
   <p>{data.installed?`Versão ${data.version} instalada em ambiente isolado.`:'O complemento ainda não está instalado neste computador.'} A consulta depende do servidor ligado.</p>
   <p>Abra uma linha municipal para atualizar itens, resultados ou documentos. A consulta não confirma vínculo CATMAT/CATSER.</p>
   <DataTable<Row> rows={data.jobs??[]} id={r=>r.id} pageSize={5} caption="Consultas Licinexus com origem documentada" columns={[
    {label:'Município e grupo',render:r=><>{ctx.cities.find(c=>c.ibge===r.arguments.municipality_ibge)?.name??r.arguments.municipality_ibge}<small>Grupo {r.arguments.group}</small></>},
    {label:'Situação',render:r=><Badge>{states[r.state]??'Conferir consulta'}</Badge>},
    {label:'Informações encontradas',render:r=>r.result?.records!=null?<>{r.result.records} registros da fonte<small>{r.result.new_revisions??0} versões acrescentadas; não são compras independentes</small></>:'Ainda não confirmadas'},
    {label:'Fonte e data',render:r=><>{(r.result?.documents??[]).map((d:Row)=><p key={d.url}><a href={d.url} target="_blank" rel="noreferrer">Abrir evidência PNCP</a></p>)}<small>{new Date(r.created_at).toLocaleString('pt-BR')}</small></>},
   ]}/><details><summary>Limites desta integração</summary><p>Buscas amplas, atas e PCA ainda dependem da disponibilidade e validação das fontes. A dependência Zod tem um alerta de segurança. A execução está isolada e limitada, sem acesso MCP direto pelo navegador.</p></details>
  </>}
 </Panel>;
}
