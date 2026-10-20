import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const out=path.resolve('..','.runtime/evidencias');
for(const width of [390,1440])test(`Rotas conectadas e linguagem · ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:950});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 const csrf=await page.evaluate(()=>decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith('irps_csrf='))?.slice(10)||''));
 const created=await page.request.post('/api/v1/scenarios/synthetic',{data:{participants:3,items:5,title:'Verificação de navegação · dados fictícios'},headers:{'X-CSRF-Token':csrf}});expect(created.status()).toBe(201);const sid=(await created.json()).id;expect((await page.request.post('/api/v1/scenarios/'+sid+'/calculate',{headers:{'X-CSRF-Token':csrf}})).status()).toBe(200);
 await page.reload();await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');const records=[];
 const routes=['inicio','oportunidades','catalogo-inteligente','coleta-oportunidades','pesquisa','resultados','produto?item=papel','municipio?cidade=3131307','pagamentos','comparar','necessidades','licitacao','participantes','itens','quantidades','distribuicao','precos','revisao','relatorios','memoria','negocio','documentos','fontes','alertas','administracao'];
 const official=await (await page.request.get('/api/v1/purchases?dataset=official&limit=1')).json();if(official.records.length)routes.push('processo?id='+official.records[0].id);
 for(const route of routes){await page.evaluate(next=>{location.hash='/'+next;},route);await expect(page.locator('#page-title')).toBeVisible();await page.waitForTimeout(60);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);expect(overflow,route).toBe(false);const text=await page.locator('h1,h2,button').allInnerTexts();expect(text.join(' ')).not.toMatch(/\b(fixture|pipeline|string|debug|deploy|nulo)\b/i);records.push({route,title:await page.locator('#page-title').innerText(),overflow});}
 await page.goto('/#/itens');await page.screenshot({path:path.join(out,`telas/${width}-itens.png`),fullPage:true});await page.goto('/#/precos');await page.screenshot({path:path.join(out,`telas/${width}-precos.png`),fullPage:true});await page.goto('/#/distribuicao');await page.screenshot({path:path.join(out,`telas/${width}-distribuicao.png`),fullPage:true});
 fs.writeFileSync(path.join(out,`rotas-${width}.json`),JSON.stringify({records,page_errors:errors},null,2));expect(errors).toEqual([]);
});
