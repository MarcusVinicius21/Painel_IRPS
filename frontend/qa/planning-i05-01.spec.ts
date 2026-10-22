import {test,expect} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I05_01/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();
test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/index.html#/inteligencia?estudo='+f.base+'&etapa=planejamento');await expect(page.getByRole('button',{name:'Abrir cálculo individual V4',exact:true})).toBeEnabled();});
test.afterEach(async({page})=>expect(errors.get(page)).toEqual([]));
async function shot(page:any,name:string){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,name+'.png')});}
test('Seletores são apenas navegação; ida e volta A/B preserva estudo, cenário e versão',async({page})=>{
 const original=await(await page.request.get('/api/v1/director/studies/'+f.base)).json();const url='/api/v1/scenarios/'+original.scenario_id;
 const before=await(await page.request.get(url)).json();const mutations:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/v1/'))mutations.push(r.url());});
 await page.getByRole('radio',{name:'Modo B — Quantidade global justificada',exact:true}).check();await expect(page.getByRole('radio',{name:'Modo B — Quantidade global justificada',exact:true})).toBeChecked();
 await page.getByRole('button',{name:'Abrir critérios do modo B',exact:true}).click();await expect(page).toHaveURL(new RegExp('distribuicao.*estudo='+f.base));await expect(page.getByRole('button',{name:'Salvar critérios',exact:true})).toBeVisible();
 await page.getByRole('link',{name:'Voltar ao estudo de origem',exact:true}).click();await expect(page.getByRole('button',{name:'Abrir cálculo individual V4',exact:true})).toBeEnabled();await page.getByRole('radio',{name:'Modo A — Necessidades municipais independentes',exact:true}).check();await page.getByRole('button',{name:'Abrir cálculo individual V4',exact:true}).click();await expect(page).toHaveURL(new RegExp('quantidades.*estudo='+f.base));await expect(page.getByRole('link',{name:'Voltar ao estudo de origem',exact:true})).toBeVisible();await page.getByRole('link',{name:'Voltar ao estudo de origem',exact:true}).click();
 expect(await(await page.request.get(url)).json()).toEqual(before);expect((await(await page.request.get('/api/v1/director/studies/'+f.base)).json()).payload).toEqual(original.payload);expect(mutations).toEqual([]);await shot(page,'ida-volta-sem-mutacao');
});
test('Histórico, necessidade, sugestão e confirmação permanecem distintos e ausências não viram zero',async({page})=>{
 const grid=page.locator('.municipal-history-panel');for(const name of ['Histórico observado · 12 meses','Necessidade calculada · V4','Sugestão do consórcio','Confirmação municipal'])await expect(grid.getByRole('columnheader',{name,exact:true})).toBeVisible();await expect(grid).toContainText('Dados insuficientes para cálculo');await expect(grid.getByLabel('Informação insuficiente',{exact:true})).not.toHaveCount(0);await expect(page.locator('.planning-summary')).toContainText('Meta global pretendida');await expect(page.locator('.dataset-warning')).toBeVisible();await expect(grid.locator('input[type=number]')).toHaveCount(0);await shot(page,'origens-e-pendencias');
});
test('Alterar contexto bloqueia preparo e editores com motivo explícito',async({page})=>{
 await page.getByLabel('Meta global pretendida · preliminar',{exact:true}).fill('200');await expect(page.getByRole('button',{name:'Abrir cálculo individual V4',exact:true})).toBeDisabled();await expect(page.getByRole('button',{name:'Abrir critérios do modo B',exact:true})).toBeDisabled();await expect(page.locator('.planning-summary-action')).toContainText('O contexto mudou. Salve um novo estudo antes de preparar a IRP.');await expect(page.locator('.planning-summary-action a')).toHaveCount(0);await expect(page.getByRole('button',{name:'Criar novo estudo com estes dados',exact:true})).toBeDisabled();await shot(page,'preparo-bloqueado');
});
test('Estudo preservado abre preparação interna sem fabricar cálculo ou confirmação',async({page})=>{
 await page.locator('.planning-summary-action').getByRole('link',{name:'Preparar IRP →',exact:true}).click();await expect(page).toHaveURL(new RegExp('etapa=preparacao'));await expect(page.getByRole('heading',{name:'Preparação dos documentos da IRP',exact:true})).toBeVisible();await expect(page).toHaveURL(new RegExp('estudo='+f.base));
});
for(const width of [1672,390])test('Layout e teclado em '+width,async({page})=>{
 await page.setViewportSize({width,height:941});await page.evaluate(()=>document.fonts.ready);await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const radio=page.getByRole('radio',{name:'Modo A — Necessidades municipais independentes',exact:true});await radio.focus();await page.keyboard.press('ArrowRight');await expect(page.getByRole('radio',{name:'Modo B — Quantidade global justificada',exact:true})).toBeChecked();await page.evaluate(()=>window.scrollTo(0,0));await shot(page,'layout-'+width);
});

test('Caixas externas e controles internos medidos na referência 03',async({page})=>{
 await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>scrollTo(0,0));
 for(const [selector,ref] of [
 ['.method-options>.selected-item',{x:227,y:166,width:495,height:198}],
 ['.method-options>.panel:nth-child(2)',{x:733,y:166,width:438,height:198}],
 ['.method-options>.panel:nth-child(3)',{x:1181,y:166,width:472,height:198}],
 ['.municipal-history-panel',{x:227,y:501,width:1426,height:331}],
 ] as const){const box=await page.locator(selector).boundingBox();expect(box).not.toBeNull();for(const k of ['x','y','width','height'] as const)expect(Math.abs(box![k]-ref[k]),selector+' '+k).toBeLessThanOrEqual(4);}
 const radios=page.locator('.planning-method-selector input');for(let i=0;i<2;i++){const b=await radios.nth(i).boundingBox();expect(b?.width).toBe(18);expect(b?.height).toBe(18);}
});
