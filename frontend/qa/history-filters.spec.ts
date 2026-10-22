import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const fixture=JSON.parse(fs.readFileSync(process.env.IRPS_FILTER_BROWSER_FIXTURE||path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const A='PNCP_RESULTADOS',B='TESTE_IRPS_FONTE_B';
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();
test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));});
test.afterEach(async({page})=>{expect(errors.get(page)).toEqual([]);});
const historyResponse=(r:any)=>r.url().includes('/director/history/'+fixture.product_id+'?');
async function login(page:any,id=fixture.base){await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+id+'&etapa=historico');await expect(page.getByLabel('Fonte',{exact:true})).toBeEnabled();}
async function apply(page:any){const wait=page.waitForResponse(historyResponse);await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();const r=await wait;expect(r.status()).toBe(200);return r.json();}
async function source(page:any,value:string){await page.getByLabel('Fonte',{exact:true}).selectOption(value);await expect(page.getByRole('button',{name:'Exportar tabela',exact:true})).toBeDisabled();}

test('Fonte exata, comparabilidade, CSV e limpar filtros usam fatos reais do banco isolado',async({page})=>{
 await login(page);await expect(page.getByLabel('Modalidade',{exact:true})).toBeDisabled();
 await source(page,A);let h=await apply(page);expect(h.scope.filters).toEqual({provider:A,only_comparable:false});expect(h.summary.observed_records).toBe(3);expect(Number(h.summary.observed_quantity)).toBe(3);
 expect(h.municipalities.flatMap((r:any)=>r.evidence).every((e:any)=>e.provider===A)).toBe(true);
 await page.getByRole('checkbox',{name:'Apenas registros comparáveis',exact:true}).check();h=await apply(page);expect(h.summary.observed_records).toBe(2);expect(Number(h.summary.observed_quantity)).toBe(3);expect(h.filter_exclusions).toHaveLength(1);
 const downloadWait=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar tabela',exact:true}).click();const download=await downloadWait;const csv=fs.readFileSync((await download.path())!,'utf8');expect(csv).toContain('provider_filter');expect(csv).toContain('only_comparable');expect(csv).toContain('"'+A+'";"true"');expect(csv).not.toContain(B);expect(csv).toContain('2025-01-01');
 await page.getByRole('button',{name:'Limpar filtros adicionais',exact:true}).click();await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue('');await expect(page.getByRole('checkbox',{name:'Apenas registros comparáveis',exact:true})).not.toBeChecked();h=await apply(page);expect(h.summary.observed_records).toBe(5);expect(Number(h.summary.observed_quantity)).toBe(10);
});

test('Retomar estudo, salvar rascunho e navegar preservam o recorte sem regravar snapshot',async({page})=>{
 await login(page,fixture.filtered);await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue(A);await expect(page.getByRole('checkbox',{name:'Apenas registros comparáveis',exact:true})).toBeChecked();
 const before=await (await page.request.get('/api/v1/director/studies/'+fixture.filtered)).json();
 await source(page,B);await apply(page);
 const saved=page.waitForResponse((r:any)=>r.url().endsWith('/director/progress')&&r.request().method()==='POST');await page.getByRole('button',{name:'Salvar progresso',exact:true}).click();const progress=await (await saved).json();expect(progress.payload.history_filters).toEqual({provider:B,only_comparable:true});expect(progress.payload.product_id).toBe(fixture.product_id);expect(progress.payload.code).toBe(fixture.code);
 await expect(page).toHaveURL(/rascunho=/);await page.reload();await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue(B);await expect(page.getByLabel('Histórico desde',{exact:true})).toHaveValue('2025-01-01');await expect(page.getByLabel('Histórico até',{exact:true})).toHaveValue('2025-12-31');await expect(page.getByLabel('Situação da compra',{exact:true})).toHaveValue('homologado');await expect(page.getByLabel('Municípios para o estudo',{exact:true})).toHaveValues([...fixture.cities].sort());
 await page.getByRole('link',{name:'Planejar este item',exact:false}).click();await expect(page.getByRole('heading',{name:'Planejamento de compras municipais',exact:true})).toBeVisible();await page.getByRole('link',{name:'Análise do histórico',exact:false}).click();await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue(B);const h=await apply(page);expect(Number(h.summary.observed_quantity)).toBe(7);
 const after=await (await page.request.get('/api/v1/director/studies/'+fixture.filtered)).json();expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toBe(before.context_sha256);
});

test('Resposta atrasada de fonte anterior não reaparece após mudança de filtro',async({page})=>{
 await login(page);let release!:()=>void,arrived!:()=>void,finished!:()=>void;
 const gate=new Promise<void>(resolve=>release=resolve),received=new Promise<void>(resolve=>arrived=resolve),done=new Promise<void>(resolve=>finished=resolve);
 await page.route((url)=>url.pathname==='/api/v1/director/history/'+fixture.product_id&&url.searchParams.get('provider')===A,async route=>{const response=await route.fetch();arrived();await gate;await route.fulfill({response});finished();});
 await source(page,A);await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();await received;
 await source(page,B);const h=await apply(page);expect(Number(h.summary.observed_quantity)).toBe(7);release();await done;
 await expect(page.getByText('Recorte consultado · '+B,{exact:false})).toBeVisible();
 const downloadWait=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar tabela',exact:true}).click();const csv=fs.readFileSync((await (await downloadWait).path())!,'utf8');expect(csv).toContain('"'+B+'"');expect(csv).not.toContain('"'+A+'"');
});

test('Falha HTTP limpa números anteriores e permite repetir a consulta',async({page})=>{
 await login(page);await source(page,A);
 const url=(u:URL)=>u.pathname==='/api/v1/director/history/'+fixture.product_id;
 await page.route(url,route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:{message:'Consulta indisponível durante o teste.'}})}));
 await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();await expect(page.getByText('Consulta indisponível durante o teste.',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Exportar tabela',exact:true})).toBeDisabled();
 await page.unroute(url);const h=await apply(page);expect(Number(h.summary.observed_quantity)).toBe(3);
 await page.getByLabel('Histórico até',{exact:true}).fill('');await expect(page.getByRole('heading',{name:'Inteligência e planejamento de compras',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Exportar tabela',exact:true})).toBeDisabled();
});

test('Recorte vazio preserva municípios e ausência não vira quantidade zero',async({page})=>{
 await login(page);await source(page,B);await page.getByLabel('Histórico desde',{exact:true}).fill('2024-01-01');await page.getByLabel('Histórico até',{exact:true}).fill('2024-12-31');await expect(page.getByLabel('Fonte',{exact:true})).toBeEnabled();
 const h=await apply(page);expect(h.summary.observed_records).toBe(0);expect(h.summary.observed_quantity).toBeNull();expect(h.summary.documented_amount).toBeNull();expect(h.municipalities).toHaveLength(2);expect(h.municipalities.every((r:any)=>r.observed_quantity===null)).toBe(true);expect(h.source_completeness_claimed).toBe(false);
});


test('Fonte e comparabilidade funcionam por teclado e em 390 px',async({page})=>{
 await login(page);
 for(const width of [1672,390]){
  await page.setViewportSize({width,height:941});await page.getByRole('button',{name:'Limpar filtros adicionais',exact:true}).click();await source(page,A);
  const checkbox=page.getByRole('checkbox',{name:'Apenas registros comparáveis',exact:true});
  if(await checkbox.isChecked())await checkbox.uncheck();
  await page.getByLabel('Fonte',{exact:true}).focus();await page.keyboard.press('Tab');await expect(checkbox).toBeFocused();await page.keyboard.press('Space');await expect(checkbox).toBeChecked();
  const h=await apply(page);expect(h.scope.filters).toEqual({provider:A,only_comparable:true});expect(Number(h.summary.observed_quantity)).toBe(3);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 }
});
