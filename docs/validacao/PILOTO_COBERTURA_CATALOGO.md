# Piloto de fontes reais — Minas Gerais

Consulta executada em 20/10/2026, no ambiente local, à API pública do PNCP. Recorte: publicações de 01 a 07/09/2025, modalidade 6, três códigos IBGE, página de 10 registros. O limite autorizado pelo próprio piloto foi de **100 páginas**. O conjunto parou em `limited`, sem erro da fonte. Resumo verificável em [`PILOTO_PNCP_MG_2026-10-20.json`](PILOTO_PNCP_MG_2026-10-20.json); as respostas completas permanecem apenas no banco local de testes.

| Município informado na fonte | Publicações no recorte | Páginas de itens concluídas | Registros de itens retornados | Consultas de resultado concluídas | Registros de resultado retornados |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alfenas (3101607) | 6 | 33/33 | 291 | 40/263 | 125 |
| Ipatinga (3131307) | 2 | 1/2 | 5 | 1/5 | 1 |
| Turmalina (3169703) | 4 | 22/25 | 210 | 0 | 0 |

As três páginas iniciais de publicação foram conciliadas com o número de páginas informado pela fonte **somente para esses recortes de sete dias e modalidade 6**. O índice retornou 12 publicações. Foram obtidos 506 registros de itens e 126 registros de resultados nas páginas executadas. Há tarefas de itens e, sobretudo, de resultados pendentes. As contagens de páginas/linhas não equivalem a compras distintas nem a consumo. Os resultados podem ter data de homologação fora da semana usada para localizar a publicação.

Comprovantes iniciais de publicação (URL e SHA-256 do corpo recebido):

- [Alfenas, modalidade 6](https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20250901&dataFinal=20250907&codigoModalidadeContratacao=6&pagina=1&tamanhoPagina=10&codigoMunicipioIbge=3101607) — `9eb795fb85a9fe7cf8c8d491bcfb15ad584d81ca3b0e99cca767deb6f6dadc9f`.
- [Ipatinga, modalidade 6](https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20250901&dataFinal=20250907&codigoModalidadeContratacao=6&pagina=1&tamanhoPagina=10&codigoMunicipioIbge=3131307) — `106e0050f037cdbb82eb940021779eb84bf999e26860a48dfef93d4cb4a9cd9d`.
- [Turmalina, modalidade 6](https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20250901&dataFinal=20250907&codigoModalidadeContratacao=6&pagina=1&tamanhoPagina=10&codigoMunicipioIbge=3169703) — `2034770d3d6223d0abc74912f406d54d826af94c60a1d62edf909bd84a6e91e1`.

Um resultado realmente lido ilustra o nível de detalhe disponível: [autoclave horizontal, item 2 de uma compra ligada ao órgão CNPJ 01.243.423/0001-03](https://pncp.gov.br/api/pncp/v1/orgaos/01243423000103/compras/2025/29/itens/2/resultados), com 1 unidade, valor unitário e total documentados de R$ 3.999,00, data de resultado 15/09/2025. Esse registro é **resultado homologado informado pelo PNCP**; não comprova entrega, liquidação, pagamento, consumo nem necessidade futura. Seu município/código IBGE e a identidade jurídica do comprador precisam ser interpretados com o CNPJ e o documento de origem.

Também foram consultados os contratos públicos de referência do PNCP e o OpenAPI da consulta, a consulta de atas por compra e o PCA consolidado. A rota de atas de uma compra real respondeu HTTP 200 com objeto `data` e `totalPaginas`; o conector foi ajustado e coberto por regressão. O PCA do mesmo órgão/ano respondeu HTTP 404; o sistema registra “não encontrado, significado não confirmado”. A API pública do Compras.gov.br respondeu HTTP 200 para CATMAT e para pesquisa de preço de material por PDM 313; na consulta de 2025, ela declarou 3.150 registros em 315 páginas. Essa consulta demonstra acesso e formato, **não** cobertura de Alfenas, Ipatinga ou Turmalina.

Qualidade observada no piloto: 3/3 consultas de índice de publicação com páginas reconciliadas; 56/60 tarefas de itens concluídas; 41/268 tarefas de resultado concluídas; 100/100 páginas do orçamento executadas. Os denominadores de tarefas vêm apenas do plano de coleta gerado, não da totalidade das compras ou homologações municipais. O painel mantém `source_completeness_ratio = null`.

Pendências para ampliar o piloto: estender o limite de páginas com monitoramento e intervalos adequados; consultar outras modalidades e períodos; identificar CNPJs dos órgãos e confrontar vínculos municipais; validar contratos e fornecedores por processo; obter fonte complementar para execução financeira; localizar contrato público estável de TCE-MG/Sicom e portais municipais. Nenhuma dessas lacunas impede usar os fatos efetivamente coletados com as ressalvas apresentadas.
