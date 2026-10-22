import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const fixture=JSON.parse(fs.readFileSync(path.resolve('../.runtime/series-i04-02/browser-fixture.json'),'utf8'));
const old=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I04_02/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
async function open(p:any,id=fixture.base){await p.goto('/index.html#/inicio?estudo='+id);await expect(p.locator('.selected-dashboard')).toBeVisible();}
async function shot(p:any,name:string){fs.mkdirSync(out,{recursive:true});if(p.viewportSize().width===1672)await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(out,name+'.png')});}
test('Série persistida: meses distintos, lacunas e origem, sem alterar snapshot',async({page})=>{
 const url='/api/v1/director/studies/'+fixture.base,before=await(await page.request.get(url)).json();
 expect(before.payload.history.observed_series.monthly).toHaveLength(12);await open(page);
 const panel=page.locator('.observed-monthly');await expect(panel.locator('.series-bar')).toHaveCount(3);
 await expect(panel.locator('.series-unknown')).toHaveCount(9);
 await expect(panel.locator('.series-value')).toHaveText(['3 CAIXA','5 CAIXA','2 CAIXA']);
 expect(await panel.locator('.series-bar').evaluateAll(bars=>bars.map(b=>(b as HTMLElement).style.height))).toEqual(['60%','100%','40%']);
 await expect(page.locator('.observed-geography .series-value')).toHaveText(['10 CAIXA']);
 await panel.locator('summary').focus();await page.keyboard.press('Enter');await expect(panel.locator('details')).toHaveAttribute('open','');
 await expect(panel).toContainText('PNCP');await expect(panel).toContainText('Sem cobertura comprovada');
 await expect(panel).toContainText(before.payload.history.observed_series.monthly[0].fact_ids[0]);
 await expect(panel.getByRole('link',{name:/Abrir fonte/}).first()).toHaveAttribute('href',/^https:\/\/example\.invalid\//);
 expect((await(await page.request.get(url)).json()).payload).toEqual(before.payload);await shot(page,'origem-teclado');
});
test('Filtro exato e comparabilidade preservados na série',async({page})=>{
 await open(page,fixture.filtered);await expect(page.locator('.observed-monthly .series-bar')).toHaveCount(1);
 await expect(page.locator('.observed-monthly .series-value')).toHaveText(['3 CAIXA']);
 await expect(page.locator('.observed-geography')).toContainText('PNCP · resultados de itens');await shot(page,'serie-filtrada');
});
test('Snapshot anterior mantém indisponibilidade sem recálculo',async({page})=>{
 await open(page,old.base);await expect(page.locator('.observed-monthly')).toContainText('Sem série mensal comparável');
 await expect(page.locator('.observed-series')).toHaveCount(0);await shot(page,'snapshot-anterior');
});
for(const width of [1672,390])test('Série real de teste navegável em '+width,async({page})=>{
 await page.setViewportSize({width,height:941});await open(page);await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('.observed-monthly .series-track').first().focus();await expect(page.locator('.observed-monthly .series-track').first()).toBeFocused();
 if(width===1672){await page.evaluate(()=>scrollTo(0,0));const boxes=await page.locator('.executive-charts>.panel').evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}}));fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'geometry.json'),JSON.stringify(boxes,null,2));}
 await shot(page,'serie-'+width);
});
