// Explicit reviewed entry point: upstream's file:// guard is not portable on Windows.
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=path.join(root,'.runtime/integracoes-118/sidecars/portal-poc/src/mcp-server.ts');
const {MCPPortalServer}=await import(pathToFileURL(source).href);
const server=new MCPPortalServer();
await server.initialize();
await server.start();
