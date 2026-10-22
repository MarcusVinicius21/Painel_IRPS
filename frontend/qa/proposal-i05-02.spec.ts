import {test,expect} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
const catalogue=JSON.parse(fs.readFileSync(path.resolve('../.runtime/history-filters/browser-fixture.json'),'utf8'));
const out=path.resolve('../docs/IRPS_MICROTAREFAS/I05_02/estados');
test.use({viewport:{width:1672,height:941},deviceScaleFactor:1});
async function shot(p:any,n:string){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,n+'.png')});}
async function read(p:any,s:any){const r=await p.request.get('/api/v1/director/studies/'+s.id+'/register');expect(r.ok()).toBe(true);return r.json();}
async function save(p:any){const response=p.waitForResponse((r:any)=>r.url().endsWith('/operations')&&r.request().method()==='POST');await p.getByRole('button',{name:'Salvar registro interno',exact:true}).click();const r=await response;expect(r.status()).toBe(201);await expect(p.getByRole('button',{name:'Salvar registro interno',exact:true})).toBeEnabled();return r.json();}
async function create(p:any){
 await p.goto('/');await p.getByRole('button',{name:'Equipe de compras A',exact:true}).click();await expect(p.locator('.identity-label')).toBeVisible();
 const cookie=(await p.context().cookies()).find((c:any)=>c.name==='irps_csrf');
 const r=await p.request.post('/api/v1/director/studies',{headers:{'x-csrf-token':cookie!.value},data:{classification:'synthetic',snapshot_id:catalogue.snapshot_id,code:catalogue.code,name:'Papel de teste I05_02 — demonstração',category:'material',specification:'Papel em caixa de dez resmas para teste local de propostas.',unit:'caixa de 10 resmas',quantity_step:'1',municipalities:['3131307','3101607'],phase:'homologado',start:'2025-01-01',end:'2025-12-31',preliminary_target:'200',target_justification:'Meta fictícia somente para teste de interface.',technical_evidence:'Conferência técnica sintética do teste local.',technical_confirmed:true}});
 expect(r.status()).toBe(201);const s=await r.json();await p.goto('/index.html#/inteligencia?estudo='+s.id+'&etapa=planejamento');await expect(p.getByLabel('Município do registro',{exact:true})).toBeVisible();return s;
}
const errors=new WeakMap<object,string[]>();
test.beforeEach(({page})=>{errors.set(page,[]);page.on('pageerror',e=>errors.get(page)!.push(e.message));});
test.afterEach(({page})=>expect(errors.get(page)).toEqual([]));

test('Propor, conferir, editar cidades e reabrir preserva V4 e confirmações ausentes',async({page})=>{
 const s=await create(page);const scenarioURL='/api/v1/scenarios/'+s.scenario.id,before=await(await page.request.get(scenarioURL)).json();
 await page.getByLabel('Município do registro',{exact:true}).selectOption('3131307');await page.getByLabel('Quantidade do registro',{exact:true}).fill('12');await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('Proposta fictícia de doze caixas para revisão.');await save(page);
 await expect(page.getByText(/Último registro por Equipe de compras A/)).toBeVisible();let data=await read(page,s);expect(data.suggested_known_total).toBeNull();expect(data.confirmed_known_total).toBeNull();expect(data.operations[0].created_by_name).toBe('Equipe de compras A');
 await page.getByLabel('Situação do registro',{exact:true}).selectOption('reviewed');await save(page);expect((await read(page,s)).suggested_known_total).toBe('12');
 await page.getByLabel('Município do registro',{exact:true}).selectOption('3101607');await expect(page.getByLabel('Quantidade do registro',{exact:true})).toHaveValue('');await page.getByLabel('Quantidade do registro',{exact:true}).fill('18');await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('Sugestão sintética de dezoito caixas conferida.');await page.getByLabel('Situação do registro',{exact:true}).selectOption('reviewed');await save(page);
 await page.reload();await expect(page.getByLabel('Município do registro',{exact:true})).toBeVisible();await page.getByLabel('Município do registro',{exact:true}).selectOption('3101607');await expect(page.getByLabel('Quantidade do registro',{exact:true})).toHaveValue('18');data=await read(page,s);expect(data.suggested_known_total).toBe('30');expect(data.suggestion_pending_municipalities).toBe(0);expect(data.confirmed_known_total).toBeNull();expect(data.consolidated_total).toBeNull();expect(data.history).toHaveLength(3);expect(await(await page.request.get(scenarioURL)).json()).toEqual(before);
 await page.getByLabel('Justificativa e observações da conferência',{exact:true}).scrollIntoViewIfNeeded();await shot(page,'editor-por-municipio');await page.evaluate(()=>scrollTo(0,0));await shot(page,'03-propostas-conferidas');
 fs.mkdirSync(path.resolve('../.runtime/proposal-i05-02'),{recursive:true});fs.writeFileSync(path.resolve('../.runtime/proposal-i05-02/browser-fixture.json'),JSON.stringify({study:s.id,scenario:s.scenario.id}));
});

test('Motivo vazio e fracionamento incompatível não geram registro',async({page})=>{
 const s=await create(page);await page.getByLabel('Quantidade do registro',{exact:true}).fill('12.5');await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('           ');await expect(page.getByRole('button',{name:'Salvar registro interno',exact:true})).toBeDisabled();await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('Quantidade fictícia incompatível para teste.');const response=page.waitForResponse(r=>r.url().endsWith('/operations'));await page.getByRole('button',{name:'Salvar registro interno',exact:true}).click();expect((await response).status()).toBe(422);await expect(page.getByText('A quantidade proposta deve respeitar a unidade e o passo definidos para este item.',{exact:true})).toBeVisible();expect((await read(page,s)).history).toHaveLength(0);await shot(page,'fracionamento-rejeitado');
});

test('Edição por teclado e persistência em 390 px',async({page})=>{
 await page.setViewportSize({width:390,height:941});const s=await create(page);await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.getByLabel('Quantidade do registro',{exact:true}).fill('0');await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('Zero proposto explicitamente em teste sintético.');await page.getByRole('button',{name:'Salvar registro interno',exact:true}).focus();const response=page.waitForResponse(r=>r.url().endsWith('/operations'));await page.keyboard.press('Enter');expect((await response).status()).toBe(201);expect((await read(page,s)).operations[0].payload.quantity).toBe('0');await expect(page.getByText(/Último registro por Equipe de compras A/)).toBeVisible();await shot(page,'mobile-editor');
});

test('Mudança do comprovante invalida sugestão e apresenta nova conferência',async({page})=>{
 const s=await create(page),cookie=(await page.context().cookies()).find(c=>c.name==='irps_csrf')!,headers={'x-csrf-token':cookie.value};
 const upload=await page.request.post('/api/v1/documents',{headers,multipart:{classification:'synthetic',file:{name:'proposta-sintetica.csv',mimeType:'text/csv',buffer:Buffer.from('descricao;quantidade\nCaixas de papel de teste;12\n')}}});expect(upload.status()).toBe(201);const doc=await upload.json();
 await page.reload();await expect(page.getByLabel('Município do registro',{exact:true})).toBeVisible();await page.getByLabel('Quantidade do registro',{exact:true}).fill('12');await page.getByLabel('Situação do registro',{exact:true}).selectOption('reviewed');await page.getByLabel('Documento recebido ou comprovante',{exact:true}).selectOption(doc.id);await page.getByLabel('Justificativa e observações da conferência',{exact:true}).fill('Proposta sintética vinculada à referência preservada.');await save(page);expect((await read(page,s)).suggested_known_total).toBe('12');
 const review=await page.request.post('/api/v1/documents/'+doc.id+'/review',{headers,data:{revision:doc.revision,decision:'needs_changes',note:'Referência sintética alterada no teste de invalidação.',corrections:{}}});expect(review.status()).toBe(200);await page.reload();await expect(page.getByText('O documento desta sugestão mudou. Confira a referência e registre uma nova versão.',{exact:true})).toBeVisible();const data=await read(page,s);expect(data.suggested_known_total).toBeNull();expect(data.confirmed_known_total).toBeNull();expect(data.operations[0].payload.quantity).toBe('12');await shot(page,'referencia-alterada');
});
