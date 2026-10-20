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

test('Produto revisado respeita troca de município e abre histórico identificado',async({page})=>{
 const id='11111111-1111-4111-8111-111111111111';
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\?.*/,async route=>{
  const cities=new URL(route.request().url()).searchParams.getAll('municipalities');
  await route.fulfill({json:{records:[{id,name:'Papel A4 · demonstração',category:'Material',unit:'CAIXA',
   classification:'synthetic',members:[{id:'paper-test',version:1}],observed_records:cities.length,
   municipalities:cities,active_months:1,observed_quantity:String(cities.length*5),known_amount:null,
   quantity_complete:true,sources:[]}],total:1}});
 });
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\/.*\/history\?.*/,async route=>{
  const cities=new URL(route.request().url()).searchParams.getAll('municipalities');
  await route.fulfill({json:{product:{id,name:'Papel A4 · demonstração',classification:'synthetic',unit:'CAIXA',members:[{id:'paper-test',version:1}]},
   municipalities:cities.map(code=>({municipality:{ibge:code,name:code==='3131307'?'Ipatinga':'Outra cidade',uf:'MG'},
    observed_records:1,distinct_processes:1,observed_months:['2025-01'],observed_years:[2025],
    observed_quantity:'5',documented_amount:'50',unit_prices:['10'],
    quantity_complete:true,coverage_state:'partial',excluded_from_totals:[],first_observed:'2025-01-10',
    last_observed:'2025-01-10',evidence:[{url:'https://pncp.gov.br/',description:'Demonstração'}]}))}});
 });
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 await page.goto('/#/catalogo-inteligente');
 await expect(page.getByRole('heading',{name:'Catálogo inteligente e cobertura'})).toBeVisible();
 await page.getByLabel('Municípios').selectOption(['3131307']);
 await page.getByRole('button',{name:'Conferir fontes e produtos'}).click();
 await expect(page.getByText('1 municípios').first()).toBeVisible();
 await page.getByRole('button',{name:'Ver por município'}).first().click();
 await expect(page.getByRole('heading',{name:'Histórico por município · Papel A4 · demonstração'})).toBeVisible();
 await expect(page.getByText('Dados fictícios para teste.')).toBeVisible();
 await expect(page.getByRole('region',{name:'Registros observados por município no recorte'}).getByText('Ipatinga/MG').first()).toBeVisible();
 await expect(page.getByText('Outra cidade')).toHaveCount(0);
});

test('Montar licitação separa histórico do cálculo V4',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 const list=await (await page.request.get('/api/v1/scenarios')).json();
 const scenario=await (await page.request.get('/api/v1/scenarios/'+list.records[0].id)).json();
 const ref=scenario.snapshot.items[0];
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\?.*/,route=>route.fulfill({json:{records:[{
  id:'11111111-1111-4111-8111-111111111111',members:[ref],name:'Produto de demonstração',
  classification:'synthetic'}],total:1}}));
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\/.*\/history\?.*/,route=>route.fulfill({json:{
  product:{name:'Produto de demonstração',classification:'synthetic',unit:'UNIDADE'},
  municipalities:scenario.snapshot.participants.map((code:string)=>({municipality:{ibge:code,name:'Município de teste'},
   coverage_state:'partial',observed_quantity:'5',observed_records:1,distinct_processes:1,
   quantity_complete:true,first_observed:'2025-01-10',last_observed:'2025-01-10',evidence:[]}))}}));
 await page.goto('/#/quantidades');
 await expect(page.getByText('Quantidades por município e item',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'O que já foi registrado'})).toBeVisible();
 await expect(page.getByText('Estas quantidades não preenchem o cálculo V4.',{exact:false})).toBeVisible();
 await expect(page.getByText('Quantidades e valores calculados pelo V4',{exact:true})).toBeVisible();
});
