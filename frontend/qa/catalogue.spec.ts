import {test,expect} from '@playwright/test';
import type {Row} from '../src/api';
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
 await page.getByRole('button',{name:'Calcular quantidades'}).click();
 await expect(page.getByText('Quantidades e valores calculados pelo V4',{exact:true})).toBeVisible();
});

test('Produtos continuam visíveis quando a consulta de cobertura falha',async({page})=>{
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\?.*/,route=>route.fulfill({json:{records:[{
  id:'11111111-1111-4111-8111-111111111111',name:'Papel A4 revisado',category:'Material',unit:'CAIXA',
  observed_records:2,municipalities:['3131307'],active_months:1,observed_quantity:'20',quantity_complete:true,
  known_amount:'100',members:[]}],total:1}}));
 await page.route(/\/api\/v1\/coverage\/inventory\?.*/,route=>route.fulfill({status:503,json:{detail:{message:'Fonte indisponível agora.'}}}));
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 await page.goto('/#/catalogo-inteligente');
 await expect(page.getByText('Papel A4 revisado').first()).toBeVisible();
 await expect(page.getByText('Cobertura não verificada para todo o período.',{exact:false})).toBeVisible();
});

test('Período acima de cinco anos mantém produtos sem prometer cobertura',async({page})=>{
 let coverageRequests=0;
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\?.*/,route=>route.fulfill({json:{records:[{
  id:'11111111-1111-4111-8111-111111111111',name:'Produto de longo período',category:'Material',unit:'CAIXA',
  observed_records:1,municipalities:['3131307'],active_months:1,observed_quantity:'10',quantity_complete:true,
  known_amount:'50',members:[]}],total:1}}));
 await page.route(/\/api\/v1\/coverage\/inventory\?.*/,route=>{coverageRequests++;return route.fulfill({json:{records:[],buyer_inventory:[]}});});
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 await page.goto('/#/catalogo-inteligente');
 await expect(page.getByText('Produto de longo período').first()).toBeVisible();
 const before=coverageRequests;
 await page.getByLabel('De',{exact:true}).fill('2019-01-01');
 await page.getByRole('button',{name:'Conferir fontes e produtos'}).click();
 await expect(page.getByText('Cobertura não verificada para todo o período.',{exact:false})).toBeVisible();
 expect(coverageRequests).toBe(before);
 await expect(page.getByText('Produto de longo período').first()).toBeVisible();
});

test('Planejamento mostra o V4 após a cidade 20 e respeita item e revisão',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
 await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
 const csrf=await page.evaluate(()=>decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith('irps_csrf='))?.slice(10)||''));
 const headers={'X-CSRF-Token':csrf};
 const createdResponse=await page.request.post('/api/v1/scenarios/synthetic',{headers,data:{participants:30,items:2}});
 expect(createdResponse.status()).toBe(201);
 const scenario=await createdResponse.json();
 const calculatedResponse=await page.request.post('/api/v1/scenarios/'+scenario.id+'/calculate',{headers});
 expect(calculatedResponse.status()).toBe(200);
 const calculated=await calculatedResponse.json();
 const refs=scenario.snapshot.items;
 let scenarioLists=0;
 await page.route('**/api/v1/scenarios',async route=>{
  scenarioLists++;
  const response=await route.fetch();const body=await response.json();
  await route.fulfill({response,json:{records:[scenario,...body.records.filter((row:Row)=>row.id!==scenario.id)]}});
 });
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\?.*/,route=>route.fulfill({json:{records:refs.map((ref:Row,index:number)=>({
  id:`11111111-1111-4111-8111-${String(index+1).padStart(12,'0')}`,members:[ref],
  name:'Produto de teste '+(index+1),classification:'synthetic'}))}}));
 await page.route(/\/api\/v1\/catalogue-intelligent\/products\/.*\/history\?.*/,route=>route.fulfill({json:{
  product:{name:'Produto de teste',classification:'synthetic',unit:'UNIDADE'},
  municipalities:scenario.snapshot.participants.map((code:string,index:number)=>({
   municipality:{ibge:code,name:'Cidade de teste '+(index+1)},coverage_state:'demonstration',
   observed_quantity:'1',observed_records:1,distinct_processes:1,quantity_complete:true,
   first_observed:'2025-01-01',last_observed:'2025-01-01',evidence:[]}))}}));
 const rowFor=async(ref:Row)=>{
  const query=new URLSearchParams({item_id:ref.id,item_version:String(ref.version)});
  query.append('municipalities',scenario.snapshot.participants[24]);
  const response=await page.request.get('/api/v1/calculations/'+calculated.id+'/item-lines?'+query);
  expect(response.status()).toBe(200);return (await response.json()).records[0];
 };
 await page.goto('/#/quantidades');await page.reload();
 await expect.poll(()=>scenarioLists).toBeGreaterThan(0);
 await expect.poll(()=>page.getByLabel('Cenário salvo').locator('option').evaluateAll(options=>options.map(option=>(option as HTMLOptionElement).value))).toContain(scenario.id);
 await page.getByLabel('Cenário salvo').selectOption(scenario.id);
 await expect(page.getByRole('heading',{name:'O que já foi registrado'})).toBeVisible();
 const section=page.getByRole('region',{name:'Histórico observado por município'});
 for(let index=0;index<3;index++)await section.getByRole('button',{name:'Próxima página'}).click();
 const first=await rowFor(refs[0]);
 await expect(section.locator('.desktop-records:visible tr').filter({hasText:'Cidade de teste 25'})).toContainText(String(Number(first.quantity)));
 await page.getByLabel('Item em análise').selectOption(refs[1].id);
 const second=await rowFor(refs[1]);
 await expect(section.locator('.desktop-records:visible tr').filter({hasText:'Cidade de teste 25'})).toContainText(String(Number(second.quantity)));
 const body=structuredClone(scenario.snapshot);delete body.review;delete body.distribution_confirmation;
 const changed=await page.request.put('/api/v1/scenarios/'+scenario.id,{headers:{...headers,'If-Match':String(scenario.current_revision)},data:body});
 expect(changed.status()).toBe(200);
 await page.reload();
 await page.getByLabel('Cenário salvo').selectOption(scenario.id);
 await expect(page.getByRole('heading',{name:'O que já foi registrado'})).toBeVisible();
 await expect(page.getByText('Cálculo pendente nesta versão').first()).toBeVisible();
});
