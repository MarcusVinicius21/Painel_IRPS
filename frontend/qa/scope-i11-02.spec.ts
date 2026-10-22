import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/browser-fixture.json'),'utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test('Dashboard mostra recorte salvo; novo rascunho preserva o estudo anterior',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();
 const before=await (await page.request.get('/api/v1/director/studies/'+f.filtered)).json();await page.goto('/#/inicio?estudo='+f.filtered);await expect(page.locator('.dataset-warning')).toBeVisible();
 const start=page.getByLabel('Período preservado desde');await expect(start).toHaveValue('2025-01-01');await expect(start).toHaveAttribute('readonly','');await expect(page.getByLabel('Situação da compra',{exact:true})).toBeDisabled();await expect(page.locator('.executive-filters')).toContainText('IPCA');await expect(page.locator('.executive-filters')).toContainText('Não aplicada');
 await page.getByRole('link',{name:'Alterar período e municípios',exact:true}).click();await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue('PNCP_RESULTADOS');await page.getByLabel('Fonte',{exact:true}).selectOption('TESTE_IRPS_FONTE_B');
 const history=page.waitForResponse(r=>r.url().includes('/director/history/'+f.product_id+'?'));await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();expect((await history).status()).toBe(200);
 const saved=page.waitForResponse(r=>r.url().endsWith('/director/progress')&&r.request().method()==='POST');await page.getByRole('button',{name:'Salvar progresso',exact:true}).click();const response=await saved;expect(response.status()).toBe(201);const draft=await response.json();expect(draft.payload.history_filters.provider).toBe('TESTE_IRPS_FONTE_B');await expect(page).toHaveURL(/rascunho=/);await page.reload();await expect(page.getByLabel('Fonte',{exact:true})).toHaveValue('TESTE_IRPS_FONTE_B');
 const after=await (await page.request.get('/api/v1/director/studies/'+f.filtered)).json();expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toEqual(before.context_sha256);
 await page.goto('/#/inicio?estudo='+f.filtered);await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.locator('.product-scope')).toContainText('PNCP · resultados de itens');
});
