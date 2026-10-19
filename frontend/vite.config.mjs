import {defineConfig} from 'vite';

const port=Number(process.env.IRPS_FRONTEND_PORT||5210);
const target=`http://127.0.0.1:${Number(process.env.IRPS_API_PORT||5211)}`;
const proxy={'/api':{target},'/health':{target}};
export default defineConfig({
 base:'./',cacheDir:'.cache/vite',
 server:{host:'127.0.0.1',port,strictPort:true,proxy},
 preview:{host:'127.0.0.1',port,strictPort:true,proxy}
});
