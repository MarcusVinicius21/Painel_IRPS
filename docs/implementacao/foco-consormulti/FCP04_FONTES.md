# FCP04 — Avaliação de fontes e código externo

Nenhum repositório foi instalado, executado ou incorporado. Metadados, licença no commit fixado e manifestos de dependências foram lidos anonimamente. Isso não é certificação de segurança integral de toda a árvore.

| Repositório | Commit auditado | Licença | Decisão |
|---|---|---|---|
| thiagosy/PNCP | b6b27a21fddf6380aa896f29e85fa6e340cf5946 | não identificada | BLOCKED_LICENSE |
| Licitei/dados-publicos-mcp | 5358afe62d2116ede86d5f9fc60d95a3a9e5837a | AGPL-3.0 | BLOCKED_LICENSE |
| dutradotdev/mcp-portal-transparencia | 62a51a05a42d89be746dff1881a9b702d86ef1d2 | MIT | BLOCKED_KEY |
| Mcp-Brasil/mcp-brasil | 2efb258370b125bbf190884283ae10f209b9d335 | MIT | OPTIONAL_REFERENCE |
| Licinexus/licinexus-mcp | 72ceda9b83ba4a10f58b59f937a246053f861eb8 | MIT | OPTIONAL_REFERENCE |
| Max-Martins/pncp-consulta | f09fcbef07d1a7552738b09998845aadd773b2dd | MIT | OPTIONAL_REFERENCE |
| okfn-brasil/querido-diario-api | bca35cbae7430abbe4d6a7e05ccddcca471b4b70 | MIT | OPTIONAL_REFERENCE |

Decisões: preservar clientes oficiais existentes; não há ganho comprovado para substituir coletores com filas, RLS e evidências por outro stack. pncp-consulta não declara dependências; Licinexus adiciona SDK MCP/axios/zod; MCP Brasil declara FastMCP/Anthropic/DuckDB; Querido Diário depende de OpenSearch e stack própria; Licitei inclui Bun/PGlite/modelos/infra, além do gate AGPL. Nenhuma dependência foi adicionada ao IRPS. Portal federal exige chave autorizada, não procurada ou utilizada aqui.

CATMAT.com.br é fonte secundária opcional, não canal do Governo Federal. Documentação https://catmat.com.br/api-docs consultada em 23/10/2026 local. Operações GET documentadas, sem instalação. Preços/compras locais continuam independentes de sua disponibilidade.
