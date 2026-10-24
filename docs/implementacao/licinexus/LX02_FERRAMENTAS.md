# LX02 — Testes individuais

18 ferramentas descobertas e testadas; 4 prompts e 2 recursos descobertos, sem tarefas de IA. Todos aceitaram os parâmetros após corrigir o caso de compra 1642 para 164. O HTTP da fonte é registrado separadamente da resposta MCP: um envelope MCP sem erro que ocultou HTTP 404 não foi aprovado como recuperação de dados. O detalhe de ata e os itens PCA não tiveram identidade de sequência confirmada; seus retornos são inconclusivos.

| Ferramenta | Funcionou | Dados | Integrado | Painel | Bloqueio / limite |
|---|---|---|---|---|---|
| search_licitacoes | NÃO | NÃO | NÃO | NÃO | HTTP 503 na rota de consulta; descoberta ampla não integrada. |
| get_licitacao | NÃO | NÃO | NÃO | NÃO | HTTP 503 na rota /api/consulta/v1, inclusive após corrigir a sequência do caso para 164. |
| list_licitacao_itens | SIM | SIM | SIM | SIM | HTTP 200; 2 itens de veículos existentes e 10 itens novos da Câmara de Ipatinga. Ingestão pelos mesmos IDs PNCP. |
| list_licitacao_resultados | SIM | SIM | SIM | SIM | HTTP 200; homologação de 2 utilitários, R$ 219.000,00; identidade já existente. Nova revisão, sem nova compra. |
| list_licitacao_arquivos | SIM | SIM | SIM | SIM | HTTP 200; 1 documento do processo de veículos preservado como evidência. |
| search_contratos | NÃO | NÃO | NÃO | NÃO | HTTP 503; busca ampla não integrada. |
| get_contrato | SIM | SIM | SIM | SIM | HTTP 200; detalhe do contrato 19875020000134-2-000035/2026 já conhecido. Evidência adicional, sem novo contrato. |
| list_contrato_termos | SIM | NÃO | NÃO | NÃO | HTTP 204 no contrato testado; resposta vazia válida, sem histórico adicional comprovado. |
| list_contrato_instrumentos | INCONCLUSIVO | NÃO | NÃO | NÃO | HTTP 404 convertido em [] pelo upstream; não comprova ausência de instrumentos ou pagamento. |
| search_atas_rp | NÃO | NÃO | NÃO | NÃO | HTTP 503; sem atas recuperadas. |
| get_ata_rp | INCONCLUSIVO | NÃO | NÃO | NÃO | HTTP 404 para sequência de ata não confirmada. Sem identidade de ata descoberta pela busca; resultado inconclusivo. |
| get_orgao | SIM | SIM | NÃO | NÃO | PNCP HTTP 404; fallback BrasilAPI HTTP 200. Cadastro complementar, não evidência oficial de compras ou filiação. |
| get_fornecedor_contratos | NÃO | NÃO | NÃO | NÃO | HTTP 503; sem contratos adicionais do fornecedor. |
| search_pca | NÃO | NÃO | NÃO | NÃO | HTTP 503; sem planejamento recuperado. |
| list_pca_itens | INCONCLUSIVO | NÃO | NÃO | NÃO | HTTP 204 para sequência PCA 1 não confirmada por índice. Sem validação de histórico ou completude. |
| get_cnpj_data | SIM | SIM | NÃO | NÃO | HTTP 200 BrasilAPI: cadastro CNPJ complementar. Não é origem governamental direta e não entrou em fatos de compra. |
| aggregate_licitacoes_por_periodo | NÃO | NÃO | NÃO | NÃO | HTTP 503; não substitui métricas IRPS. Nenhuma agregação promovida a fato. |
| compare_periodos | NÃO | NÃO | NÃO | NÃO | HTTP 503/429; não integrado. Sem comparação histórica ou percentual confiável. |

Evidências privadas: discovery.json, tool-results.json e requests.jsonl em .runtime/licinexus. Logs e respostas cadastrais não são publicados. A amostra pertence a municípios monitorados; nenhuma filiação ou regularidade foi inferida.
