import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
const evidence=path.resolve('../.runtime/pixel-perfect/browser');
const expected=JSON.parse(fs.readFileSync(path.resolve('../docs/IRPS_REFINAMENTO_PIXEL_PERFECT/inventario.json'),'utf8')).expected_boxes;
const stages=['selecao','inicio','selecao','planejamento','preparacao','manifestacoes','consolidacao'];
for(let screen=0;screen<7;screen++)test(`Referência 0${screen}: caixas medidas, estados vazios e quatro tamanhos responsivos`,async({page})=>{
 test.setTimeout(180000);fs.mkdirSync(evidence,{recursive:true});const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();
 const snapshot=await (await page.request.get('/api/v1/national-catalogue?q=150682&limit=25')).json();const item=snapshot.records.find((r:any)=>r.code==='150682');expect(item).toBeTruthy();
 const municipalities=(await (await page.request.get('/api/v1/municipalities')).json()).records.filter((r:any)=>r.uf==='MG').slice(0,8).map((r:any)=>r.ibge);
 const csrf=(await page.context().cookies()).find(c=>c.name==='irps_csrf')!.value;
 const response=await page.request.post('/api/v1/director/studies',{headers:{'x-csrf-token':csrf},data:{classification:'synthetic',snapshot_id:item.snapshot_id,code:item.code,name:item.name,specification:item.name,unit:'unidade',category:'veiculo',quantity_step:'1',municipalities,phase:'homologado',start:'2025-01-01',end:'2026-10-21',preliminary_target:'200',target_justification:'Meta fictícia exclusiva para teste de composição. Não representa demanda municipal.',technical_evidence:'Conferência fictícia exclusiva do teste visual, sem validade institucional.',technical_confirmed:true}});expect(response.status()).toBe(201);const study=await response.json();
 const url=screen===1?`/#/inicio?estudo=${study.id}`:`/#/inteligencia?estudo=${study.id}&etapa=${stages[screen]}`;
 const results:any[]=[];
 for(const width of [screen===0?1536:1672,320,390,768,1024]){
  await page.setViewportSize({width,height:width>1400?(screen===0?1024:941):1000});await page.goto(url);await expect(page.locator('#page-title')).toBeVisible();
  if(screen===1)await expect(page.locator('.executive-item-slot .selected-item')).toBeVisible();else await expect(page.locator('.selected-item:visible,.workflow-preparation-layout:visible,.irp-register:visible').first()).toBeVisible();
  await page.evaluate(()=>document.fonts.ready);await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important}'});await page.evaluate(()=>window.scrollTo(0,0));
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
  if(screen===1){await expect(page.getByRole('combobox',{name:'Situação do gráfico'})).toHaveValue('homologado');await expect(page.getByRole('link',{name:'Usar os dados no planejamento'})).toHaveAttribute('href',`#/inteligencia?estudo=${study.id}&etapa=planejamento`);}
  if(width>1400){for(const [selector,x,y,w,h] of expected['0'+screen]){const box=await page.locator(selector).first().boundingBox();expect(box,selector).not.toBeNull();const deltas=[box!.x-x,box!.y-y,box!.width-w,box!.height-h];results.push({selector,box,expected:{x,y,width:w,height:h},deltas});expect(Math.max(...deltas.map(Math.abs)),selector).toBeLessThanOrEqual(4);}}
  await page.screenshot({path:path.join(evidence,`0${screen}-${width}.png`)});
 }
 fs.writeFileSync(path.join(evidence,`0${screen}-assertions.json`),JSON.stringify({synthetic:true,geometry:'main boxes only, ±4px; not a pixel-perfect certification',results,errors},null,2));expect(errors).toEqual([]);
});
