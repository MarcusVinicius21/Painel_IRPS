import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/similar-i04-05/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I04_05/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
async function open(p:any){await p.goto('/index.html#/inteligencia?estudo='+f.base+'&etapa=selecao&aba=similares');await expect(p.getByRole('tab',{name:'Itens similares',exact:true})).toHaveAttribute('aria-selected','true');await p.evaluate(()=>document.fonts.ready);}
async function shot(p:any,n:string){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,n+'.png')});}
test('Equivalência persistida mostra versões, revisão e links sem mudar o estudo',async({page})=>{
 const url='/api/v1/director/studies/'+f.base,before=await(await page.request.get(url)).json();await open(page);
 const panel=page.getByRole('tabpanel',{name:'Itens similares',exact:true});await expect(panel.locator('.similar-items-content>ul>li')).toHaveCount(2);
 await panel.getByText('Responsável, versão e provas da equivalência',{exact:true}).click();await expect(panel).toContainText(f.product_id);await expect(panel).toContainText('Dados gerados para testar filtros');
 const link=panel.getByRole('link',{name:'Abrir registro deste item · versão 1',exact:true}).first();await expect(link).toHaveAttribute('target','_blank');
 const popup=page.waitForEvent('popup');await link.click();const opened=await popup;await opened.waitForLoadState();await expect(opened).toHaveURL(/#\/processo\?id=/);await expect(opened.locator('tbody tr')).toHaveCount(1);await opened.close();
 expect((await(await page.request.get(url)).json()).payload).toEqual(before.payload);await expect(page).toHaveURL(new RegExp('estudo='+f.base));await shot(page,'revisao-e-registros');
});
test('Aba acessível por teclado e recarregamento mantém visualização',async({page})=>{
 await open(page);await page.getByRole('tab',{name:'Histórico por município',exact:true}).focus();await page.keyboard.press('End');await expect(page.getByRole('tab',{name:'Itens similares',exact:true})).toBeFocused();await expect(page.getByRole('tabpanel')).toContainText('Membros da mesma equivalência revisada');await page.reload();await expect(page.getByRole('tab',{name:'Itens similares',exact:true})).toHaveAttribute('aria-selected','true');await shot(page,'02-similares');
});
test('Falha de consulta não exibe candidatos ou provas anteriores',async({page})=>{
 await page.route('**/director/products/*/similar?*',r=>r.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:{message:'Os itens precisam de nova conferência.'}})}));await open(page);await expect(page.getByRole('tabpanel')).toContainText('Não foi possível conferir as equivalências');await expect(page.locator('.similar-items-content')).toHaveCount(0);await shot(page,'falha-conferencia');
});
test('Sem vínculo selecionado mantém vazio e não escolhe candidato por nome',async({page})=>{
 await open(page);await page.getByLabel('Histórico tecnicamente vinculado',{exact:true}).selectOption('');await expect(page.getByRole('tabpanel')).toContainText('Sem equivalência revisada para este item');await expect(page.getByLabel('Histórico tecnicamente vinculado',{exact:true})).toHaveValue('');await shot(page,'sem-equivalencia');
});
test('Múltiplos vínculos não geram escolha silenciosa',async({page})=>{
 await page.route('**/national-catalogue/*/*/links',async route=>{const response=await route.fetch(),data=await response.json();data.records=[...data.records,...data.records.map((r:any)=>({...r,product_id:'00000000-0000-0000-0000-000000000123'}))];await route.fulfill({response,json:data});});
 await page.goto('/index.html#/inteligencia?codigo='+f.code+'&catalogo='+f.snapshot_id+'&etapa=selecao&aba=similares');await expect(page.getByRole('tabpanel')).toBeVisible();await expect(page.getByLabel('Histórico tecnicamente vinculado',{exact:true})).toHaveValue('');await expect(page.getByRole('tabpanel')).toContainText('Há mais de uma equivalência vinculada');
});
test('Mobile 390 preserva acesso e não alarga a página',async({page})=>{
 await page.setViewportSize({width:390,height:941});await open(page);await expect(page.locator('.similar-items-content')).toBeVisible();await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.getByRole('tab',{name:'Itens similares',exact:true}).focus();await expect(page.getByRole('tab',{name:'Itens similares',exact:true})).toBeFocused();await shot(page,'similares-390');
});
