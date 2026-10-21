import type {Row} from '../api';
import {quantity} from '../api';
import {Panel} from './ui';

export function HistoricalCharts({history,rows,unit,className=''}:{history:Row|null;rows:Row[];unit:string;className?:string}){
 const windows=history?.aggregate_windows||[];
 return <section className={'historical-charts '+className} aria-label="Gráficos e indicadores do item">
  <Panel scrollable title="Quantidade observada por período"><div className="chart-surface">{windows.length?<dl>{windows.map((w:Row)=><div key={w.months}><dt>{w.months} meses</dt><dd>{quantity(w.observed_quantity)} {unit}</dd></div>)}</dl>:<p>Sem quantidades comparáveis.<small>O código ainda exige vínculo técnico revisado.</small></p>}</div></Panel>
  <Panel scrollable title="Evolução mensal das ocorrências"><div className="chart-surface"><p>Sem série mensal comparável.<small>Períodos não consultados não representam zero compras.</small></p></div></Panel>
  <Panel scrollable title="Municípios e cobertura"><div className="chart-surface"><p>{rows.length} municípios no recorte<small>{history?'Confira as evidências de cada município.':'Sem histórico revisado para este código.'}</small></p></div></Panel>
 </section>;
}
