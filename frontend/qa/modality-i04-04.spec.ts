import {test,expect} from '@playwright/test';import fs from 'node:fs';import path from 'node:path';
const f=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I04_04/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
const errors=new WeakMap<object,string[]>();
test.beforeEach(async({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));await page.goto('/');await page.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(page.locator('.identity-label')).toBeVisible();await page.goto('/index.html#/inteligencia?estudo='+f.base+'&etapa=historico');await expect(page.getByLabel('Fonte',{exact:true})).toBeEnabled();});
test.afterEach(async({page})=>expect(errors.get(page)).toEqual([]));
const params=new URLSearchParams([['phase','homologado'],['start','2025-01-01'],['end','2025-12-31'],...f.cities.map((c:string)=>['municipalities',c])]);
const url='/api/v1/director/history/'+f.product_id;
async function shot(p:any,n:string){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,n+'.png')});}
test('UI e API mantêm modalidade indisponível com razão e desconhecidos preservados',async({page})=>{
 await expect(page.getByLabel('Modalidade',{exact:true})).toBeDisabled();await expect(page.getByText('Parte dos registros não informa a modalidade. O filtro permanece indisponível para não ocultá-los.',{exact:true})).toBeVisible();
 const options=await(await page.request.get(url+'/filters?'+params)).json();expect(options.modality_available).toBe(false);expect(options.modality_unknown_handling).toBe('not_filtered');expect(options.modality_normalization_version).toBe(1);
 const response=await page.request.get(url+'?'+params+'&modality=6');expect(response.status()).toBe(422);expect((await response.json()).detail.code).toBe('HISTORY_MODALITY_UNAVAILABLE');await page.getByLabel('Modalidade',{exact:true}).scrollIntoViewIfNeeded();await shot(page,'modalidade-indisponivel');
});
test('Fonte I02 continua exata e registros sem modalidade não desaparecem',async({page})=>{
 await page.getByLabel('Fonte',{exact:true}).selectOption('PNCP_RESULTADOS');const response=page.waitForResponse(r=>r.url().includes('/director/history/'+f.product_id+'?'));await page.getByRole('button',{name:'Conferir histórico por município',exact:true}).click();const data=await(await response).json();
 expect(data.summary.observed_records).toBe(3);expect(Number(data.summary.observed_quantity)).toBe(3);expect(data.scope.filters.provider).toBe('PNCP_RESULTADOS');
 const facts=data.municipalities.flatMap((r:any)=>r.evidence);expect(facts).toHaveLength(3);expect(facts.every((e:any)=>e.modality.state==='unknown'&&e.modality.code===null)).toBe(true);await shot(page,'fonte-e-desconhecidos');
});
test('Consulta repetida é estável e não regrava o snapshot anterior',async({page})=>{
 const stored='/api/v1/director/studies/'+f.base,before=await(await page.request.get(stored)).json();const a=await(await page.request.get(url+'?'+params)).json(),b=await(await page.request.get(url+'?'+params)).json();
 expect(a.snapshot_sha256).toBe(b.snapshot_sha256);expect(a.summary).toEqual(b.summary);expect((await(await page.request.get(stored)).json()).payload).toEqual(before.payload);
});
test('Aviso e fonte continuam acessíveis em 390 px',async({page})=>{
 await page.setViewportSize({width:390,height:941});await page.getByLabel('Modalidade',{exact:true}).scrollIntoViewIfNeeded();await expect(page.getByLabel('Modalidade',{exact:true})).toBeDisabled();await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByLabel('Fonte',{exact:true}).focus();await expect(page.getByLabel('Fonte',{exact:true})).toBeFocused();await shot(page,'modalidade-390');
});
