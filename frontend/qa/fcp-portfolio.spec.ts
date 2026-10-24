import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

test.describe('FCP · operador real e evidências públicas locais',()=>{
 test.skip(!process.env.IRPS_FCP_OPERATIONAL,'Exige instância operacional local explícita; não cria dados de demonstração.');
 test.beforeEach(async({page})=>{
  await page.goto('/');
  const credentials=JSON.parse(fs.readFileSync(path.resolve('../.runtime/operacional-local/acesso-privado.json'),'utf8'));
  await page.getByLabel('Senha de acesso').fill(credentials.password);
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Portfólio CONSORMULTI',exact:true})).toBeVisible();
  await expect(page.getByRole('navigation',{name:'Grupos do portfólio'}).getByRole('button')).toHaveCount(20);
 });
 test('login único, histórico municipal, fornecedor e evidência',async({page})=>{
  const context=await (await page.request.get('/api/v1/auth/context')).json();expect(context.identity_mode).toBe('operational_local');
  await page.getByRole('navigation',{name:'Grupos do portfólio'}).getByRole('button').filter({hasText:'Compra de veículos'}).click();
  await page.getByLabel('Municípios').selectOption(['3131307']);
  await page.getByLabel('Situação da compra').selectOption('homologado');
  await page.getByRole('button',{name:'Aplicar e salvar filtros'}).click();
  await page.getByRole('button',{name:'Compras dos municípios',exact:true}).click();
  await expect(page.getByText('SAINT EMILION', {exact:false}).first()).toBeVisible();
  const evidence=page.getByRole('link',{name:'Abrir evidência oficial'}).first();
  await expect(evidence).toHaveAttribute('href',/^https:\/\/pncp.gov.br\//);
  await page.getByRole('button',{name:'Fornecedores verificados',exact:true}).click();
  await expect(page.getByText('12579490000101',{exact:false}).first()).toBeVisible();
  await page.getByRole('navigation',{name:'Grupos do portfólio'}).getByRole('button').filter({hasText:'Material de informática'}).click();
  await page.getByLabel('Situação da compra').selectOption('publicado_estimado');
  await page.getByLabel('Municípios').selectOption(['3168705']);
  await page.getByRole('button',{name:'Aplicar e salvar filtros'}).click();
  await page.getByRole('button',{name:'Compras dos municípios',exact:true}).click();
  await expect(page.getByText('17112673000136',{exact:false}).first()).toBeVisible();
  await page.reload();await expect(page.getByLabel('Municípios')).toHaveValues(['3168705']);
  expect((await (await page.request.get('/api/v1/portfolio/preferences')).json()).payload.group).toBe('17');
 });
 test('código com preço oficial, persistência e falha secundária independente',async({page})=>{
  await page.route('https://catmat.com.br/**',r=>r.abort());
  await page.getByRole('navigation',{name:'Grupos do portfólio'}).getByRole('button').filter({hasText:/^15\s*Café/}).click();
  await page.getByLabel('Código ou descrição').fill('463562');
  await page.getByLabel('Situação do código').selectOption('true');
  await page.getByLabel('Subgrupo técnico').selectOption('cafe_produto');
  await page.getByRole('button',{name:'Aplicar e salvar filtros'}).click();
  await page.getByRole('button',{name:'Abrir ficha 463562'}).first().click();
  await page.getByRole('button',{name:'Consultar preços nacionais',exact:true}).click();
  await expect(page.getByRole('link',{name:/Arquivo oficial/}).first()).toBeVisible({timeout:60000});
  await expect(page.getByText('Preços nacionais não são automaticamente compras', {exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Compras dos municípios',exact:true}).click();
  await expect(page.getByText('Sem vínculo encontrado neste recorte', {exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Fontes e cobertura',exact:true}).click();
  await expect(page.getByText('A exportação devolveu datas fora do período solicitado.',{exact:false})).toBeVisible();
 });
 test('responsividade, foco e acessibilidade do conteúdo novo',async({page})=>{
  const findings=[];
  for(const width of [320,390,1536]){
   await page.setViewportSize({width,height:1000});await page.waitForLoadState('networkidle');
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)).toBe(true);
   await page.getByLabel('Código ou descrição').focus();await expect(page.getByLabel('Código ou descrição')).toBeFocused();
   const scan=await new AxeBuilder({page}).include('.portfolio-layout').analyze();
   findings.push({width,violations:scan.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}))});
   expect(scan.violations.filter(v=>v.impact==='critical'||v.impact==='serious')).toEqual([]);
  }
  fs.mkdirSync('../.runtime/irps-fcp',{recursive:true});fs.writeFileSync('../.runtime/irps-fcp/accessibility.json',JSON.stringify(findings,null,2));
 });
});
