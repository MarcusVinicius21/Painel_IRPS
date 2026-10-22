import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/browser-fixture.json'),'utf8'));
test.use({viewport:{width:1536,height:1024},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+f.base+'&etapa=selecao');await expect(page.locator('.dataset-warning')).toBeVisible();await page.waitForLoadState('networkidle');});
test('Matriz preserva recorte ao selecionar e exporta todo histórico com seleção explícita',async({page})=>{
 const original=await (await page.request.get('/api/v1/director/studies/'+f.base)).json();
 const matrix=page.locator('.municipal-history-panel');await expect(matrix.locator('tbody tr')).toHaveCount(2);
 await page.getByRole('checkbox',{name:'Incluir Ipatinga/MG no estudo',exact:true}).uncheck();await expect(matrix.locator('tbody tr')).toHaveCount(2);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar tabela',exact:true}).click();const csv=fs.readFileSync((await (await download).path())!,'utf8');
 expect(csv).toContain('selected_for_study');expect(csv).toContain('3131307');expect(csv).toContain('3101607');expect(csv).toContain('"homologado"');expect(csv).toContain('"2025-01-01"');expect(csv).toContain('"caixa de 10 resmas"');expect(csv.split('\n').find(x=>x.includes('3131307'))).toContain('"false"');
 await matrix.locator('tbody tr').first().locator('details summary').click();await expect(matrix).toContainText('Situação: Homologado');await expect(matrix).toContainText('versão 1');await expect(matrix).toContainText('Registro ');
 await page.getByRole('button',{name:'Município · IBGE',exact:false}).click();await expect(matrix.locator('thead th[aria-sort]')).toHaveAttribute('aria-sort','ascending');
 const after=await (await page.request.get('/api/v1/director/studies/'+f.base)).json();expect(after.payload).toEqual(original.payload);expect(after.context_sha256).toEqual(original.context_sha256);
});
test('Janelas e planejamento permanecem separados; ação leva ao modo existente sem gravar',async({page})=>{
 await expect(page.locator('.historical-charts .volume-track')).toHaveCount(4);await expect(page.locator('.volume-partial')).toContainText('janelas sobrepostas');fs.mkdirSync('../docs/IRPS_REFINAMENTO_I09_I17/I10_03/ESTADOS',{recursive:true});await page.screenshot({path:'../docs/IRPS_REFINAMENTO_I09_I17/I10_03/ESTADOS/HISTORICO_SINTETICO.png'});
 await expect(page.locator('.selection-quantity-context')).toContainText('Histórico observado');await expect(page.locator('.selection-quantity-context')).toContainText('Necessidade V4');await expect(page.locator('.selection-quantity-context')).toContainText('Sugestão do consórcio');await expect(page.locator('.selection-quantity-context')).toContainText('Confirmação municipal');
 let writes=0;page.on('request',r=>{if(r.method()==='POST')writes++;});await page.getByRole('link',{name:'Abrir planejamento',exact:true}).click();await expect(page).toHaveURL(/etapa=planejamento/);await expect(page.getByRole('heading',{name:'Planejamento de compras municipais',exact:true})).toBeVisible();expect(writes).toBe(0);
 await page.setViewportSize({width:390,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
