import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const fixture=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const out=path.resolve(process.env.IRPS_WINDOWS_SCREENSHOTS||'../docs/IRPS_MICROTAREFAS/I04_01/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});test.afterEach(async({page})=>expect(errors.get(page)).toEqual([]));
const chart=(p:any)=>p.locator('.volume-windows-panel');
async function open(p:any,id=fixture.filtered){await p.goto('/index.html#/inicio?estudo='+id);await expect(p.locator('.selected-dashboard')).toBeVisible();}
async function shot(p:any,name:string){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,name+'.png')});}
// Rendering-only variations of a generated, explicitly synthetic study. Not evidence of official purchases.
async function variation(p:any,values:(string|null)[],reduced=false){await p.route(u=>u.pathname==='/api/v1/director/studies/'+fixture.filtered,async route=>{const response=await route.fetch();const study=await response.json();study.payload.history.temporal_windows.forEach((w:any,i:number)=>{w.observed_quantity=values[i];if(reduced&&i===3){w.scope_covers_requested_window=false;w.start='2025-06-01';}});await route.fulfill({response,json:study});});await open(p);}

test('Quatro barras usam totais e fonte do snapshot real sem modificar o estudo',async({page})=>{
 const endpoint='/api/v1/director/studies/'+fixture.filtered;const before=await(await page.request.get(endpoint)).json();await open(page);await expect(chart(page).getByRole('img')).toHaveCount(4);await expect(chart(page)).toContainText('Totais parciais · janelas sobrepostas');await expect(chart(page)).toContainText('PNCP · resultados de itens');await expect(chart(page)).toContainText('Homologado · 2025-01-01 a 2025-12-31');const card=await chart(page).boundingBox(),limits=await chart(page).locator('summary').boundingBox();expect(limits!.y+limits!.height).toBeLessThanOrEqual(card!.y+card!.height);
 const values=await chart(page).locator('.volume-value').allTextContents();expect(values).toEqual(['3 CAIXA','3 CAIXA','3 CAIXA','3 CAIXA']);for(const bar of await chart(page).locator('.volume-bar').all())expect(await bar.getAttribute('style')).toBe('height: 100%;');const after=await(await page.request.get(endpoint)).json();expect(after.payload).toEqual(before.payload);await shot(page,'01-quatro-janelas');
});
test('Janelas mistas não desenham barra para ausente; proporções 25 50 100 são visuais',async({page})=>{
 await variation(page,[null,'0.75','1.5','3']);await expect(chart(page).getByRole('img')).toHaveCount(3);await expect(chart(page).locator('.volume-missing')).toHaveCount(1);await expect(chart(page).locator('dd').first()).toContainText('Não disponível');expect(await chart(page).locator('.volume-bar').evaluateAll(bars=>bars.map(b=>(b as HTMLElement).style.height))).toEqual(['25%','50%','100%']);await shot(page,'mistas');
});
test('Todas as quantidades ausentes têm placeholders e nenhuma barra zero',async({page})=>{
 await variation(page,[null,null,null,null]);await expect(chart(page).getByRole('img')).toHaveCount(0);await expect(chart(page).locator('.volume-missing')).toHaveCount(4);await expect(chart(page).locator('.volume-bar')).toHaveCount(0);await expect(chart(page).locator('.volume-value')).toHaveText(['Não disponível','Não disponível','Não disponível','Não disponível']);await shot(page,'sem-quantidades');
});
test('Zero documentado é distinto de ausência e não é chamado de consumo',async({page})=>{
 await variation(page,['0',null,'0','0']);await expect(chart(page).getByRole('img')).toHaveCount(3);await expect(chart(page).locator('.volume-zero-label')).toHaveCount(3);await expect(chart(page).locator('.volume-missing')).toHaveCount(1);expect(await chart(page).locator('.volume-bar').evaluateAll(bars=>bars.map(b=>(b as HTMLElement).style.height))).toEqual(['0%','0%','0%']);await shot(page,'zero-documentado');
});
test('Detalhes por teclado informam sobreposição, unidade, períodos e filtros',async({page})=>{
 await open(page);const bar=chart(page).getByRole('img').first();await bar.focus();await expect(bar).toBeFocused();await expect(bar).toHaveAttribute('aria-label',/Total observado parcial.*2025-12-01 a 2025-12-31.*PNCP/);const summary=chart(page).locator('summary');await summary.focus();await page.keyboard.press('Enter');await expect(chart(page).locator('details')).toHaveAttribute('open','');await expect(chart(page)).toContainText('Não some as barras');await expect(chart(page)).toContainText('Apenas registros comparáveis');await expect(chart(page)).toContainText('não calculamos média mensal');await shot(page,'limites-teclado');
});
test('Entrada inválida ou negativa não vira barra e janela reduzida é identificada',async({page})=>{
 await variation(page,['-1','NaN','','3'],true);await expect(chart(page).getByRole('img')).toHaveCount(1);await expect(chart(page).locator('.volume-missing')).toHaveCount(3);await expect(chart(page).getByRole('img')).toHaveAttribute('aria-label',/período reduzido/);await expect(chart(page).locator('.volume-value').first()).toContainText('-1 CAIXA');await expect(chart(page)).toContainText('Valor negativo: confira a fonte');
});
for(const width of [390,1536])test('Gráfico legível e navegável em '+width,async({page})=>{
 await page.setViewportSize({width,height:width===1536?1024:941});await open(page);await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const first=chart(page).getByRole('img').first();await first.focus();await expect(first).toBeFocused();await shot(page,'grafico-'+width);
});
