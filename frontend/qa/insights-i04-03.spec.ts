import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const fixture=JSON.parse(fs.readFileSync(path.resolve('../.runtime/series-i04-02/browser-fixture.json'),'utf8'));
const previous=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-contract/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I04_03/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();
test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
test.afterEach(async({page})=>expect(errors.get(page)).toEqual([]));
async function open(p:any,id=fixture.base){await p.goto('/index.html#/inicio?estudo='+id);await expect(p.locator('.selected-dashboard')).toBeVisible();await p.evaluate(()=>document.fonts.ready);}
async function shot(p:any,name:string){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,name+'.png')});}
test('Dados persistidos sustentam os quatro insights, sem somar processos compartilhados',async({page})=>{
 const url='/api/v1/director/studies/'+fixture.base,before=await(await page.request.get(url)).json();await open(page);
 const panel=page.locator('.history-insights');await expect(panel.locator('[data-insight]')).toHaveCount(4);
 await expect(panel.locator('[data-insight="municipalities"]')).toContainText('2 de 2 municípios');
 await expect(panel.locator('[data-insight="processes"]')).toContainText('1 processo identificado');
 await expect(panel.locator('[data-insight="dates"]')).toContainText('De 05/01/2025 a 05/07/2025');
 await expect(panel.locator('[data-insight="comparison"]')).toContainText('4 de 5 registros comparáveis. 1 fora dos totais.');
 for(const item of await panel.locator('[data-insight]').all())await expect(item).toHaveAttribute('data-status','partial');
 const box=await panel.boundingBox(),button=await panel.getByRole('button',{name:'Métodos e evidências',exact:true}).boundingBox();expect(button!.y+button!.height).toBeLessThanOrEqual(box!.y+box!.height);
 const after=await(await page.request.get(url)).json();expect(after.payload).toEqual(before.payload);await shot(page,'01-insights');
});
test('Métodos, condições, fontes e limites abrem por teclado com retorno do foco',async({page})=>{
 await open(page);const trigger=page.getByRole('button',{name:'Métodos e evidências',exact:true});await trigger.focus();await page.keyboard.press('Enter');const dialog=page.getByRole('dialog');
 await expect(dialog).toBeVisible();await expect(dialog).toContainText('Demonstração fictícia');await expect(dialog).toContainText('Homologado · 2025-01-01 a 2025-12-31');
 await expect(dialog.getByText('Método:',{exact:true})).toHaveCount(4);await expect(dialog.getByText('Condição mínima:',{exact:true})).toHaveCount(4);
 await expect(dialog).toContainText('Não somamos contagens municipais');await expect(dialog).toContainText('Tendência e sazonalidade: indisponíveis');
 await expect(dialog.getByRole('link',{name:/Abrir fonte/}).first()).toHaveAttribute('href',/^https:\/\/example\.invalid\//);await expect(dialog).toContainText('Consulta:');await shot(page,'metodos-e-evidencias');
 await page.keyboard.press('Escape');await expect(dialog).not.toBeVisible();await expect(trigger).toBeFocused();
});
test('Fonte exata e comparabilidade mantêm contexto no acesso aos documentos',async({page})=>{
 await open(page,fixture.filtered);await expect(page.locator('[data-insight="comparison"]')).toContainText('2 de 2 registros comparáveis. 0 fora dos totais.');
 await page.getByRole('button',{name:'Métodos e evidências',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('PNCP · resultados de itens');await expect(page.getByRole('dialog')).toContainText('Apenas registros comparáveis');
 await page.getByRole('dialog').getByRole('link',{name:/Conferir registros e documentos/}).click();await expect(page).toHaveURL(/aba=fontes/);await expect(page).toHaveURL(new RegExp('estudo='+fixture.filtered));
 await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue('PNCP_RESULTADOS');
});
for(const width of [390,1536])test('Painel e inspeção utilizáveis em '+width,async({page})=>{
 await page.setViewportSize({width,height:width===1536?1024:941});await open(page);await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('.history-insights').scrollIntoViewIfNeeded();await shot(page,'painel-'+width);
 await page.getByRole('button',{name:'Métodos e evidências',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await shot(page,'inspecao-'+width);
});
test.describe('Snapshots persistidos da base isolada I01',()=>{
 test.use({baseURL:'http://127.0.0.1:5252'});
 test('Resumo anterior não produz insights reconstruídos nem altera o estudo',async({page})=>{
  const url='/api/v1/director/studies/'+previous.legacy,before=await(await page.request.get(url)).json();await open(page,previous.legacy);
  await expect(page.locator('.history-insights [data-status="unavailable"]')).toHaveCount(4);
  await expect(page.locator('.history-insights')).not.toContainText('0 de');
  await page.getByRole('button',{name:'Métodos e evidências',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('Os dados preservados não foram recalculados');
  expect((await(await page.request.get(url)).json()).payload).toEqual(before.payload);await shot(page,'snapshot-anterior');
 });
 test('Quantidade ausente mantém as contagens conhecidas, sem sugerir zero',async({page})=>{
  await open(page,previous.unknown);const quantity=page.locator('.executive-top .executive-metrics>div').filter({has:page.getByText('Quantidade documentada',{exact:true})});await expect(quantity.locator('[title="Informação não disponível"]')).toBeVisible();
  await expect(page.locator('[data-insight="municipalities"]')).toHaveAttribute('data-status','partial');
  await expect(page.locator('.history-insights')).not.toContainText('0 unidades');await shot(page,'quantidade-ausente');
 });
});
