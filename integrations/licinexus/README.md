# Licinexus MCP isolado no IRPS

Versão NPM fixada: **0.2.1**, MIT, `@licinexusbr/mcp`. Em 24/10/2026, o GitHub main declara 0.2.2, mas o registro NPM consultado publica somente até 0.2.1. O pacote foi conferido pelo SHA512 do registro; LICENSE original está preservada. Não foi copiada implementação para substituir os coletores IRPS.

Instalação explícita na raiz do IRPS, Node >=20:

```powershell
New-Item -ItemType Directory -Force .runtime/licinexus/service
Copy-Item integrations/licinexus/package.json .runtime/licinexus/service/package.json
Copy-Item integrations/licinexus/package-lock.json .runtime/licinexus/service/package-lock.json
npm ci --ignore-scripts --prefix .runtime/licinexus/service
npm audit --omit=dev --prefix .runtime/licinexus/service
```

Não executar npx remoto a cada consulta. O backend usa o pacote local fixado, por stdio, sem herdar chaves ou URI PostgreSQL. O guard mantém HTTPS e hosts fixos, limite de corpo 2 MB, estrutura JSON limitada, heap de 192 MB, até oito requisições por chamada e prazo externo. Nenhuma porta MCP é exposta.

Auditoria inicial: um aviso alto de memória no Zod, refletido também no dependente Licinexus (dois pacotes sinalizados). Não foi forçada migração incompatível para Zod 4. Isolamento e limites reduzem exposição, mas não equivalem à correção do upstream. Não está liberado como servidor MCP público.

## Operação

POST autenticado/CSRF `/api/v1/portfolio/licinexus` aceita somente ID de fato oficial municipal existente, grupo 01–20 e operação `items`, `results`, `documents` ou `contract`. Não aceita URL, shell, prompt ou ferramenta arbitrária. GET no mesmo caminho apresenta as últimas vinte consultas da organização.

O pedido persiste no `job` existente como `licinexus.query`. O worker de monitoramento o executa usando a mesma trava PostgreSQL do coletor PNCP. Respostas 429/503 pausam o host e permitem até três tentativas. Uma execução interrompida recupera a concessão de três minutos. A coleta permanece dependente do backend ligado, sem dependência de conversa Codex. Nenhum banco adicional ou migração foi criado.

`Capture` entrega ao importador existente a resposta oficial realmente obtida, com URL original, HTTP e SHA256. Não simula uma requisição e não fabrica uma página. Apenas itens e resultados usam essa ingestão; documento/contrato detalhado fica como evidência observada, sem completar fases ou pagamentos. A paginação ausente da ferramenta de itens não comprova coleta completa; a ingestão conserva estado parcial e não marca páginas da fila histórica como concluídas.

As identidades continuam PNCP, sem prefixo Licinexus nos fatos. Revisões preservam os fatos anteriores. Texto e grupo são candidatos; não criam vínculo CATMAT/CATSER. Atas não comprovam estoque físico; nenhuma inferência de saldo, consumo ou pagamento foi introduzida. Agregações/comparações upstream não substituem os indicadores auditáveis do IRPS.

Fila e evidências da rodada: `docs/implementacao/licinexus/`. Sem push, merge, deploy ou alteração dos oito módulos V4.
