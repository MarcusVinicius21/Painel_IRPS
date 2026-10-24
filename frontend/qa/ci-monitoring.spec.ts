import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

test.describe('CI · monitoramento operacional',()=>{
 test.skip(!process.env.IRPS_FCP_OPERATIONAL,'Exige instância operacional explícita; não cria dados fictícios.');
 test('118 alvos, agenda e provedores sem expor credenciais',async({page})=>{
  await page.goto('/');
  const credentials=JSON.parse(fs.readFileSync(path.resolve('../.runtime/operacional-local/acesso-privado.json'),'utf8'));
  await page.getByLabel('Senha de acesso').fill(credentials.password);
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await expect(page.getByText('118 municípios monitorados',{exact:true})).toBeVisible();
  await expect(page.getByText('Monitoramento não comprova filiação ou cobertura completa de compras.')).toBeVisible();
  await expect(page.getByRole('button',{name:'Atualizar agora',exact:true})).toBeEnabled();
  await page.getByText('Conferir fontes e limitações',{exact:true}).click();
  await expect(page.getByRole('cell',{name:'Portal da Transparência',exact:true})).toBeVisible();
  const response=await page.request.get('/api/v1/portfolio/providers');expect(response.status()).toBe(200);
  const provider=(await response.json()).records.find((r:any)=>r.provider==='PORTAL_TRANSPARENCIA');
  expect(provider.operational).toBe(true);expect(JSON.stringify(provider)).not.toContain('chave-api-dados');
  const schedule=await (await page.request.get('/api/v1/portfolio/refresh')).json();expect(schedule.last_run).toBeTruthy();
  for(const width of [390,1672]){
   await page.setViewportSize({width,height:941});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)).toBe(true);
  }
 });
});
