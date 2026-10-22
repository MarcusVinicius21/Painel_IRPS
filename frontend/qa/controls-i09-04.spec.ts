import {test,expect} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/sequence-08/fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_REFINAMENTO_I09_I17/I09_04/ESTADOS');
const stages=['selecao','historico','planejamento','preparacao','manifestacoes','consolidacao'];
async function login(page:any){await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();}
async function open(page:any,stage:string){await page.goto('/#/inteligencia?estudo='+f.study+'&etapa='+stage);await expect(page.locator('.dataset-warning')).toBeVisible();await page.waitForLoadState('networkidle');await page.evaluate(()=>document.fonts.ready);}
for(const width of [1672,390])test('Controles globais: rótulos, SVG e foco nas etapas '+width,async({page})=>{
 test.setTimeout(120000);await page.setViewportSize({width,height:941});await login(page);const evidence=[];
 for(const stage of stages){await open(page,stage);const help=page.getByRole('button',{name:'Ajuda',exact:true});await page.keyboard.press('Tab');await help.focus();await expect(help).toBeFocused();expect(await help.evaluate(e=>getComputedStyle(e).outlineStyle)).toBe('solid');await expect(help.locator('svg')).toHaveAttribute('aria-hidden','true');await help.press('Enter');await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(help).toBeFocused();
 const controls=await page.locator('main input[aria-describedby],main select[aria-describedby],main textarea[aria-describedby]').evaluateAll(list=>list.filter(e=>e.getClientRects().length).map(e=>({label:e.getAttribute('aria-label'),hints:e.getAttribute('aria-describedby')!.split(' ').map(id=>document.getElementById(id)?.textContent)})));for(const c of controls){expect(c.label).toBeTruthy();expect(c.hints.every(Boolean)).toBe(true);}evidence.push({stage,associatedHints:controls.length});}
 fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/FOCO_'+width+'.json',JSON.stringify(evidence,null,2));await page.screenshot({path:out+'/FOCO_'+width+'.png'});
});
test('Busca informa carregamento, impede duplicação e recupera erro explícito',async({page})=>{
 await page.setViewportSize({width:1672,height:941});await login(page);await open(page,'selecao');let release:()=>void=()=>{};const wait=new Promise<void>(r=>release=r);
 await page.route('**/national-catalogue?*',async route=>{await wait;await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:{message:'Falha de consulta simulada exclusivamente no teste'}})});});
 const search=page.getByRole('button',{name:'Buscar no catálogo',exact:true});await expect(search.locator('svg')).toHaveAttribute('aria-hidden','true');await search.click();const pending=page.getByRole('button',{name:'Pesquisando…',exact:true});await expect(pending).toBeDisabled();await expect(pending).toHaveAttribute('aria-busy','true');await expect(pending.locator('.control-spinner')).toBeVisible();fs.mkdirSync(out,{recursive:true});await page.screenshot({path:out+'/BUSCA_CARREGANDO.png'});release();await expect(search).toBeEnabled();await expect(search).toHaveAttribute('aria-busy','false');await expect(page.getByText('Falha de consulta simulada exclusivamente no teste',{exact:false})).toBeVisible();await page.screenshot({path:out+'/BUSCA_FALHA.png'});
});
test('Controles indisponíveis preservam explicação e estado',async({page})=>{
 await login(page);await open(page,'selecao');const modality=page.getByRole('combobox',{name:'Modalidade',exact:true});await expect(modality).toBeDisabled();await expect(modality).toHaveAttribute('aria-describedby',/.+/);const hint=await modality.getAttribute('aria-describedby');await expect(page.locator('[id="'+hint+'"]')).toContainText(/indisponível/);await expect(page.locator('.dataset-warning')).toContainText(/fictícia/);
});
