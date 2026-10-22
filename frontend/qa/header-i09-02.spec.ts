import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_REFINAMENTO_I09_I17/I09_02');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();});
test('Topbar conserva identidade e controles verdadeiros',async({page})=>{
 await page.goto('/#/inteligencia?estudo='+f.study+'&etapa=selecao');await expect(page.locator('.dataset-warning')).toBeVisible();await expect(page.getByRole('combobox',{name:'Organização ativa',exact:true})).toBeDisabled();await expect(page.locator('.identity-label')).toHaveAttribute('title',/Equipe de compras A/);await expect(page.getByLabel('Ambiente de testes')).toBeVisible();await expect(page.getByRole('link',{name:'Abrir acompanhamentos',exact:true})).toHaveAttribute('href','#/alertas');
 const warning=(await page.locator('.dataset-warning').boundingBox())!,identity=(await page.locator('.identity-label').boundingBox())!;expect(warning.y).toBeGreaterThanOrEqual(identity.y+identity.height);const crumbs=(await page.locator('.breadcrumbs').boundingBox())!,ribbon=(await page.getByLabel('Ambiente de testes').boundingBox())!;expect(crumbs.y+crumbs.height).toBeLessThanOrEqual(ribbon.y);
 expect((await page.locator('.topbar').boundingBox())!.height).toBe(60);expect((await page.locator('.page-symbol').boundingBox())!.width).toBe(48);expect((await page.locator('.workflow-steps a>span').first().boundingBox())!.width).toBe(32);
 await page.getByRole('button',{name:'Sair',exact:true}).click();await expect(page.getByRole('button',{name:'Equipe de compras A',exact:true})).toBeVisible();
});
test('Ajuda contextual funciona nas seis etapas e devolve foco',async({page})=>{
 for(const stage of ['selecao','historico','planejamento','preparacao','manifestacoes','consolidacao']){await page.goto('/#/inteligencia?estudo='+f.study+'&etapa='+stage);await expect(page.locator('.dataset-warning')).toBeVisible();await page.waitForLoadState('networkidle');const help=page.getByRole('button',{name:'Ajuda',exact:true});await help.focus();await page.keyboard.press('Enter');const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();await expect(dialog.getByRole('link',{name:'Conferir fontes e cobertura',exact:true})).toHaveAttribute('href','#/fontes');await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(help).toBeFocused();}
 await page.goto('/#/inicio?estudo='+f.study);await expect(page.locator('.dataset-warning')).toBeVisible();await page.getByRole('button',{name:'Ajuda',exact:true}).click();await expect(page.getByRole('dialog').getByText(/ausência de registros não significa quantidade zero/)).toBeVisible();
});
test('Etapas mantêm contexto, guardas e significado de navegação',async({page})=>{
 await page.goto('/#/inteligencia?estudo='+f.study+'&etapa=selecao');const steps=page.getByRole('navigation',{name:'Etapas da compra'});await expect(steps).toHaveAttribute('title',/não representam aprovação/);await expect(steps.locator('a')).toHaveCount(6);await steps.getByRole('link',{name:/Análise do histórico/}).click();await expect(page).toHaveURL(new RegExp('estudo='+f.study));await expect(steps.locator('[aria-current=step]')).toContainText('Análise do histórico');
 await page.goto('/#/inteligencia');await page.reload();await expect(page.getByRole('button',{name:'Buscar no catálogo',exact:true})).toBeVisible();await expect(steps.locator('a')).toHaveCount(1);await expect(steps.locator('[aria-disabled=true]')).toHaveCount(5);
});
test('Ajuda, descrição e etapas permanecem acessíveis em390px',async({page})=>{
 await page.setViewportSize({width:390,height:941});await page.goto('/#/inteligencia?estudo='+f.study+'&etapa=selecao');await expect(page.locator('.dataset-warning')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.getByRole('button',{name:'Ajuda',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Ajuda',exact:true})).toBeFocused();fs.mkdirSync(out+'/CAPTURAS/mobile390',{recursive:true});await page.screenshot({path:out+'/CAPTURAS/mobile390/cabecalho.png'});
});

test('42 marcadores respeitam as âncoras específicas das sete referências',async({page})=>{
 const cases=[
  {ref:'00',stage:'selecao',width:1536,height:1024,x:[211,465,686,901,1105,1272],y:[127,126,126,126,126,126]},
  {ref:'01',stage:'historico',width:1672,height:941,x:[232,503,743,975,1201,1385],y:[120,120,119,119,119,119]},
  {ref:'02',stage:'selecao',width:1672,height:941,x:[246,521,775,1019,1259,1476],y:[142,141,141,141,141,141]},
  {ref:'03',stage:'planejamento',width:1672,height:941,x:[229,476,721,959,1190,1388],y:[128,128,128,127,127,127]},
  {ref:'04',stage:'preparacao',width:1672,height:941,x:[231,482,736,976,1209,1419],y:[139,139,139,137,136,136]},
  {ref:'05',stage:'manifestacoes',width:1672,height:941,x:[229,489,737,973,1212,1440],y:[138,137,137,137,137,137]},
  {ref:'06',stage:'consolidacao',width:1672,height:941,x:[231,483,732,980,1212,1438],y:[139,138,138,138,138,137]},
 ];
 for(const c of cases){await page.setViewportSize({width:c.width,height:c.height});await page.goto('/#/'+(c.ref==='01'?'inicio?estudo='+f.study:'inteligencia?estudo='+f.study+'&etapa='+c.stage));await expect(page.locator('.dataset-warning')).toBeVisible();await page.waitForLoadState('networkidle');const boxes=await page.locator('.workflow-steps a>span').evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y}}));expect(boxes).toHaveLength(6);for(let i=0;i<6;i++){expect(Math.abs(boxes[i].x-c.x[i]),c.ref+' marcador '+(i+1)+' X').toBeLessThanOrEqual(2);expect(Math.abs(boxes[i].y-c.y[i]),c.ref+' marcador '+(i+1)+' Y').toBeLessThanOrEqual(2);}}
});
