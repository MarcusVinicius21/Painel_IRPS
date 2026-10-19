> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Contratos executáveis

Gerado do FastAPI em execução. Login de teste é restrito ao ambiente local.

| Método | Endereço | Operação |
|---|---|---|
| GET | `/health` | Health |
| GET | `/health/live` | Live |
| GET | `/health/ready` | Ready |
| GET | `/local-issuer/.well-known/jwks.json` | Jwks |
| GET | `/api/v1/auth/test-users` | Test Users |
| POST | `/api/v1/auth/test-login` | Login |
| POST | `/api/v1/auth/oidc-session` | Oidc Session |
| GET | `/api/v1/auth/context` | Context |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/municipalities` | Municipalities |
| GET | `/api/v1/items` | Items |
| GET | `/api/v1/catalogue/official` | Official Catalogue |
| GET | `/api/v1/scenarios` | Scenario List |
| POST | `/api/v1/scenarios` | Scenario Create |
| POST | `/api/v1/scenarios/synthetic` | Scenario Synthetic |
| GET | `/api/v1/scenarios/{sid}` | Scenario Get |
| PUT | `/api/v1/scenarios/{sid}` | Scenario Put |
| POST | `/api/v1/scenarios/{sid}/confirm-distribution` | Distribution Confirm |
| POST | `/api/v1/scenarios/{sid}/calculate` | Scenario Calculate |
| POST | `/api/v1/scenarios/{sid}/review` | Scenario Review |
| GET | `/api/v1/scenarios/{sid}/versions` | Versions |
| GET | `/api/v1/scenarios/{sid}/calculations` | Calculations |
| GET | `/api/v1/calculations/{cid}/lines` | Lines |
| POST | `/api/v1/scenarios/{sid}/exports/{fmt}` | Scenario Export |
| GET | `/api/v1/artifacts/{aid}/download` | Artifact Download |
| GET | `/api/v1/quotes` | Quote List |
| POST | `/api/v1/quotes` | Quote Create |
| GET | `/api/v1/quotes/{qid}` | Quote Get |
| PUT | `/api/v1/quotes/{qid}` | Quote Put |
| GET | `/api/v1/documents` | Document List |
| POST | `/api/v1/documents` | Document Upload |
| GET | `/api/v1/documents/{did}` | Document Get |
| POST | `/api/v1/documents/{did}/review` | Document Review |
| GET | `/api/v1/documents/{did}/original` | Document Original |
| POST | `/api/v1/assistant/ask` | Assistant Ask |
| POST | `/api/v1/assistant/tools` | Assistant Tool |
| POST | `/api/v1/assistant/external` | External Disabled |
| GET | `/api/v1/purchases` | Purchases |
| GET | `/api/v1/sources` | Source List |
| GET | `/api/v1/coverage` | Coverage |
| GET | `/api/v1/purchases/{fid}` | Purchase Get |
| POST | `/api/v1/sources/sync` | Source Sync |
| GET | `/api/v1/jobs/{jid}` | Job Get |
| GET | `/api/v1/watches` | Watches |
| POST | `/api/v1/watches` | Watch Create |
| DELETE | `/api/v1/watches/{wid}` | Watch Delete |
| GET | `/api/v1/audit` | Audit |
| GET | `/api/v1/opportunity-options` | Dados para filtros de oportunidades |
| POST | `/api/v1/municipality-groups` | Salva um grupo de municípios da organização |
| POST | `/api/v1/opportunity-equivalences` | Registra equivalência técnica revisada |
| POST | `/api/v1/opportunities/query` | Lista oportunidades com cobertura e indicadores |
| POST | `/api/v1/opportunities/{key}/detail` | Abre histórico, fontes e preços do recorte |
| POST | `/api/v1/opportunities/{key}/review` | Salva revisão humana de viabilidade |
| POST | `/api/v1/opportunities/{key}/scenario` | Cria rascunho de cenário com idempotência |
| GET/POST | `/api/v1/history-collections` | Lista ou prepara coleta PNCP limitada |
| GET | `/api/v1/history-collections/{cid}` | Consulta cobertura e ponto de retomada |
| POST | `/api/v1/history-collections/{cid}/advance` | Solicita uma quantidade limitada de páginas |
| POST | `/api/v1/history-collections/{cid}/pause` | Pausa a coleta |
| POST | `/api/v1/history-collections/{cid}/resume` | Retoma a coleta autorizada |
| POST | `/api/v1/history-collections/{cid}/extend` | Aumenta o limite de páginas até 2000 |
| GET | `/api/v1/opportunity-alerts` | Lista acompanhamentos e diferenças comprovadas |
| POST | `/api/v1/opportunity-watches` | Cria acompanhamento local do conjunto de versões |
| POST | `/api/v1/opportunity-alerts/refresh` | Compara somente dados já coletados |
| DELETE | `/api/v1/opportunity-watches/{wid}` | Desativa acompanhamento e preserva histórico |
