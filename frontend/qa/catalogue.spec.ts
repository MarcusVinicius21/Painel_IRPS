import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

const out=path.resolve('..','.runtime/evidencias/telas');
fs.mkdirSync(out,{recursive:true});

for(const width of [390,1440])test(`Catálogo e cobertura · ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 await page.goto('/#/catalogo-inteligente');
 await expect(page.getByRole('heading',{name:'Catálogo inteligente e cobertura'})).toBeVisible();
 await expect(page.getByText('O que a coleta comprovou')).toBeVisible();
 await page.getByRole('button',{name:'Conferir fontes e produtos'}).click();
 await expect(page.getByText('Órgãos identificados no recorte')).toBeVisible();
 await expect(page.getByText('Ele não mede todas as compras do município',{exact:false})).toBeVisible();
 if(width===1440){
  const normalized=page.waitForResponse(response=>response.url().includes('/catalogue-intelligent/reprocess')&&response.request().method()==='POST');
  await page.getByRole('button',{name:'Reanalisar itens coletados'}).click();
  expect((await normalized).status()).toBe(200);
  await expect(page.getByText('Itens reanalisados.',{exact:false})).toBeVisible();
 }
 const response=await page.request.get('/api/v1/coverage/inventory?start=2025-09-01&end=2025-09-07&municipalities=3131307');
 expect(response.status()).toBe(200);expect((await response.json()).official_phase_completeness_claimed).toBe(false);
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
 expect(overflow.scroll).toBeLessThanOrEqual(overflow.width+1);
 await page.locator('#page-title').scrollIntoViewIfNeeded();
 await page.waitForTimeout(200);
 await page.screenshot({path:path.join(out,`${width}-catalogo-primeira-dobra.png`)});
 await page.screenshot({path:path.join(out,`${width}-catalogo-cobertura.png`),fullPage:width===1440});
 if(width===390){await page.getByText('O que a coleta comprovou').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,'390-catalogo-painel-cobertura.png')});}
 const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
 expect(axe.violations).toEqual([]);expect(errors).toEqual([]);
});
