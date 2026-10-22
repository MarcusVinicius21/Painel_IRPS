import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test('Grade consulta origens distintas e não aplica ajuste manual ou em lote',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+f.study+'&etapa=planejamento');await expect(page.locator('.dataset-warning')).toBeVisible();
 const before=await (await page.request.get('/api/v1/director/studies/'+f.study+'/register')).json(),mutations:string[]=[];page.on('request',r=>{if(!['GET','HEAD'].includes(r.method())&&r.url().includes('/api/v1/'))mutations.push(r.url());});
 const grid=page.locator('.municipal-history-panel');for(const name of ['Histórico observado · 12 meses','Necessidade calculada · V4','Sugestão do consórcio','Confirmação municipal'])await expect(grid.getByRole('columnheader',{name,exact:true})).toBeVisible();await expect(grid.locator('input[type=number]')).toHaveCount(0);await expect(grid).toContainText('Dados insuficientes para cálculo');await expect(grid).toContainText('Ajustes em lote indisponíveis');
 await page.getByText('Ajustes e comparação com a meta',{exact:true}).click();await expect(grid).toContainText('dependem de definição e autorização institucional');await expect(grid).toContainText('Diferenças percentuais e subtotais ficam indisponíveis');
 expect(await (await page.request.get('/api/v1/director/studies/'+f.study+'/register')).json()).toEqual(before);expect(mutations).toEqual([]);
 await page.setViewportSize({width:390,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
