> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Resultado por contrato de aceite

“Completo” abaixo significa o contrato **local** desta rodada, com contas sintéticas. Não significa produção aprovada.

| Gate | Estado local | Comprovado | Limite restante |
|---|---|---|---|
| P0-A FastAPI | COMPLETO | Serviço HTTP, configuração tipada, OpenAPI executável, saúde e recusa segura | Operação produtiva e observabilidade distribuída |
| P0-B PostgreSQL | COMPLETO | PostgreSQL 18.6 portátil; cinco migrações; 30 tabelas; 26 com RLS forçada; 55 FKs | Backups/restauração e alta disponibilidade |
| P0-C Autorização | COMPLETO NO TESTE LOCAL / PARCIAL EM PRODUÇÃO | RS256/JWK, issuer/audience/exp/nbf, membership, revogação, CSRF/CORS e testes A/B | IdP real, provisionamento e revisão independente |
| P1-A V4 | COMPLETO | Oito arquivos idênticos, 65 regressões históricas e 200 verificações internas | Nenhuma alteração de fórmula autorizada ou realizada |
| P1-B Licitações | COMPLETO NO RECORTE LOCAL | Modos A/B, parâmetros/fonte, 3/10/20/118, 100 itens, versões, preços, memória, revisão e 11.800 linhas | Anuência municipal, recursos e aprovação administrativa oficial |
| P1-C Documentos/relatórios | COMPLETO NO RECORTE LOCAL | Quatro leitores revisáveis; originais; PDF/CSV/XLSX reabertos; downloads autorizados | Antivírus, isolamento do parser, OCR, grandes arquivos |
| P1-D Assistente | COMPLETO OFFLINE / PARCIAL PARA PROVEDORES | Ferramentas fechadas, resolução sem substituição, L01–L07, cache por acesso e reserva transacional | Modelo externo, quotas distribuídas e reconciliação real de cobrança |
| P2-A Fontes | PARCIAL COM COLETA REAL | IBGE, PNCP publicações/itens, CATMAT/CATSER; evidências gravadas | Histórico amplo, contratos/resultados/pagamentos, demais fontes |
| P2-B Observatório | COMPLETO NO RECORTE LOCAL | Fluxos conectados; dados do banco; desktop/mobile; sem troca de papel no cliente | Homologação com usuários e consolidação dos dados reais |

## Percentual estimado e método

Estimativa de engenharia para o **recorte P0–P2 da rodada**, com denominador fixo de 100 pontos. Os pesos não medem quantidade de arquivos ou de testes. Cada grupo considera execução, prova e o trabalho de produção ainda não realizado.

| Grupo | Peso | Entregue estimado | Justificativa do saldo |
|---|---:|---:|---|
| Runtime e configuração | 10 | 10 | Executável e reproduzível localmente |
| Banco e persistência | 10 | 9 | Falta operação de backup/restauração |
| Identidade e isolamento | 15 | 10 | IdP real e operação produtiva pendentes |
| Matemática V4 | 15 | 15 | Núcleo preservado e regressões |
| Cenários e comercial privado | 15 | 12 | Aprovações e governança administrativa pendentes |
| Documentos e relatórios | 8 | 6 | Antivírus, sandbox e OCR pendentes |
| Assistente e custos | 8 | 5 | Provedor e cobrança real desligados |
| Fontes e cobertura | 9 | 4 | Coleta pequena, sem histórico completo |
| Frontend integrado | 5 | 4 | Falta validação de uso em campo |
| QA e operação | 5 | 3 | Falta auditoria independente e ensaio produtivo |
| **Total** | **100** | **78** | **Gate de produção fechado** |

Os 78% são uma avaliação explícita, não um fato estatístico sobre o produto inteiro. Não equivalem à cobertura dos 118 municípios, acurácia preditiva ou prontidão comercial. A evidência objetiva está nos testes, registros e hashes.

## Preservação

2.210 arquivos inventariados foram mantidos idênticos. Os oito módulos matemáticos e os arquivos principais das skills foram comparados por SHA-256. Os 192 arquivos de código inventariados na auditoria anterior do Radar continuam iguais. Nenhum segredo do Radar foi aberto. Não houve repositório Git no workspace; nenhum commit, push ou deploy foi executado.
