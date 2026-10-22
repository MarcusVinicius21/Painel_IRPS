import {test,expect} from '@playwright/test';import fs from 'node:fs';
const fixture=JSON.parse(fs.readFileSync('../.runtime/sequence-08/fixture.json','utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test('Quadro confirmado preserva pendências, documento e total independente do filtro',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();
 const base='/api/v1/director/studies/'+fixture.study;const before=await(await page.request.get(base+'/register')).json();
 await page.goto('/index.html#/inteligencia?estudo='+fixture.study+'&etapa=consolidacao');const table=page.locator('.consolidation-layout .desktop-records');await expect(table.locator('tbody tr')).toHaveCount(2);
 await expect(table.locator('tbody tr').filter({hasText:'Alfenas/MG'})).toContainText('Não disponível');await expect(table.locator('tbody tr').filter({hasText:'Ipatinga/MG'})).toContainText('30');
 await table.getByRole('button',{name:'Quantidade confirmada',exact:true}).click();await expect(table.locator('tbody tr').first()).toContainText('Ipatinga/MG');
 await page.getByLabel('Itens por página',{exact:true}).selectOption('20');await expect(table.locator('tbody tr')).toHaveCount(2);
 await page.getByLabel('Buscar município',{exact:true}).fill('Alfenas');await expect(table.locator('tbody tr')).toHaveCount(1);await expect(page.locator('.consolidated-scope-total')).toContainText('30 unidade');
 await page.getByLabel('Buscar município',{exact:true}).fill('');const link=table.locator('tbody tr').filter({hasText:'Ipatinga/MG'}).getByRole('link',{name:'Abrir comprovante'});const original=await page.request.get((await link.getAttribute('href'))!);expect(original.status()).toBe(200);await expect(table).toContainText('Documento vinculado · versão');
 await table.getByRole('button',{name:'Conferir Ipatinga/MG',exact:true}).click();await expect(page).toHaveURL(/etapa=manifestacoes.*municipio=3131307/);await expect(page.locator('.manifest-summary')).toContainText('30 unidade');
 expect(await(await page.request.get(base+'/register')).json()).toEqual(before);expect(errors).toEqual([]);
});
