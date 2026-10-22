import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test('Documentos reais selecionáveis, estados e lotes apenas informativos',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+f.study+'&etapa=preparacao');await expect(page.locator('.document-choices')).toBeVisible();
 for(const [kind,label] of [['formulario','Formulário municipal'],['procedimento','Procedimento de IRP'],['planilha','Planilha de itens e municípios'],['especificacoes','Anexo de especificações']]){
  const btn=page.locator('.document-choices').getByRole('button',{name:label,exact:true});await btn.click();await expect(page.getByLabel('Documento a preparar',{exact:true})).toHaveValue(kind);await expect(btn).toHaveAttribute('aria-pressed','true');await expect(btn.locator('svg')).toHaveCount(1);
 }
 const posts:string[]=[];page.on('request',r=>{if(r.method()==='POST')posts.push(r.url());});await page.getByText('Lotes · recurso indisponível',{exact:true}).click();await expect(page.locator('.optional-lots')).toContainText('nenhum lote será criado automaticamente');expect(posts).toEqual([]);await expect(page.getByLabel('Documento a preparar',{exact:true}).locator('option[value=lotes]')).toHaveCount(0);
 await page.setViewportSize({width:390,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
