import {useState} from 'react';
import {useApi,useResource,post} from '../api';
import type {Row} from '../api';
import {Panel,Notice,DataTable,Badge} from '../components/ui';

const time=(value:unknown)=>typeof value==='string'?new Date(value).toLocaleString('pt-BR'):'Ainda não registrada';
const labels:Record<string,string>={PNCP:'PNCP',COMPRAS_GOV:'Compras.gov.br',IBGE:'IBGE',CATMAT_COM_BR:'CATMAT.com.br',
 LICITEI:'Licitei · POC isolada',PORTAL_TRANSPARENCIA:'Portal da Transparência',THIAGOSY_PNCP:'Cliente PNCP sem licença identificada',
 MCP_BRASIL:'MCP Brasil',LICINEXUS:'Licinexus',QUERIDO_DIARIO:'Querido Diário'};

export function MonitoringStatus(){
 const ctx=useApi(),targets=useResource('/portfolio/municipalities'),schedule=useResource('/portfolio/refresh'),providers=useResource('/portfolio/providers');
 const [pending,setPending]=useState(false);
 return <Panel title="Acompanhamento dos municípios">
  {targets.loading?<p role="status">Conferindo municípios monitorados…</p>:targets.error?<Notice tone="amber">{targets.error}</Notice>:<p><strong>{targets.data?.monitored??'Não disponível'} municípios monitorados</strong>. Filiações confirmadas por documento: {targets.data?.membership_confirmed??'Não disponível'}.</p>}
  <p>Monitoramento não comprova filiação ou cobertura completa de compras.</p>
  {schedule.loading?<p role="status">Consultando atualização…</p>:schedule.error?<Notice tone="amber">{schedule.error}</Notice>:<>
   <p>Última execução: {time(schedule.data?.last_run)}. Próxima verificação: {time(schedule.data?.next_run)}.</p>
   {schedule.data?.last_error?<Notice tone="amber">A última atualização precisa de atenção. Os dados salvos continuam disponíveis.</Notice>:null}
   <p>{schedule.data?.enabled?'A agenda retoma enquanto o servidor estiver ligado.':'A agenda ainda não foi iniciada neste ambiente.'} Estoque não disponível.</p>
   <p>Fila de consultas oficiais, incluindo outras coleções: {((schedule.data?.queue??[]) as Row[]).map(r=>`${({ready:'a consultar',running:'em execução',completed:'concluídas',failed:'com falha',failed_retryable:'aguardando nova tentativa',blocked:'bloqueadas',quarantined:'em conferência'} as Record<string,string>)[r.state]??r.state}: ${r.requests}`).join('; ')||'Nenhuma consulta registrada'}. Esses contadores não medem compras ou cobertura municipal.</p>
  </>}
  <button className="button secondary" disabled={pending||!ctx.can('sources.sync')} onClick={()=>{
   setPending(true);void ctx.run(async()=>{await post('/portfolio/refresh',{});},'Atualização solicitada. Acompanhe a próxima execução.').finally(()=>setPending(false));
  }}>{pending?'Solicitando…':'Atualizar agora'}</button>
  <details><summary>Conferir fontes e limitações</summary>
   {providers.loading?<p role="status">Consultando fontes…</p>:providers.error?<Notice tone="amber">{providers.error}</Notice>:<DataTable<Row> rows={providers.data?.records||[]} id={r=>r.provider} pageSize={10} caption="Situação das integrações" columns={[
    {label:'Fonte',render:r=>labels[r.provider]||r.provider},
    {label:'Situação',render:r=><Badge>{r.operational?'Consulta disponível':r.installed?'Instalada · uso limitado':'Ainda não utilizada'}</Badge>},
    {label:'Informação',render:r=>r.provider==='PORTAL_TRANSPARENCIA'?'Consulta CEIS por CNPJ. Não comprova regularidade geral.':r.provider==='LICITEI'?'POC separada. Uso comercial depende de revisão da licença.':r.official?'Dados oficiais; confira o período e a fase.':'Complemento. Não substitui documentos oficiais.'},
   ]}/>}
  </details>
  <details><summary>Catálogo: atualização manual aos sábados</summary><p>Importe somente arquivos oficiais conferidos, entre 8h e 12h. A atualização automática não substitui o catálogo.</p><p>A prévia e a importação local usam o procedimento administrativo documentado. Versões anteriores são preservadas.</p></details>
 </Panel>;
}
