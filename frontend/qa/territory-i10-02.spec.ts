import {test,expect} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/rodada30/testing/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_REFINAMENTO_I09_I17/I10_02/ESTADOS');
test.use({viewport:{width:1536,height:1024},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+f.base+'&etapa=selecao');await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.getByLabel('Fonte',{exact:true})).toBeEnabled();});
test('Território localiza no cadastro sem perder municípios, dados ou afirmar cobertura',async({page})=>{
 const active=page.getByRole('button',{name:'Todos',exact:true});await expect(active).toHaveCSS('background-color','rgb(0, 99, 226)');await expect(active).toHaveCSS('color','rgb(255, 255, 255)');const select=page.getByLabel('Municípios para o estudo',{exact:true});await expect(select).toHaveValues([...f.cities].sort());
 await page.getByRole('button',{name:'Estado',exact:true}).click();await page.getByLabel('Localizar municípios por UF',{exact:true}).selectOption('RJ');await expect(select).toHaveValues([...f.cities].sort());
 await page.getByRole('button',{name:'Municípios',exact:true}).click();await page.getByLabel('Localizar município',{exact:true}).fill('nenhuma correspondência');await expect(select).toHaveValues([...f.cities].sort());
 await page.getByRole('button',{name:'Todos',exact:true}).click();await expect(page.getByLabel('Abrangência no cadastro')).toHaveValue('');await expect(select).toHaveValues([...f.cities].sort());
 await page.getByText('Cadastro, seleção e cobertura',{exact:true}).click();await expect(page.locator('.territory-selector')).toContainText('não comprova cobertura nacional nem vínculo consorcial');
 fs.mkdirSync(out,{recursive:true});await page.screenshot({path:out+'/TERRITORIO.png'});
});
test('Municípios, período, fase e fonte atravessam a API; snapshot salvo não é regravado',async({page})=>{
 const before=await (await page.request.get('/api/v1/director/studies/'+f.base)).json();
 await page.getByLabel('Municípios para o estudo',{exact:true}).selectOption(f.cities[1]);await page.getByLabel('Histórico desde',{exact:true}).fill('2025-12-01');await page.getByLabel('Fonte',{exact:true}).selectOption('TESTE_IRPS_FONTE_B');
 await page.getByRole('checkbox',{name:'Apenas registros comparáveis',exact:true}).check();
 const response=page.waitForResponse(r=>r.url().includes('/director/history/'+f.product_id+'?'));await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();const r=await response;expect(r.status()).toBe(200);const data=await r.json();
 expect(data.municipalities.map((x:any)=>x.municipality.ibge)).toEqual([f.cities[1]]);expect(Number(data.summary.observed_quantity)).toBe(2);expect(data.scope.filters).toEqual({provider:'TESTE_IRPS_FONTE_B',only_comparable:true});expect(data.summary.start).toBe('2025-12-01');expect(data.summary.phase).toBe('homologado');
 const after=await (await page.request.get('/api/v1/director/studies/'+f.base)).json();expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toEqual(before.context_sha256);
 await page.setViewportSize({width:390,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);await page.getByRole('button',{name:'Estado',exact:true}).focus();await expect(page.getByRole('button',{name:'Estado',exact:true})).toBeFocused();await page.screenshot({path:out+'/MOBILE390.png'});
});
