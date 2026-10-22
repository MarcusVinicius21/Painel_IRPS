import {test,expect} from '@playwright/test';
import {historyInsights} from '../src/historyInsights';

// Generated contract examples, never official procurement data.
function example(){return {contract_version:2,scope:{phase:'homologado',start:'2025-01-01',end:'2025-12-31',municipalities:['A','B']},summary:{phase:'homologado',start:'2025-01-01',end:'2025-12-31',selected_municipalities:2,municipalities_with_records:2,observed_records:3,distinct_processes:1,process_identity_complete:true,comparable_records:2,excluded_records:1,observed_quantity:null,documented_amount:null},municipalities:[{municipality:{ibge:'A'},observed_records:2,distinct_processes:1,first_observed:'2025-01-05',last_observed:'2025-03-05',evidence:[{fact_id:'generated-1',provider:'TEST',url:'https://example.invalid/one',event_date:'2025-01-05',consulted_at:'2026-10-21T12:00:00Z'}]},{municipality:{ibge:'B'},observed_records:1,distinct_processes:1,first_observed:'2025-05-05',last_observed:'2025-05-05',evidence:[{fact_id:'generated-2',provider:'TEST',url:'https://example.invalid/two',event_date:'2025-05-05',consulted_at:'2026-10-21T12:00:00Z'}]}]};}
const by=(h:any,id:string)=>historyInsights(h).find(i=>i.id===id)!;

test('Informações suficientes: contagens globais, datas e condições explícitas',()=>{
 const items=historyInsights(example());expect(items).toHaveLength(4);expect(items.every(i=>i.status==='partial'&&i.formula&&i.minimum&&i.limitation&&i.evidence.length===2)).toBe(true);
 expect(items[0].text).toBe('2 de 2 municípios selecionados têm registros.');
 expect(items[2].text).toBe('De 05/01/2025 a 05/05/2025.');
 expect(items[3].text).toBe('2 de 3 registros comparáveis. 1 fora dos totais.');
});
test('Processo compartilhado entre municípios não é somado novamente',()=>{
 const h=example();expect(by(h,'processes').text).toBe('1 processo identificado no recorte.');
 h.municipalities[1].evidence.push(h.municipalities[0].evidence[0]);expect(by(h,'processes').evidence).toHaveLength(2);
});
test('Nulos não viram zero nem valores monetários inferidos',()=>{
 const h:any=example();h.summary.distinct_processes=null;h.summary.comparable_records=null;
 expect(by(h,'processes').status).toBe('unavailable');expect(by(h,'comparison').status).toBe('unavailable');
 expect(JSON.stringify(historyInsights(h))).not.toMatch(/R\$|0 unidades|economia|previsão/);
 expect(by(h,'municipalities').status).toBe('partial');
});
test('Estudo anterior, ausência e contrato desconhecido permanecem indisponíveis',()=>{
 for(const h of [null,undefined,{municipalities:[]},{...example(),contract_version:3}])expect(historyInsights(h).every(i=>i.status==='unavailable'&&i.evidence.length===0)).toBe(true);
});
test('Contexto divergente de fase ou período não autoriza insights',()=>{
 const h=example();h.scope.phase='pago';expect(historyInsights(h).every(i=>i.status==='unavailable')).toBe(true);
 h.scope.phase='homologado';h.scope.start='2024-01-01';expect(historyInsights(h).every(i=>i.status==='unavailable')).toBe(true);
});
test('Datas incompletas ou fora do escopo não produzem amplitude falsa',()=>{
 const h:any=example();h.municipalities[1].last_observed=null;expect(by(h,'dates').status).toBe('unavailable');
 h.municipalities[1].last_observed='2026-05-05';expect(by(h,'dates').status).toBe('unavailable');
 h.municipalities[1].last_observed='2025-02-30';expect(by(h,'dates').status).toBe('unavailable');
});
test('Prévia limitada nunca vira denominador ou contagem de processos',()=>{
 const h:any=example();h.summary.observed_records=1000;h.summary.distinct_processes=500;h.summary.comparable_records=999;h.municipalities[0].evidence_truncated=true;
 expect(by(h,'processes').text).toContain('500 processos');expect(by(h,'processes').evidenceTruncated).toBe(true);
 expect(by(h,'comparison').text).toBe('999 de 1000 registros comparáveis. 1 fora dos totais.');
});
test('Sem fatos não há processos, datas ou comparabilidade fabricados',()=>{
 const h:any=example();Object.assign(h.summary,{observed_records:0,municipalities_with_records:0,distinct_processes:null,comparable_records:0,excluded_records:0});h.municipalities=[];
 expect(by(h,'municipalities').text).toBe('0 de 2 municípios selecionados têm registros.');
 expect(historyInsights(h).slice(1).every(i=>i.status==='unavailable')).toBe(true);
});
test('Contagens inconsistentes, negativas e fracionadas são recusadas',()=>{
 const h:any=example();h.summary.comparable_records=3;expect(by(h,'comparison').status).toBe('unavailable');
 h.summary.distinct_processes=-1;expect(by(h,'processes').status).toBe('unavailable');
 h.summary.municipalities_with_records=0.5;expect(by(h,'municipalities').status).toBe('unavailable');
});
test('Identificação incompleta permanece parcial; snapshots não são alterados',()=>{
 const h=example();h.summary.process_identity_complete=false;const before=structuredClone(h);
 expect(by(h,'processes').text).toContain('identificação parcial');expect(h).toEqual(before);
});
