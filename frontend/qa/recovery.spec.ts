import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
test('Falha controlada e recuperação sem perder documentos',async({page})=>{
 await page.setViewportSize({width:390,height:900});await page.goto('/');await page.getByRole('button',{name:'Empresa fictícia A',exact:true}).click();await expect(page.locator('.identity-label')).toContainText('Empresa fictícia A');
 const filename=`teste-local-${Date.now()}.csv`;
 const csrf=await page.evaluate(()=>decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith('irps_csrf='))?.slice(10)||''));const uploaded=await page.request.post('/api/v1/documents',{headers:{'X-CSRF-Token':csrf},multipart:{classification:'business_private',file:{name:filename,mimeType:'text/csv',buffer:Buffer.from(`descricao;quantidade\nPapel A4 ${filename};12\n`)}}});expect(uploaded.ok()).toBeTruthy();
 const before=await (await page.request.get('/api/v1/documents')).json();expect(before.records.length).toBeGreaterThan(0);
 await page.route('**/api/v1/documents',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:{message:'Não foi possível consultar os documentos agora. Tente novamente em instantes.'}})}));
 await page.goto('/#/documentos');await expect(page.getByRole('status')).toContainText('Não foi possível consultar os documentos agora.');
 await page.unroute('**/api/v1/documents');await page.reload();await expect(page.locator('.mobile-records:visible, .desktop-records:visible').getByText(before.records[0].filename,{exact:true}).first()).toBeVisible();const after=await (await page.request.get('/api/v1/documents')).json();expect(after.records.map(r=>r.id)).toEqual(before.records.map(r=>r.id));
 const documents=page.locator('section.panel').filter({has:page.getByRole('heading',{name:'Documentos preservados'})});
 const uploadedRow=documents.locator('.mobile-records:visible article').filter({hasText:filename});
 for(let pageNumber=0;await uploadedRow.count()===0&&pageNumber<after.records.length;pageNumber++){
  await documents.getByRole('button',{name:'Próxima página'}).click();
 }
 await uploadedRow.getByRole('button',{name:'Revisar leitura',exact:true}).click();await expect(page.locator('.mobile-records:visible, .desktop-records:visible').getByText('Descrição',{exact:true}).first()).toBeVisible();await page.evaluate(()=>window.scrollTo(0,0));
 const out=path.resolve('..','.runtime/evidencias');await page.screenshot({path:path.join(out,'telas/390-recuperacao-documentos.png'),fullPage:true});fs.writeFileSync(path.join(out,'recuperacao-interface.json'),JSON.stringify({controlled_status:503,restored:true,document_count:after.records.length,original_ids_preserved:true},null,2));
});
