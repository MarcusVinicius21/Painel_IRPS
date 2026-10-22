import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/browser-fixture.json'),'utf8')),empty=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
test('Ponto mensal documentado, fontes, CSV e ação de planejamento preservam recorte',async({page})=>{
 await page.goto('/#/inicio?estudo='+f.base);await expect(page.locator('.dataset-warning')).toBeVisible();
 await expect(page.locator('.monthly-observation-point')).toHaveCount(1);await expect(page.locator('.monthly-observation-segment')).toHaveCount(0);await expect(page.locator('.monthly-observed-line')).toHaveAttribute('aria-label',/Lacunas não são ligadas nem preenchidas/);
 await page.getByText('Ver valores mensais e fontes',{exact:true}).click();await expect(page.locator('.monthly-source-table')).toContainText('2025-12');await expect(page.locator('.monthly-source-table')).toContainText('10 CAIXA');
 const wait=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar tabela',exact:true}).click();const csv=fs.readFileSync((await (await wait).path())!,'utf8');expect(csv).toContain('evidence_item_versions');expect(csv).toContain(f.product_id);
 await page.getByRole('link',{name:'Usar os dados no planejamento',exact:false}).click();await expect(page).toHaveURL(/etapa=planejamento/);await expect(page).toHaveURL(new RegExp(f.base));
});
test('Sem série o dashboard mantém ausência e as abas levam ao estudo correto',async({page})=>{
 await page.goto('/#/inicio?estudo='+empty.study);await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.locator('.monthly-observation-point')).toHaveCount(0);await expect(page.locator('.observed-monthly')).toContainText('Sem série mensal comparável');
 await page.getByRole('link',{name:'Fontes e documentos',exact:true}).click();await expect(page).toHaveURL(/aba=fontes/);await expect(page).toHaveURL(new RegExp(empty.study));
});
