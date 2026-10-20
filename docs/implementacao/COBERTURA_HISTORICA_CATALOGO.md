# Cobertura histórica e catálogo inteligente — incremento revisável

## O que funciona

A coleta oficial PNCP continua paginada e retomável. Este incremento permite recortes de até cinco anos e modalidades 1–14, separa publicação de atualização, consulta itens e resultados vinculados, contratos e suas atualizações por CNPJ, atas por compra, atualizações de atas, PCA consolidado e atualizações de PCA. Cada tarefa tem chave estável, estado, tentativas, página e observação com URL, data e SHA-256. `scripts/avancar_coletas.py` executa apenas um lote limitado de coletas previamente criadas; a frequência de acionamento fica com o agendador local. Pausa humana, 429/503, `Retry-After`, limite de páginas e falhas permanecem visíveis.

O painel `/catalogo-inteligente` mostra municípios, órgãos/CNPJ identificados, fonte, modalidade, período, fase, páginas planejadas e comprovantes. `request_completion_ratio` compara **somente páginas planejadas** com páginas conciliadas no recorte. `source_completeness_ratio` permanece nulo. Resultados homologados, atas, PCA, contratos, empenhos e pagamentos não herdam a cobertura da data de publicação. Um resultado consultado para item conhecido não comprova todos os resultados do município. O código IBGE informado para a unidade localiza o registro; sua vinculação jurídica ao município comprador exige conferência do órgão/CNPJ.

O reprocessamento salva `item_normalization` por fato e versão do algoritmo, sem alterar a resposta original, o fato, o documento ou a revisão humana. Descrição e unidade originais, chave textual normalizada, código de catálogo, embalagem, confiança e conflitos ficam disponíveis. Sugestões com código/unidade/embalagem compatíveis ainda exigem revisão explícita. `canonical_product` é imutável e versionado por `supersedes_id`; o bloqueio transacional impede que um mesmo item ativo pertença a dois produtos revisados. Unidades e embalagens conflitantes são rejeitadas. A visão de Oportunidades aceita agrupamento por produto revisado e conserva a revisão de viabilidade vinculada ao contexto avaliado. Quantidade observada, preço e valor só são apresentados na fase selecionada, sem inferir consumo ou necessidade futura.

A consulta de preços do Compras.gov.br usa os endpoints oficiais de preços praticados por código CATMAT/CATSER. Ela busca **uma página por ação**, informa total de páginas declarado pela fonte e guarda apenas campos públicos necessários; nome/identificador de pessoa física não são persistidos. Esses preços são pesquisa de referência, não prova de cobertura municipal nem equivalência técnica automática. O catálogo CATMAT/CATSER já existente permanece disponível.

## Fontes e contratos consultados

| Fonte | Rota oficial usada | Situação nesta branch |
| --- | --- | --- |
| PNCP consulta | `GET /v1/contratacoes/publicacao`, `/atualizacao` | Coleta real paginada, por data, modalidade e código IBGE |
| PNCP consulta | `GET /v1/contratos`, `/atualizacao` | Coleta por CNPJ de órgão; contrato fica fora do somatório dos itens |
| PNCP público | `GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens` e `/itens/{item}/resultados` | Itens e resultados distintos; consulta de resultado não prova completude da fase |
| PNCP público | `GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/atas` | Resposta real pode trazer `data`, `totalPaginas`; índice observado, sem quantidade de compra inferida. Paginação além da primeira não é presumida sem parâmetro documentado. |
| PNCP público | `GET /v1/orgaos/{cnpj}/pca/{ano}/consolidado` | Plano observado separadamente. HTTP 404 fica como “não encontrado, significado não confirmado”. |
| PNCP consulta | `GET /v1/atas/atualizacao`, `/v1/pca/atualizacao` | Índices de atualização observados, sem fatos de compra inferidos |
| Compras.gov.br | `/modulo-material/4_consultarItemMaterial`, `/modulo-servico/6_consultarItemServico` | Catálogos já existentes |
| Compras.gov.br | `/modulo-pesquisa-preco/1_consultarMaterial`, `/3_consultarServico` | Consulta pontual de preço por código oficial, com fonte e limite |
| TCE-MG/Sicom | Portal oficial de dados abertos | Portal identificado, mas sem contrato de API validado nesta rodada; nenhuma coleta automatizada declarada |
| Portais municipais | Dependem do município e órgão | Nenhum conector genérico sem contrato público comprovado |

Referências: [OpenAPI da consulta PNCP](https://pncp.gov.br/api/consulta/v3/api-docs), [manual de atas do PNCP](https://pncp.gov.br/manual/pt-br/latest/ata_de_registro_de_preco/consultar_atas_de_registro_de_preco_por_compra.html), [Swagger do Compras.gov.br](https://dadosabertos.compras.gov.br/swagger-ui/index.html), [portal do TCE-MG](https://dadosabertos.tce.mg.gov.br/).

## Limites de implementação

- O piloto cobre apenas três municípios, uma semana e uma modalidade. Os 118 municípios continuam cadastrados, mas o cadastro não comprova seu histórico.
- A soma de publicações, itens, resultados, contratos e atas seria duplicação de fases; cada tela consulta uma situação de cada vez.
- Resultados e preços do PNCP dependem de itens alcançados pela coleta. Não há denominador oficial de todos os resultados homologados, entregas, pagamentos ou consumo.
- O PNCP devolve respostas distintas do exemplo textual do manual para atas; a primeira página é preservada com seu total declarado. O app não pagina por parâmetro que não tenha sido documentado.
- Um 404 de PCA ou ata não prova inexistência do documento. O estado técnico mantém essa incerteza.
- Comparação de itens exige especificação, unidade, embalagem e revisão. Códigos iguais ajudam a sugerir; não substituem essa decisão.
- A consulta de Compras.gov.br pode refletir compras federais e outras esferas e não amplia automaticamente a cobertura de municípios.
- Não há vínculo comprovado entre publicação/resultado e execução financeira municipal. Conectores TCE-MG e portais requerem análise por endpoint/arquivo, licenças, atualização e reconciliação.
- O agendador local não é serviço de produção; faltam gestão operacional, monitoramento e políticas de retenção para implantação.

## Operação local

Após configurar `.runtime/config-local.json` e aplicar `alembic upgrade head` no ambiente local, iniciar API e frontend conforme o README. A página **Atualizar histórico** prepara uma coleta e permite avançar página a página. Para executar lotes já autorizados via agendador externo:

```powershell
.\.venv\Scripts\python.exe scripts\avancar_coletas.py --collections 5 --pages-each 1
```

O piloto reproduzível, limitado a três municípios e sem IA paga, usa `scripts/piloto_cobertura.py`. Ele exige `auth_mode=local_test`; não usa credenciais privadas para as consultas públicas. Sua evidência resumida está em [`PILOTO_PNCP_MG_2026-10-20.json`](../validacao/PILOTO_PNCP_MG_2026-10-20.json).
