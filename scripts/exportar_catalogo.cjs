const fs=require('node:fs');const path=require('node:path');
const base=path.resolve(__dirname,'..');
// Catalogue data only; no frontend arithmetic is executed or copied into the API.
const data=fs.readFileSync(path.join(base,'frontend/src/data/demo.ts'),'utf8');
const start=data.indexOf('export const families=');const end=data.indexOf('export function defaultInputs');
const {stripTypeScriptTypes}=require('node:module');
const code=stripTypeScriptTypes(data.slice(start,end),{mode:'strip'}).replaceAll('export ','');
const catalog=new Function(code+';return catalog;')();
const dir=path.join(base,'backend/seed_data');fs.mkdirSync(dir,{recursive:true});
fs.writeFileSync(path.join(dir,'items.json'),JSON.stringify(catalog,null,2));
fs.copyFileSync(path.join(base,'frontend/src/data/cities.json'),path.join(dir,'cities.json'));
console.log('118 identidades preservadas; catálogo fictício exportado:',catalog.length);
