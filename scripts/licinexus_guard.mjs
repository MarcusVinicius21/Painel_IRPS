import fs from 'node:fs';import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const {default:axios}=await import(pathToFileURL(path.join(root,'.runtime/licinexus/service/node_modules/axios/index.js')).href);
const original=axios.create.bind(axios);let last=0,budget=0;
axios.create=(config)=>{
 const client=original({...config,maxContentLength:2*1024*1024,maxBodyLength:1024,maxRedirects:0});
 client.interceptors.request.use(async c=>{
  const url=client.getUri(c),host=new URL(url).host;
  if(!url.startsWith('https://')||!['pncp.gov.br','brasilapi.com.br','minhareceita.org'].includes(host)||c.method!=='get'||++budget>Number(process.env.IRPS_LX_BUDGET||8))throw Error('IRPS_NETWORK_GUARD');
  if(Date.now()-last<1500)await new Promise(r=>setTimeout(r,1500-(Date.now()-last)));last=Date.now();
  const transforms=Array.isArray(c.transformResponse)?c.transformResponse:[c.transformResponse];
  c.transformResponse=[function(raw,headers,status){
   if(typeof raw!=='string'||Buffer.byteLength(raw)>2*1024*1024)throw Error('IRPS_RESPONSE_LIMIT');
   if(process.env.IRPS_LX_TRACE)fs.appendFileSync(process.env.IRPS_LX_TRACE,JSON.stringify({url,status,sha256:crypto.createHash('sha256').update(raw).digest('hex'),body:raw,at:new Date().toISOString()})+'\n');
   if(status===200&&raw){
    let obj;try{obj=JSON.parse(raw)}catch{return raw;}
    let nodes=0;function bound(x,depth=0){if(++nodes>100000||depth>25||Array.isArray(x)&&x.length>2000)throw Error('IRPS_JSON_BOUNDARY');if(x&&typeof x==='object')for(const v of Object.values(x))bound(v,depth+1);};bound(obj);
   }
   return transforms.reduce((value,fn)=>typeof fn==='function'?fn.call(this,value,headers,status):value,raw);
  }];return c;
 });return client;
};
