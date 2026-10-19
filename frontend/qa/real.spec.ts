import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
const out=path.resolve('..','.runtime/evidencias');fs.mkdirSync(path.join(out,'telas'),{recursive:true});
const diagnostics=new WeakMap();
test.beforeEach(async({page})=>{const d={console:[],http_errors:[],network_failures:[]};diagnostics.set(page,d);page.on('console',m=>{if(['error','warning'].includes(m.type()))d.console.push({type:m.type(),line:m.location().lineNumber||0,source:m.location().url?new URL(m.location().url).pathname:'unknown',content_recorded:false});});page.on('response',r=>{if(r.status()>=400)d.http_errors.push({path:new URL(r.url()).pathname,status:r.status(),expected:r.status()===401&&new URL(r.url()).pathname.endsWith('/auth/context')});});page.on('requestfailed',r=>d.network_failures.push({path:new URL(r.url()).pathname,failure:r.failure()?.errorText}));});
test.afterEach(async({page},info)=>{const d=diagnostics.get(page);fs.writeFileSync(path.join(out,'browser-'+info.title.replace(/[^a-zA-Z0-9]+/g,'-')+'.json'),JSON.stringify(d,null,2));expect(d.network_failures.filter(x=>!x.failure?.includes('ERR_ABORTED'))).toEqual([]);expect(d.http_errors.filter(x=>!x.expected)).toEqual([]);});
async function login(page,user='Equipe de compras A'){
 await page.goto('/');await page.getByRole('button',{name:user,exact:true}).click();await expect(page.getByRole('heading',{level:1})).toContainText('Uma boa decisão');
 await expect(page.locator('.identity-label')).toContainText(user);
}
async function measure(page){await page.evaluate(()=>{window.__irpsMetrics={clicks:0,fields:[],screens:[],start:performance.now()};});}
async function metrics(page,task){return await page.evaluate(task=>({...window.__irpsMetrics,task,duration_ms:Math.round(performance.now()-window.__irpsMetrics.start)}),task);}
test.beforeEach(async({page})=>{await page.addInitScript(()=>{document.addEventListener('click',()=>{if(window.__irpsMetrics)window.__irpsMetrics.clicks++},true);document.addEventListener('input',e=>{const el=e.target;if(window.__irpsMetrics&&el instanceof HTMLElement){const name=el.closest('label')?.innerText||el.getAttribute('name')||el.tagName;if(!window.__irpsMetrics.fields.includes(name))window.__irpsMetrics.fields.push(name)}},true);window.addEventListener('hashchange',()=>{if(window.__irpsMetrics)window.__irpsMetrics.screens.push(location.hash.split('?')[0])});});});

for(const width of [320,390,768,1024,1440])test(`Observatório real · ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await login(page);await page.screenshot({path:path.join(out,`telas/${width}-inicio.png`),fullPage:true});
 await page.goto('/#/licitacao');await measure(page);await page.getByRole('button',{name:'Novo planejamento',exact:true}).click();const dialog=page.getByRole('dialog');
 await dialog.getByLabel('Nome da compra').fill('QA Observatório '+width);
 await dialog.getByLabel('Municípios fictícios no cenário').selectOption(width===1440?'118':'3');
 await dialog.getByLabel('Itens do catálogo de teste').selectOption(width===1440?'100':'5');
 await dialog.getByRole('button',{name:'Criar cenário com dados fictícios'}).click();await expect(dialog).not.toBeVisible();
 const calculation=page.waitForResponse(r=>r.url().includes('/calculate')&&r.request().method()==='POST');await page.getByRole('button',{name:'Calcular cenário',exact:true}).click();const response=await calculation;expect(response.status()).toBe(200);const calc=await response.json();expect(calc.summary.lines).toBe(width===1440?11800:15);
 await expect(page.locator('.scenario-summary strong')).not.toHaveText('Não disponível');
 const measured=await metrics(page,'Criar cenário fictício e calcular');fs.writeFileSync(path.join(out,`ux-${width}.json`),JSON.stringify({...measured,manual_fields:measured.fields.length,calculation_id:calc.id,scenario_id:calc.scenario_id,persisted_lines:calc.summary.lines},null,2));
 await page.screenshot({path:path.join(out,`telas/${width}-licitacao.png`),fullPage:true});
 const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();fs.writeFileSync(path.join(out,`axe-${width}.json`),JSON.stringify(axe.violations,null,2));expect(axe.violations).toEqual([]);
 const overflow=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,width:innerWidth}));expect(overflow.doc).toBeLessThanOrEqual(overflow.width+1);
 await page.getByRole('link',{name:'Quantidades',exact:true}).click();await expect(page.getByText('Quantidades por município e item',{exact:true})).toBeVisible();await expect(page.locator('.mobile-records:visible, .desktop-records:visible').getByText(/Quantidade para revisão\./).first()).toBeVisible();await page.screenshot({path:path.join(out,`telas/${width}-quantidades.png`),fullPage:true});
 await page.getByRole('link',{name:'Relatórios',exact:true}).click();await page.getByRole('button',{name:'Gerar CSV',exact:true}).click();const download=page.waitForEvent('download');await page.getByRole('link',{name:/Baixar IRPS_cenario/}).click();const d=await download;const file=path.join(out,`export-navegador-${width}.csv`);await d.saveAs(file);expect(fs.readFileSync(file,'utf-8')).toContain('DADOS FICTÍCIOS');
 await page.getByRole('button',{name:'Perguntar ao IRPS',exact:true}).click();await page.getByLabel('Sua pergunta',{exact:true}).fill('Quanto Ipatinga pagou por papel A4?');await page.getByLabel('Consultar em',{exact:true}).selectOption('synthetic');await page.getByRole('button',{name:'Consultar informações',exact:true}).click();await expect(page.getByRole('heading',{name:'Pagamentos líquidos documentados. Pagamento não comprova consumo.'})).toBeVisible();await page.screenshot({path:path.join(out,`telas/${width}-assistente.png`),fullPage:true});await page.keyboard.press('Escape');
 expect(errors).toEqual([]);
});

test('Custos privados · documentos e encerramento da sessão',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});await login(page,'Empresa fictícia A');await page.goto('/#/negocio');await measure(page);const savedQuote=page.waitForResponse(r=>r.url().endsWith('/quotes')&&r.request().method()==='POST');await page.getByRole('button',{name:'Calcular e salvar simulação',exact:true}).click();const privateQuote=await (await savedQuote).json();await expect(page.locator('.quote-profit')).not.toContainText('Não disponível');fs.writeFileSync(path.join(out,'ux-negocio.json'),JSON.stringify(await metrics(page,'Calcular simulação comercial privada'),null,2));await page.screenshot({path:path.join(out,'telas/1440-negocio.png'),fullPage:true});
 const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();expect(axe.violations).toEqual([]);
 await page.goto('/#/documentos');await measure(page);await page.getByLabel('Escolher documentos').setInputFiles({name:'teste-local.csv',mimeType:'text/csv',buffer:Buffer.from('descricao;quantidade\nPapel A4;12\n')});await expect(page.getByRole('heading',{name:'Confira a leitura de teste-local.csv'})).toBeVisible();await page.getByRole('button',{name:'Registrar conferência',exact:true}).click();await expect(page.getByText('Revisão registrada',{exact:true})).toBeVisible();fs.writeFileSync(path.join(out,'ux-documentos.json'),JSON.stringify(await metrics(page,'Importar CSV e registrar conferência'),null,2));await page.screenshot({path:path.join(out,'telas/1440-documentos.png'),fullPage:true});
 await page.getByRole('button',{name:'Sair',exact:true}).click();await expect(page.getByRole('heading',{name:'Entre no Observatório IRPS'})).toBeVisible();
 await page.getByRole('button',{name:'Empresa fictícia B',exact:true}).click();await expect(page.locator('.identity-label')).toContainText('Empresa fictícia B');await page.goto('/#/negocio');expect((await page.request.get('/api/v1/quotes/'+privateQuote.id)).status()).toBe(404);const own=await (await page.request.get('/api/v1/quotes')).json();expect(own.records.some(q=>q.id===privateQuote.id)).toBe(false);
});

test('Teclado · consulta oficial · identidade e fontes',async({page})=>{
 await page.setViewportSize({width:390,height:844});await login(page);await page.goto('/#/inicio');await page.keyboard.press('Tab');await page.keyboard.press('Tab');expect(await page.locator(':focus').count()).toBe(1);
 await page.getByRole('button',{name:'Perguntar ao IRPS'}).click();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Perguntar ao IRPS'})).toBeFocused();
 await page.goto('/#/fontes');await expect(page.getByRole('heading',{name:'Saiba de onde vêm as informações'})).toBeVisible();await expect(page.getByText('PNCP',{exact:true}).first()).toBeVisible();await page.screenshot({path:path.join(out,'telas/390-fontes.png'),fullPage:true});
 const a=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();fs.writeFileSync(path.join(out,'axe-fontes.json'),JSON.stringify(a.violations,null,2));expect(a.violations).toEqual([]);
 const official=await (await page.request.get('/api/v1/purchases?dataset=official&municipality_ibge=3131307&limit=1')).json();
 await page.goto('/#/resultados?cidade=3131307');
 await expect(page.getByLabel('Dados',{exact:true})).toHaveValue('official');
 if(official.records.length)await expect(page.locator('.mobile-records:visible, .desktop-records:visible').getByText('Fonte oficial').first()).toBeVisible();
 else{await expect(page.getByText('Resultado vazio não significa ausência de compras')).toBeVisible();await expect(page.locator('.mobile-records:visible, .desktop-records:visible').getByText('Fonte oficial')).toHaveCount(0);}
 await page.screenshot({path:path.join(out,'telas/390-compras-oficiais.png'),fullPage:true});
});

test('Esforço real · procurar comprador e comparar preços',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});await login(page);await measure(page);
 await page.getByLabel('Pesquisar produto, serviço, obra ou município').fill('Papel A4');await page.getByRole('button',{name:'Pesquisar compras',exact:true}).click();await page.getByLabel('Dados',{exact:true}).selectOption('synthetic');await expect(page.locator('.desktop-records').getByText('Órgão fictício compras-a').first()).toBeVisible();
 fs.writeFileSync(path.join(out,'ux-comprador.json'),JSON.stringify(await metrics(page,'Procurar comprador de papel A4 com dados fictícios'),null,2));await page.screenshot({path:path.join(out,'telas/1440-comprador.png'),fullPage:true});
 await page.goto('/#/comparar');await measure(page);await page.getByLabel('Dados',{exact:true}).selectOption('synthetic');await page.getByRole('button',{name:'Consultar recorte',exact:true}).click();await expect(page.getByText('Encontramos registros no recorte escolhido. Confira a situação de cada compra.').first()).toBeVisible();
 fs.writeFileSync(path.join(out,'ux-comparacao.json'),JSON.stringify(await metrics(page,'Comparar preços contratados de três municípios'),null,2));await page.screenshot({path:path.join(out,'telas/1440-comparacao.png'),fullPage:true});
});
