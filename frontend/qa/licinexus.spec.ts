import {test,expect} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
test('Licinexus · itens oficiais novos, filtros e fila real',async({page})=>{
 test.skip(!process.env.IRPS_FCP_OPERATIONAL,'Exige operador local e piloto oficial, sem dados sintéticos.');
 await page.goto('/');const credentials=JSON.parse(fs.readFileSync(path.resolve('../.runtime/operacional-local/acesso-privado.json'),'utf8'));
 await page.getByLabel('Senha de acesso').fill(credentials.password);await page.getByRole('button',{name:'Entrar',exact:true}).click();
 await page.getByRole('navigation',{name:'Grupos do portfólio'}).getByRole('button').filter({hasText:'Material de informática'}).click();
 await page.getByLabel('Municípios',{exact:true}).selectOption(['3131307']);await page.getByLabel('Situação da compra').selectOption('publicado_estimado');
 await page.getByRole('button',{name:'Aplicar e salvar filtros'}).click();await page.getByRole('button',{name:'Compras dos municípios',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Consultas complementares Licinexus'})).toBeVisible();
 await page.getByLabel('CNPJ do órgão comprador').fill('19871680000147');await page.getByRole('button',{name:'Filtrar órgão',exact:true}).click();
 await page.getByLabel('Fonte do registro').selectOption('PNCP_ITENS');
 const rows=page.getByRole('table',{name:'Compras municipais observadas, sem soma entre fases'});
 await expect(rows.getByText('Mouse Computador',{exact:true})).toBeVisible();
 await expect(rows.getByText('"Teclado Microcomputador"',{exact:true})).toBeVisible();
 await expect(rows.getByText('19871680000147',{exact:false}).first()).toBeVisible();
 await page.getByLabel('CNPJ do fornecedor').fill('00000000000000');await page.getByRole('button',{name:'Filtrar fornecedor',exact:true}).click();
 await expect(page.getByText('Sem vínculo encontrado neste recorte',{exact:true})).toBeVisible();
 await page.getByLabel('CNPJ do fornecedor').fill('');await page.getByRole('button',{name:'Filtrar fornecedor',exact:true}).click();
 await expect(rows.getByText('Mouse Computador',{exact:true})).toBeVisible();
 await rows.getByText('Complementar consulta PNCP',{exact:true}).first().click();
 const response=page.waitForResponse(r=>r.url().endsWith('/portfolio/licinexus')&&r.request().method()==='POST');
 await rows.getByRole('button',{name:'Consultar documentos',exact:true}).first().click();expect((await response).status()).toBe(202);
 for(const width of [390,1672]){await page.setViewportSize({width,height:941});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);}
});
