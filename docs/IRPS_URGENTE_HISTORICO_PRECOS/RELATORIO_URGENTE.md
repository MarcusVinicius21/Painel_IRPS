# IRPS — relatório urgente de histórico e preços

Data de fechamento: 23/10/2026, horário de Brasília. Execução local U0 → U4.

## Entrega operacional

**Aplicação funcionando: http://127.0.0.1:5296/**. O Chrome está aberto com um único operador, em duas abas: CATSER 14729 e CATMAT 463700. A pesquisa principal consulta preços oficiais ao selecionar um código, mesmo sem vínculo PNCP. O histórico PNCP permanece independente, com fase, unidade, município, fonte e limitações.

- Catálogo preservado: **345.575 CATMAT + 3.104 CATSER = 348.679 códigos**.
- Fatos PNCP correntes preservados: **495**, sem somar fases como novas compras.
- Preços mensais importados: **114.029 linhas de material + 25.292 de serviço = 139.321**, exclusivamente setembro/2026.
- Códigos do catálogo com preços no mês importado: **42.313 CATMAT + 1.250 CATSER = 43.563**, ou **12,49372632%** dos 348.679 códigos. Isso mede presença no arquivo importado; não cobertura de todas as compras, anos ou municípios.
- Nenhum registro sintético inserido no operacional; V4, operador e dados anteriores preservados.

## U0 — erros reproduzidos antes da edição

Branch inicial/final: `checkpoint/irps-integrado-i17-04-2026-10-22`; HEAD `a83e3205e685370e12ad6c42bd17f57bba20a6ff`. Pasta real do Windows utilizada. O diff acumulado foi preservado e copiado para controle privado antes de editar. Não houve checkout, reset, limpeza, commit, push, PR, merge ou deploy.

| Caso confirmado | HTTP real | Causa e efeito | Correção |
|---|---:|---|---|
| CATSER 14729: API com quantidade 1 e valor 1590, mas resumo visual de planejamento | 200 | A etapa histórico usava cards de necessidade/meta em vez do contrato histórico | Usa history.summary por historyIndicators; vínculo único dispara consulta no contexto selecionado |
| Segunda consulta de preços perde campos | 200 nas duas chamadas | Cache armazenava linhas saneadas e as reinterpretava como JSON bruto do fornecedor | Leitura versionada, compatibilidade explícita com páginas antigas válidas e rejeição das páginas antigas com campos vazios |
| Cache não se renova quando a resposta externa se repete | 200 | Deduplicação devolvia observação antiga, mantendo a data fora dos cinco minutos | Recibo imutável por consulta HTTP efetiva; preserva separadamente o identificador do conteúdo original |
| Unidade de serviços ausente apesar de existir na fonte | 200 | Leitura limitada ao campo nomeUnidadeFornecimento | Aceita nomeUnidadeMedida e siglas, preservando o que a fonte informou |
| Origem exposta como JSON bruto | 200 | SelectedItem imprimia item.origin diretamente | Fonte, versão, URL, contagem, importação e identificador legíveis; certificação derivada no servidor também no endpoint de detalhe |
| Identificadores de compras grandes tratados como números | 200 | Alguns idCompra excedem a precisão inteira do JavaScript | Identificadores enviados como texto, inclusive ao ler cache anterior; testes protegem os 17 dígitos |
| auth/context antes de entrar | 401 INVALID_TOKEN | Ausência de sessão; comportamento esperado | Mantido; sessão expirada volta ao login sem expor credenciais |
| Período de preços superior a 366 dias, provocado pelo teste | 422 PRICE_PERIOD_INVALID | Validação, não indisponibilidade da fonte | Aviso para corrigir o período, sem repetição automática |

**Não reproduzimos 429 ou 5xx da fonte oficial durante os exemplos reais desta rodada.** Esses casos foram simulados somente em QA para validar tratamento. O HTTP 200 com campos vazios era um erro semântico do cache, não prova de fonte indisponível.

Provas anteriores à alteração: U0_REPRODUCAO.json e três capturas U0. O arquivo registra respostas, resumo da API, texto do DOM, console/pageerror e caminhos HTTP saneados. MATRIZ_ERROS.csv separa defeitos reais, validações intencionais e falhas simuladas. SERVICO_HTTP_AMOSTRA.log é uma amostra sanitizada do serviço, não um histórico completo.

## U1 — preços sob demanda: CONCLUÍDO

O componente OfficialPrices reutiliza **GET /api/v1/catalogue-intelligent/reference-prices**. A função pública catalogue.reference_prices permanece como ponto de entrada, delegando ao conector corrigido. Não foi criado outro serviço externo de preços.

Rotas oficiais conferidas no Swagger vigente:

- Material: https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial — tipo=codigoItemCatalogo e codigo.
- Serviço: https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico — codigoItemCatalogo.
- Documentação: https://dadosabertos.compras.gov.br/swagger-ui/index.html

A interface oferece período independente do histórico PNCP, até 366 dias, dez registros por página, anterior/próxima, carregamento, ausência comprovada, erro e nova tentativa. Mostra código/tipo, descrição, especificação, embalagem, quantidade/unidade, preço unitário em reais, comprador/UASG, município/UF informados, datas e link público. Campo ausente continua ausente.

Trocar código/período cancela a espera no cliente e ignora respostas atrasadas. O servidor limita páginas; não há varredura dos 348.679 códigos. O cache é consultado por fonte/tipo/código/período/página e organização. CATMAT e CATSER com o mesmo número não compartilham resultados.

O vínculo PNCP não condiciona os preços do Compras.gov.br. Um NOBREAK sem código nacional certificado continua acessível pela identidade original do item publicado. Não foi criada associação por palavra em comum. Publicações estimadas, homologações e contratos continuam separados pelo filtro de fase; preços do Compras.gov.br não entram nos fatos ou totais PNCP.

### Exemplos reais demonstrados

| Recorte | Resultado observado |
|---|---|
| CATSER 14729, API, 01/01 a 23/10/2026 | 1.090 registros informados pela fonte; dez por página. Exemplo: treinamento, quantidade 1 UNIDADE, preço unitário R$ 5.190,00, Comando da Marinha, compra 19/10 e resultado 20/10/2026 |
| CATSER 14729, PNCP homologado, Ipatinga e Timóteo | Um registro em Timóteo, Câmara Municipal, 1 UNIDADE e R$ 1.590,00 documentados. Não é o mesmo registro do exemplo nacional acima |
| CATMAT 463700, API, 01/01 a 23/10/2026 | 66 registros informados. Item: gordura vegetal/margarina sem sal. Exemplo: 100 EMBALAGENS de 15 KG, preço unitário R$ 135,69; Fundo Municipal de Assistência Social de Casimiro de Abreu/RJ, UASG 928206. Não convertido em outra unidade |
| CATMAT 10006, código existente no catálogo, mesmo período | Resposta oficial vazia: zero registros retornados naquele recorte; não afirma que nunca houve compra |
| NOBREAK por identidade PNCP | 7 UNIDADES e R$ 2.113,37 estimados no registro publicado, com fonte e unidade originais. Sem vínculo nacional certificado, sem homologação inventada e sem classificar o órgão estadual como prefeitura |

Links verificáveis:

- CATSER: https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico?codigoItemCatalogo=14729&dataCompraInicio=2026-01-01&dataCompraFim=2026-10-23&pagina=1&tamanhoPagina=10
- CATMAT: https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial?tipo=codigoItemCatalogo&codigo=463700&dataCompraInicio=2026-01-01&dataCompraFim=2026-10-23&pagina=1&tamanhoPagina=10
- Declaração nacional no item PNCP da Câmara: https://pncp.gov.br/api/pncp/v1/orgaos/17112673000136/compras/2026/44/itens?pagina=1&tamanhoPagina=20

As respostas são snapshots datados; as fontes podem mudar depois da consulta. U1_PRECOS_REAIS.json, U1_CATMAT_PRECOS.json e U4_CHROME.json preservam os exemplos sem cabeçalhos de autenticação.

## U2 — erros, cache e segurança: CONCLUÍDO

- Respostas identificam available, empty_valid_response, source_unavailable, partial, not_collected ou needs_review conforme o caso.
- Falha sem evidência preservada retorna erro explícito (502 ou 429), com código técnico, status externo quando recebido e prazo de espera. Não retorna uma falsa ausência de compras.
- 429/503 ativam backoff por fonte; não há loop automático. 400/422 exigem correção de parâmetros. Timeouts/conexão/JSON malformado são identificados sem traceback no navegador.
- Se houver página preservada para o mesmo recorte, ela aparece com data original e aviso de atualização falha. Sem essa página, o arquivo mensal pode servir de fallback, identificado como tal, se contiver resultados daquele código/período.
- O operador também pode escolher explicitamente “Arquivos mensais já importados”. Meses não importados não viram zero.
- A interface preserva os demais painéis durante falha de uma fonte. Sessão expirada retorna ao login; não há senha embutida no cliente nem renovação por credencial exposta.

**Aviso do Chrome:** o argumento --no-sandbox é distinto de falha de coleta. Os testes e a janela deixada aberta usam chromiumSandbox=true. A leitura real de chrome://version confirmou ausência de --no-sandbox, --disable-web-security e --ignore-certificate-errors na janela aberta. Não foi ocultado um aviso mantendo o sandbox desligado. O endereço local permanece HTTP em loopback; não foi instalada certificação nem preparado acesso de produção.

## U3 — piloto mensal: CONCLUÍDO para setembro/2026

Repositório: https://repositorio.dados.gov.br/seges/comprasgov/pesquisa_precos/

O LEIAME oficial explica UTF-8, separador ponto e vírgula, particionamento por data_compra, atualização semanal e possível substituição de meses anteriores. Orienta uso dos arquivos; não foi identificada uma licença nominal no LEIAME consultado, e não foi inventada uma atribuição de licença.

| Arquivo | ZIP bytes | CSV bytes | Linhas aceitas | Rejeições / duplicações exatas |
|---|---:|---:|---:|---:|
| material_2026_09.csv.zip | 19.696.451 | 129.275.984 | 114.029 | 0 / 0 |
| servico_2026_09.csv.zip | 3.527.134 | 23.428.700 | 25.292 | 0 / 0 |

- Material SHA-256: 2db1fa67fbd15afb3a4ad18faa1e9ba9c1f382beb81b3a19bb7c9c0ad7c50b13
- Serviço SHA-256: 51ab278c0baddd6812fcc849b7563bfdfdd832b7c19914a234f979ca6a9ec417

Hashes calculados localmente, tamanhos conferidos com a fonte e CRC dos ZIPs validado. Não há alegação de checksum assinado pelo fornecedor. Os arquivos originais permanecem privados no disco; não integram o ZIP de revisão.

Antes da alteração de esquema, backup consistente de 17.827.141 bytes foi restaurado em banco descartável. Conferidos os 348.679 códigos e os 495 fatos correntes restaurados. O banco operacional não foi recriado.

Foi necessária a migração **0015**, exclusivamente aditiva, para price_monthly_snapshot e price_monthly_record, com FORCE RLS, escopo por organização, índices de código/período e bloqueio de alteração/exclusão. Ela foi aplicada primeiro em QA e depois no operacional. As migrações também foram validadas do zero e repetidas até head 0015 em banco descartável.

Importação transacional por staging/COPY; limite conservador de tamanho/linhas; reconciliação de contagens; chave de origem id_compra + id_item_compra; hash por linha; arquivo, versão, registro lógico CSV e data rastreáveis. Repetição idempotente confirmada para os dois arquivos. Novas versões de arquivo geram snapshots novos; versões conflitantes de um mesmo item permanecem visíveis para revisão. Nenhum preço mensal é inserido como fato PNCP, necessidade V4 ou manifestação municipal.

**Qualidade:** 23.050 linhas de materiais e 2.969 de serviços não informam unidade (26.019 no total). Todas as linhas aceitas possuem quantidade e preço numéricos documentados, mas isso não basta para comparabilidade. O código de serviço 271377 aparece uma vez no arquivo e não foi localizado no CATSER importado. Foi preservado com indicação de revisão, sem reclassificação para CATMAT. Essa linha não entra nos 43.563 códigos oficiais com preços associados.

### Comparação API x arquivo

No recorte setembro/2026:

- CATMAT 463700: API e arquivo informam dois registros; as duas chaves comparadas apresentam mesmos valores e quantidades.
- CATSER 14729: API informa 223 registros, arquivo 224. Entre as primeiras páginas, nove chaves comuns apresentam mesmos preços e quantidades. A comparação não percorreu as 223 linhas da API, nem prova igualdade integral.

O arquivo foi publicado em 17/10; a API foi consultada em 23/10. Atualizações posteriores podem explicar diferenças, mas **a causa da linha divergente não foi determinada**. As versões foram mantidas separadas. Não houve fusão cega ou soma dos registros.

## U4 — validação e evidências

Execuções finais:

- Suíte backend completa em PostgreSQL descartável novo: **316 testes + 200 subtestes aprovados**.
- Testes focados de preço mensal e cache: **15 aprovados** na execução registrada. Rechecagem final de histórico, contrato e estudos: **45 aprovados**.
- Playwright em Chrome real no operacional: **uma jornada abrangente aprovada**, incluindo paginação, período inválido 422, resposta vazia, arquivo mensal, CATSER, CATMAT, NOBREAK e origem legível. Nenhuma fonte sintética foi usada nesse fluxo.
- Build TypeScript/Vite aprovado.
- Migrações novas e idempotência aprovadas até 0015; RLS das oito tabelas verificadas preservada.
- Oito módulos V4 byte a byte iguais ao manifesto original; sete referências originais sem diff.
- Um operador, uma organização, um vínculo; nenhum sintético em fatos, itens, cenários ou documentos operacionais.
- git diff --check aprovado.

Uma repetição intermediária da suíte em base QA reutilizada teve **315 aprovados e uma falha NORMALIZATION_REQUIRED** no teste de histórico. O teste reprocessa no máximo 500 fatos, enquanto a base acumulava fixtures de outras execuções. Foi preservada a falha e repetida a suíte em banco novo. Não foram alteradas as asserções desse teste, o reprocessamento de produção ou os cálculos para acomodar a base. Logs intermediários relevantes acompanham a revisão.

Avisos não bloqueantes: depreciação Starlette/httpx, chave curta intencional no teste de JWT inválido e diretiva use client ignorada em dependência do build. Não correspondem a uma credencial operacional exposta.

Comandos principais efetivamente executados:

```powershell
node .runtime/urgente-precos/u0.mjs
.venv/Scripts/python.exe -m pytest backend/tests/test_monthly_prices.py backend/tests/test_reference_prices_runtime.py -q --tb=short
.venv/Scripts/python.exe .runtime/urgente-precos/backup-restaurar.py
# backend/, com IRPS_LOCAL_CONFIG privado apontando primeiro para QA, depois para operacional
../.venv/Scripts/python.exe -m alembic upgrade head
# raiz, alvo operacional explicitamente conferido
.venv/Scripts/python.exe scripts/importar_precos_mensais.py --target-database irps_operacional_local_ab7af83a1b --month 2026-09 --manifest docs/IRPS_URGENTE_HISTORICO_PRECOS/U3_INTEGRIDADE_ZIPS.json --backup-proof docs/IRPS_URGENTE_HISTORICO_PRECOS/U3_BACKUP_RESTAURADO.json
.venv/Scripts/python.exe .runtime/urgente-precos/migrar-qa.py --evidence-dir .runtime/urgente-precos
.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short --junitxml=.runtime/urgente-precos/python.xml
# frontend/, IRPS_BASE_URL=http://127.0.0.1:5296 e IRPS_URGENT_REAL=1
npx.cmd playwright test qa/urgent-prices-real.spec.ts
npm.cmd run build
# raiz
git diff --check
```

## Arquivos e contratos

Alterados nesta rodada:

- backend/app/catalogue.py: mantém a função pública de preços e delega ao conector corrigido.
- backend/app/price_queries.py (novo): cache, normalização, recibos, backoff, falhas e snapshots de preços.
- backend/app/national_catalogue.py: detalhe do código com certificação de origem aditiva, igual à busca.
- backend/app/opportunity_routes.py: status explícito de falhas, fallback mensal e GET monthly-prices.
- backend/app/monthly_prices.py (novo): importação e leitura mensal indexada, independente de PNCP.
- backend/migrations/versions/0015_monthly_prices.py (novo): duas tabelas append-only com RLS.
- scripts/importar_precos_mensais.py (novo): piloto local explícito, manifesto e prova de backup.
- frontend/src/connected/Director.tsx: resumo histórico correto, consulta de vínculo único e painel independente de preços.
- frontend/src/api.tsx: erro estruturado compatível com Error, preservando status/código/detalhes saneados.
- frontend/src/components/OfficialPrices.tsx e CatalogueOrigin.tsx (novos): preços por fonte e origem legível.
- frontend/src/components/official-prices.css (novo): altura automática apenas do resumo histórico, para impedir sobreposição de dados reais.
- frontend/src/components/WorkflowUI.tsx: usa apresentação de origem legível.
- frontend/src/components/HistoryDetails.tsx e MunicipalMatrix.tsx: nome e CNPJ do comprador nas evidências; backend expõe esses campos de forma aditiva, sem mudar os agregados.
- backend/tests/test_reference_prices_runtime.py, test_monthly_prices.py e frontend/qa/urgent-prices-real.spec.ts (novos): regressões e demonstração real.

GET reference-prices preserva os campos anteriores e adiciona state, scope, source_error, cache_hit, has_next_page e dados de unidade/especificação/comprador. Identificadores de compra passam a texto para evitar perda de precisão. GET monthly-prices aceita kind/code/start/end/page e identifica meses importados, revisão e linhas de origem. Nenhum desses contratos aprova equivalência, preço de referência formal ou quantidade futura.

## Limites remanescentes e próximos lotes

1. Apenas setembro/2026 foi importado integralmente desses dois arquivos. Não há afirmação de cobertura anual, nacional de todas as fontes ou completa de um município.
2. Comparabilidade continua exigindo especificação/unidade/embalagem/data; não se calculou média automática, previsão, economia ou necessidade futura.
3. Unidades ausentes e código de serviço não localizado exigem conferência. Não foram completados com valores presumidos.
4. PNCP permanece com o piloto já documentado e seus limites. Importar preços federais não amplia automaticamente cobertura municipal PNCP.
5. NOBREAK segue sem associação CATMAT nacional certificada; não houve aprovação humana fabricada.
6. Nenhum plano futuro, IRP, documento administrativo, manifestação ou publicação oficial foi criado nesta rodada para aparentar sucesso.
7. Próximos meses devem repetir integridade, backup, limites, staging e reconciliação. Não foi iniciada varredura histórica massiva nem serviço pago.

## Pacote de revisão

GALERIA.html contém capturas separadas antes/depois, desktop 1672×941, evidência do quadro PNCP e captura mobile 390px. São provas de operação, sem declaração pixel-perfect. TESTES.log/XML, matriz de falhas, HTTPs, métricas SQL, conciliações e Git acompanham o pacote.

DIFF_INCREMENTO.patch compara esta rodada com o backup inicial e inclui os arquivos novos. DIFF_LOCAL_ACUMULADO.patch inclui código acumulado desde HEAD, preservando o trabalho anterior; não é autorização para substituí-lo por um patch histórico.

O ZIP exclui banco, backups, dependências, arquivos de configuração privada, senhas, sessões, chaves e arquivos mensais brutos com dados pessoais de fornecedores. As origens públicas e hashes continuam rastreáveis. Nenhum commit, push ou deploy foi executado.
