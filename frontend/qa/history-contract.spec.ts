import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
// Real API/PostgreSQL fixtures from backend/tests/prepare_history_browser.py.
const fixture=JSON.parse(fs.readFileSync(process.env.IRPS_HISTORY_BROWSER_FIXTURE||path.resolve('../.runtime/history-contract/browser-fixture.json'),'utf8'));
const out=path.resolve('../.runtime/history-contract/screenshots');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
for(const surface of ['inicio','inteligencia'])for(const state of ['known','unknown','empty','zero','legacy']){
 test(`Indicadores históricos: ${surface} / ${state}`,async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();
  await expect(page.locator('.identity-label')).toContainText('Equipe de compras A');
  const sid=fixture[state],endpoint='/api/v1/director/studies/'+sid;
  const before=await (await page.request.get(endpoint)).json();
  await page.goto(`/#/${surface}?estudo=${sid}&etapa=selecao`);
  await expect(page.getByText('Demonstração fictícia · sem necessidade ou confirmação oficial.',{exact:true})).toBeVisible();
  const metric=(label:string)=>page.locator('.executive-metrics > div').filter({has:page.getByText(label,{exact:true})}).first().locator('dd');
  if(state==='known'){
   await expect(metric('Municípios com registros')).toContainText('1');
   await expect(metric('Processos identificados')).toContainText('1');
   await expect(metric('Quantidade documentada')).toContainText('3');
   await expect(metric('Quantidade documentada')).toContainText('CAIXA');
   await expect(metric('Valor documentado')).toContainText(/R\$\s*30,00/);
   await expect(page.getByText('Totais parciais dos registros encontrados.',{exact:false})).toBeVisible();
   await expect(page.locator('.historical-charts dl dd')).toHaveCount(4);
   await expect(page.locator('.historical-charts dl dd').first()).toContainText('3');
   await page.evaluate(()=>document.fonts.ready);fs.mkdirSync(out,{recursive:true});
   await page.screenshot({path:path.join(out,surface+'-1672x941.png')});
   expect(await page.evaluate(()=>devicePixelRatio)).toBe(1);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
   if(surface==='inteligencia'){
    await page.goto(`/#/inteligencia?estudo=${sid}&etapa=historico`);
    await expect(page.locator('.municipal-history-panel')).toBeVisible();
    await expect(page.locator('.historical-charts dl dd')).toHaveCount(4);
    await page.screenshot({path:path.join(out,'historico-1672x941.png')});
   }
  }else if(state==='zero'){
   await expect(metric('Quantidade documentada')).toHaveText(/^0CAIXA/);
   await expect(metric('Processos identificados').locator('[title="Informação não disponível"]')).toBeVisible();
  }else{
   for(const label of ['Quantidade documentada','Valor documentado'])await expect(metric(label).locator('[title="Informação não disponível"]')).toBeVisible();
   if(state==='legacy')await expect(page.locator('.historical-charts dl')).toHaveCount(0);
   else{await expect(page.locator('.historical-charts dl dd')).toHaveCount(4);await expect(page.locator('.historical-charts dl dd').first()).toContainText('Não disponível');}
   if(state==='legacy')await expect(page.getByText('Estudo anterior: resumo agregado indisponível.',{exact:false})).toBeVisible();
   if(state==='empty')await expect(metric('Municípios com registros')).toContainText('0');
  }
  const after=await (await page.request.get(endpoint)).json();
  expect(after.payload).toEqual(before.payload);expect(after.context_sha256).toBe(before.context_sha256);
  expect(errors).toEqual([]);
 });
}
