import {test,expect} from '@playwright/test';
import fs from 'node:fs';

test.use({launchOptions:{chromiumSandbox:true},viewport:{width:1672,height:941},deviceScaleFactor:1});
test('consulta anual real preserva origens, unidades e ausência de preços',async({page,baseURL})=>{
 test.skip(process.env.IRPS_ANNUAL_REAL!=='1','Somente instância operacional local explicitamente selecionada.');
 test.setTimeout(240000);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('chrome://version');expect(await page.locator('#command_line').innerText()).not.toContain('--no-sandbox');
 await page.goto('/');await page.getByLabel('Senha de acesso').fill(JSON.parse(fs.readFileSync('../.runtime/operacional-local/acesso-privado.json','utf8')).password);
 await page.getByRole('button',{name:'Entrar',exact:true}).click();await page.locator('.irps-shell').waitFor();
 const identity=await(await page.request.get('/api/v1/auth/context')).json();expect(identity.identity_mode).toBe('operational_local');
 const evidence:any[]=[];
 for(const [code,snapshot,total] of [['14729','ac3d44be-de3b-4566-835a-ea74568bd61a',1290],['463700','eba714f4-7f7d-40d1-8a6c-d83cda77b536',89],['10006','eba714f4-7f7d-40d1-8a6c-d83cda77b536',0]] as const){
  await page.goto('/#/inteligencia?catalogo='+snapshot+'&codigo='+code+'&etapa=historico');
  const panel=page.locator('.official-prices');await panel.waitFor();
  await expect(panel.locator('p').first()).toContainText(code);
  const response=page.waitForResponse(r=>r.url().includes('/consolidated-prices?')&&r.url().includes('start=2025-10-01')&&r.url().includes('code='+code),{timeout:90000});
  await panel.getByRole('button',{name:'Consultar últimos 12 meses fechados'}).click();
  const api=await response;expect(api.status()).toBe(200);const data=await api.json();expect(data.total_records_reported).toBe(total);
  expect(data.coverage.months_reconciled).toHaveLength(12);expect(data.source_kind).toBe('monthly_consolidated');expect(data.municipal_coverage_claimed).toBe(false);
  await expect(panel.getByText('Consultando preços no Compras.gov.br… O histórico PNCP continua disponível abaixo.',{exact:true})).toBeHidden();
  await panel.locator('.monthly-coverage summary').click();await expect(panel.locator('.monthly-coverage tbody tr')).toHaveCount(12);
  if(!total)await expect(panel).toContainText('Isso não significa que o item nunca foi comprado.');
  else {
   expect(data.records).toHaveLength(10);expect(new Set(data.records.map((r:any)=>r.source_key)).size).toBe(10);
   const second=page.waitForResponse(r=>r.url().includes('/consolidated-prices?')&&r.url().includes('page=2'));
   await panel.getByRole('button',{name:'Próximos preços',exact:true}).click();expect((await second).status()).toBe(200);
   await expect(panel.getByRole('status').filter({hasText:'Página 2'})).toBeVisible();
   if(code==='463700'){
    for(let p=3;p<=9;p++){
     const next=page.waitForResponse(r=>r.url().includes('/consolidated-prices?')&&r.url().includes('page='+p));
     await panel.getByRole('button',{name:'Próximos preços',exact:true}).click();const last=await(await next).json();
     if(p===9){expect(last.records).toHaveLength(9);expect(last.has_next_page).toBe(false);}
    }
    await expect(panel.getByRole('button',{name:'Próximos preços',exact:true})).toBeDisabled();
   }
  }
  await panel.screenshot({path:'../.runtime/irps-12-meses/R3_04-'+code+'.png'});
  evidence.push({code,status:api.status(),total,months:12,source:data.source_kind,statistics:data.statistics});
 }
 await page.setViewportSize({width:390,height:844});
 await page.locator('.official-prices').screenshot({path:'../.runtime/irps-12-meses/R3_04-mobile.png'});
 expect(errors).toEqual([]);fs.writeFileSync('../.runtime/irps-12-meses/R3_04-browser.json',JSON.stringify({baseURL,sandbox:true,identity:identity.identity_mode,errors,evidence},null,2));
});
