import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const savedFixture=JSON.parse(fs.readFileSync(path.resolve(process.env.IRPS_SHELL_FIXTURE||'../.runtime/history-filters/browser-fixture.json'),'utf8'));
const fixture={...savedFixture,base:savedFixture.base||savedFixture.study};
const output=path.resolve(process.env.IRPS_SHELL_SCREENSHOTS||'../.runtime/shell-i03-01/screenshots');
const sections=['inicio','inteligencia','oportunidades','licitacao','documentos','comparar','pesquisa','catalogo-inteligente','relatorios','administracao'];
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();
test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
test.afterEach(async({page})=>{expect(errors.get(page)).toEqual([]);});
async function study(page:any,route='inteligencia',stage='selecao'){await page.goto('/#/'+route+'?estudo='+fixture.base+'&etapa='+stage);await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.getByRole('heading',{name:'Item selecionado',exact:true})).toBeVisible();}

test('Shell mantém destinos, identidade e avisos',async({page})=>{
 await study(page);expect(await page.locator('.rail .shell-nav-entry>a').evaluateAll(as=>as.map(a=>a.getAttribute('href')!.split('?')[0]))).toEqual(sections.map(s=>'#/'+s));await expect(page.locator('.rail nav a.active')).toHaveAttribute('href',new RegExp('^#/inteligencia\\?estudo='));await expect(page.locator('.organization-switch')).toBeDisabled();await expect(page.getByLabel('Ambiente de testes')).toBeVisible();
 await page.getByRole('link',{name:'Abrir acompanhamentos',exact:true}).click();await expect(page).toHaveURL(/#\/alertas$/);await expect(page.locator('.rail nav a.active')).toHaveAttribute('href','#/alertas');await expect(page.locator('#page-title')).toBeVisible();await page.locator('.identity-label').click();await expect(page).toHaveURL(/#\/administracao$/);await expect(page.locator('#page-title')).toBeVisible();await page.locator('.brand').click();await expect(page).toHaveURL(/#\/inicio$/);
});
test('Stepper preserva estudo, guardas e etapa',async({page})=>{
 await study(page);const steps=page.getByRole('navigation',{name:'Etapas da compra'});await expect(steps.locator('a')).toHaveCount(6);await steps.getByRole('link',{name:'Análise do histórico',exact:false}).click();await expect(page).toHaveURL(new RegExp('estudo='+fixture.base));await expect(steps.locator('[aria-current=step]')).toContainText('Análise do histórico');await expect(page.getByLabel('Fonte',{exact:true})).toBeVisible();
 await page.goto('/#/inteligencia');await page.reload();await expect(page.getByRole('button',{name:'Buscar no catálogo',exact:true})).toBeVisible();await expect(steps.locator('.step-unavailable[aria-disabled=true]')).toHaveCount(5);await expect(steps.locator('a')).toHaveCount(1);await expect(steps).toHaveAttribute('title',/não representam aprovação/);
});
test('Teclado, salto ao conteúdo e retorno de foco do menu',async({page})=>{
 await study(page);const skip=page.getByRole('link',{name:'Ir para o conteúdo',exact:true});await skip.focus();await page.keyboard.press('Tab');await expect(page.locator('.brand')).toBeFocused();await page.keyboard.press('Shift+Tab');await expect(skip).toBeFocused();await page.keyboard.press('Enter');await expect(page.locator('#conteudo')).toBeFocused();await page.setViewportSize({width:925,height:900});const menu=page.getByRole('button',{name:'Abrir navegação completa',exact:true});await expect(menu).toBeVisible();await menu.focus();await page.keyboard.press('Enter');await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('button',{name:'Fechar painel',exact:true})).toBeFocused();await page.keyboard.press('Tab');await expect(page.getByRole('dialog').getByRole('link',{name:'Início',exact:true})).toBeFocused();await page.keyboard.press('Escape');await expect(menu).toBeFocused();await expect(page.getByRole('dialog')).toHaveCount(0);
});
for(const width of [390,768,925,950,1024,1536,1672])test('Sem overflow e navegação em '+width+' px',async({page})=>{
 await page.setViewportSize({width,height:width===1536?1024:941});await study(page);
 for(const route of ['inteligencia','inicio']){if(route==='inicio')await study(page,route,'historico');await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await expect(page.getByLabel('Ambiente de testes')).toBeVisible();
 if(width<=950){await expect(page.getByRole('navigation',{name:'Navegação mobile'})).toBeVisible();await expect(page.getByRole('button',{name:'Abrir navegação completa',exact:true})).toBeVisible();}else{await expect(page.locator('.rail')).toBeVisible();const box=await page.locator('.rail').boundingBox();expect(box!.width).toBe(width>=1600?213:194);}
 const title=await page.locator('#page-title').boundingBox();expect(title!.x).toBeGreaterThanOrEqual(0);expect(title!.x+title!.width).toBeLessThanOrEqual(width);fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,route+'-'+width+'.png')});}
});
