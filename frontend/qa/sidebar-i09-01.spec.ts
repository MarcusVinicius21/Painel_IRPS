import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const fixture=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_REFINAMENTO_I09_I17/I09_01');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
test.beforeEach(async({page})=>{await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/#/inteligencia?estudo='+fixture.study+'&etapa=selecao');await expect(page.locator('.dataset-warning')).toBeVisible();});

test('Onze destinos da referência e ferramentas anteriores continuam reais',async({page})=>{
 const rail=page.locator('.rail');
 await expect(rail.locator('.shell-nav-entry>a')).toHaveText(['Início','Inteligência e Planejamento','Oportunidades','Planejamento (V4)','Documentos','Municípios','Histórico de Compras','Catálogo Nacional','Relatórios','Configurações']);
 await expect(rail.getByRole('button',{name:'IRP',exact:true})).toHaveAttribute('aria-expanded','false');
 const links=await rail.locator('.shell-nav-entry>a').evaluateAll(as=>as.map(a=>a.getAttribute('href')!));
 for(const href of links){await page.goto('/'+href);await expect(page.locator('#page-title')).toBeVisible();await expect(page.locator('#page-title')).not.toHaveText('Esta página não foi encontrada');}
 const more=rail.locator('.shell-extra-tools');await more.locator('summary').click();
 const extras=await more.locator('a').evaluateAll(as=>as.map(a=>a.getAttribute('href')!));
 expect(extras).toEqual(['#/negocio','#/necessidades','#/fontes','#/alertas']);
 for(const href of extras){await page.goto('/'+href);await expect(page.locator('#page-title')).toBeVisible();await expect(page.locator('#page-title')).not.toHaveText('Esta página não foi encontrada');}
});

test('IRP preserva estudo nas três etapas e explica ausência de contexto',async({page})=>{
 const rail=page.locator('.rail'),toggle=rail.getByRole('button',{name:'IRP',exact:true});await toggle.focus();await page.keyboard.press('Enter');await expect(toggle).toHaveAttribute('aria-expanded','true');
 for(const [name,stage] of [['Preparação da IRP','preparacao'],['Manifestações','manifestacoes'],['Consolidação','consolidacao']]){await rail.getByRole('link',{name,exact:true}).click();await expect(page).toHaveURL(new RegExp('estudo='+fixture.study+'&etapa='+stage));await expect(page.locator('.dataset-warning')).toBeVisible();await expect(rail.getByRole('link',{name,exact:true})).toHaveAttribute('aria-current','page');}
 await page.goto('/#/inteligencia');await page.reload();await rail.getByRole('button',{name:'IRP',exact:true}).click();await expect(rail.getByText('Selecione um estudo para preparar a IRP.')).toBeVisible();await expect(rail.getByRole('link',{name:'Selecionar um item',exact:true})).toHaveAttribute('href','#/inteligencia');
});

test('Geometria da sidebar, foco e menu mobile390',async({page})=>{
 const rail=page.locator('.rail');const box=await rail.boundingBox();expect(box!.x).toBe(0);expect(box!.width).toBe(213);
 await page.keyboard.press('Tab');await rail.getByRole('button',{name:'IRP',exact:true}).focus();await expect(rail.getByRole('button',{name:'IRP',exact:true})).toBeFocused();expect(await rail.getByRole('button',{name:'IRP',exact:true}).evaluate(e=>getComputedStyle(e).outlineStyle)).not.toBe('none');
 await page.setViewportSize({width:390,height:941});await expect(rail).toBeHidden();const trigger=page.getByRole('button',{name:'Abrir navegação completa',exact:true});await trigger.focus();await page.keyboard.press('Enter');const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();await dialog.getByRole('button',{name:'IRP',exact:true}).click();await dialog.getByRole('link',{name:'Manifestações',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(page).toHaveURL(/etapa=manifestacoes/);await expect(page.locator('#page-title')).toBeFocused();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);fs.mkdirSync(out+'/CAPTURAS/mobile390',{recursive:true});await page.screenshot({path:out+'/CAPTURAS/mobile390/manifestacoes.png'});
});

// Ink bounds measured from the unchanged authorized 3000×550 institutional asset.
test('Marca institucional inteira nas duas larguras de sidebar',async({page})=>{
 for(const width of [1536,1672]){await page.setViewportSize({width,height:941});const bounds=await page.locator('.rail .approved-brand').evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),[w,h]=s.backgroundSize.split(' ').map(parseFloat),[x,y]=s.backgroundPosition.split(' ').map(parseFloat);return{left:x+214*w/3000,right:x+1314*w/3000,top:y+147*h/550,bottom:y+417*h/550,width:r.width,height:r.height}});expect(bounds.left).toBeGreaterThanOrEqual(0);expect(bounds.top).toBeGreaterThanOrEqual(0);expect(bounds.right).toBeLessThanOrEqual(bounds.width);expect(bounds.bottom).toBeLessThanOrEqual(bounds.height);}
});
