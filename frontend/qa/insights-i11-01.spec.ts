import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const linked=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/browser-fixture.json'),'utf8'));
const legacy=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/legacy.json'),'utf8'));
const free=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
test('Resumo e quatro insights usam o snapshot ligado, com método e limite documental',async({page})=>{
 const before=await (await page.request.get('/api/v1/director/studies/'+linked.base)).json();await page.goto('/#/inicio?estudo='+linked.base);await expect(page.locator('.dataset-warning')).toBeVisible();
 const summary=page.locator('.product-summary');await expect(summary).toContainText(/R\$\s*100,00/);await expect(summary.locator('.executive-metrics>div').nth(2)).toContainText('10');
 await expect(page.locator('.history-insights li[data-insight]')).toHaveCount(4);await expect(page.locator('.insight-documental')).toHaveText('Regras documentais');await expect(page.getByText('Gerado por IA',{exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Métodos e evidências',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('Método:');await expect(page.getByRole('dialog')).toContainText('Não representam toda a demanda');await page.keyboard.press('Escape');
 const after=await (await page.request.get('/api/v1/director/studies/'+linked.base)).json();expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toEqual(before.context_sha256);
 fs.mkdirSync('../docs/IRPS_REFINAMENTO_I09_I17/I11_01/ESTADOS',{recursive:true});await page.screenshot({path:'../docs/IRPS_REFINAMENTO_I09_I17/I11_01/ESTADOS/LIGADO.png'});
});
test('Sem vínculo e estudo legado abrem sem recalcular ou converter ausência em zero',async({page})=>{
 for(const id of [free.study,legacy.legacy]){
  const before=await (await page.request.get('/api/v1/director/studies/'+id)).json();await page.goto('/#/inicio?estudo='+id);await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.locator('.product-summary [title="Informação não disponível"]')).toHaveCount(4);await expect(page.locator('.history-insights li[data-status="unavailable"]')).toHaveCount(4);
  await page.setViewportSize({width:390,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);await page.setViewportSize({width:1672,height:941});
  const after=await (await page.request.get('/api/v1/director/studies/'+id)).json();expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toEqual(before.context_sha256);
 }
});
