# Catálogo completo e histórico real — E0 a E5

## Resultado executivo

A aplicação operacional está em http://127.0.0.1:5296/ e foi aberta no Chrome com o operador único. Foram importados **345.575 códigos CATMAT e 3.104 CATSER: 348.679 códigos**, a partir dos CSVs oficiais publicados em 17/10/2026. A reconciliação integral por conjuntos de códigos encontrou zero ausências, extras, rejeições ou duplicações. **100% significa integralidade desses dois arquivos identificados**, incluindo ativos e inativos; não significa cobertura integral de compras públicas.

A busca usa paginação no servidor, contagem real do recorte, código exato, descrição com normalização de acentos, filtros e acesso à primeira/última página. Foram testadas também a passagem CATMAT→CATSER e consultas com deslocamento alto. Não há carregamento de centenas de milhares de códigos no navegador.

O piloto PNCP foi ampliado para Ipatinga e Timóteo, com **138 consultas paginadas comprovadas**. Há **495 fatos atuais**, classificados separadamente: 29 publicações, 389 linhas de itens publicados, 75 resultados homologados e 2 contratos. Esses números **não podem ser somados como quantidade de compras independentes**. Versões anteriores foram preservadas.

## Estado inicial e preservação

Pasta real: `C:/Users/NEXUS/Downloads/TRAMPOS/IRPs/Painel_IRPS`. Branch `checkpoint/irps-integrado-i17-04-2026-10-22`, HEAD `a83e3205e685370e12ad6c42bd17f57bba20a6ff`. O diff local anterior, inclusive login único e piloto oficial, foi preservado. Não houve commit, push, PR, merge ou deploy. Não foi aplicado patch histórico, substituído o banco ou copiada a base QA.

O banco operacional tinha zero códigos nacionais. Os 348.679 códigos anteriores estavam em uma base QA distinta; sua importação original não certificava a fonte. O importador também recusava o modo operacional. A nova base operacional havia sido criada sem essa carga, explicando a pesquisa vazia. Os hashes antigos coincidem com os arquivos agora obtidos diretamente do repositório oficial; a confirmação foi independente, sem copiar dados QA.

Antes da importação foram feitos backups consistentes, verificados com pg_restore --list e protegidos por ACL. Permanecem somente na pasta privada `.runtime`; não fazem parte deste pacote. O importador exige o nome exato do banco local alvo, manifesto oficial e identidade operacional válida. Importação e staging são transacionais, com conferência de hash/quantidade antes do commit. Não foram criadas migrações nesta rodada.

## E0 — diagnóstico: CONCLUÍDO

Leitura do estado Git, banco/configuração efetivos, contratos, snapshots antigos e histórico NOBREAK. Evidências em E0_DIAGNOSTICO.md, E0_CONTAGENS.json, E0_NOBREAK_HISTORICO.json e capturas E0. O histórico existente não foi apagado nem convertido em correspondência CATMAT automática.

## E1 — fonte e importação: CONCLUÍDO para os snapshots identificados

Fonte de descoberta: https://www.gov.br/compras/pt-br/cidadao/portal-de-dados-abertos

Repositório: https://repositorio.dados.gov.br/seges/comprasgov/catalogo_cnbs/

| Arquivo oficial | Registros | Ativos | Inativos | Bytes | SHA-256 |
|---|---:|---:|---:|---:|---|
| catmat.csv | 345.575 | 250.034 | 95.541 | 129.107.488 | 4c8c69973d4a3130421a79f95c5a11506f7c19439d812da3bebd08d37cb6e140 |
| catser.csv | 3.104 | 3.022 | 82 | 518.306 | 06372173e2f3fd56b311e1504a6314082459d85556e450b7fdb14d4e74adf22f |

Formato UTF-8, separador ponto e vírgula. Última modificação HTTP: 17/10/2026 09:02:04 UTC e 09:02:05 UTC. O LEIAME oficial descreve substituição semanal completa, com ativos e inativos. Datas, URLs, headers, hashes, quantidades e comparação de todos os códigos estão em CONCILIACAO_CATMAT_CATSER.json. Arquivos grandes permanecem privados no disco e não são repetidos no ZIP.

## E2 — pesquisa completa: CONCLUÍDO

GET `/api/v1/national-catalogue`: resposta aditiva com total, offset, limit, next_offset, last_offset e selected_snapshots. Mantidos records e snapshots anteriores. Consulta exata por código; busca textual sem acentos é descoberta, não equivalência. Contagem correta para filtros ativo/inativo, grupo, classe e tipo. Deslocamentos mistos não eliminam serviços.

A paginação usa seleção materializada das chaves antes de buscar metadados/vínculos das 25 linhas. Índices existentes de chave e busca permanecem; definições em E5_METRICAS.json. Última página CATMAT medida em aproximadamente **113 ms**, contra 8,6 s antes do ajuste desta rodada; não é SLA. Medições reais em E2_PAGINACAO_OTIMIZADA.json. O endpoint continua limitado a 50 resultados por chamada.

A interface distingue catálogo oficial, registros coletados, vínculo verificado e ausência de consulta suficiente. Tipo de catálogo altera a consulta efetiva; botões primeira/última página funcionam. Origem não certificada não recebe selo de catálogo oficial.

## E3 — coleta pública: CONCLUÍDO no piloto delimitado; cobertura histórica ampla PARCIAL

Janelas de publicações: **16–22/10/2025 e 16–22/10/2026**, modalidades 4, 6, 8 e 9, municípios IBGE 3131307 e 3168705. Os itens e resultados derivam dos processos encontrados nessas janelas. Contratos e índice de atualização de atas foram consultados para os CNPJs municipais documentados. Não foram varridos todos os meses, todas as modalidades ou todos os órgãos.

| Plano | Páginas/tarefas comprovadas | Estado |
|---|---:|---|
| Publicações/itens/resultados 2026 | 30 | Concluído no escopo |
| Publicações/itens/resultados 2025 | 104 | Concluído no escopo |
| Contratos | 2 | Concluído no escopo |
| Índices de atas atualizadas | 2 | Concluído no escopo |

138/138 tarefas materializadas possuem evidência de resposta bem-sucedida. A expansão dinâmica de páginas foi feita com checkpoints e lotes limitados; o limite do plano 2025 foi ampliado explicitamente após constatar páginas pendentes. Pausas, backoff e parada para restrições continuam ativos. Não houve resposta 429/503 nessas 138 consultas; isso não comprova comportamento das fontes em outros horários. Testes isolados cobrem erros/retomada já existentes.

| Fatos atuais | Ipatinga | Timóteo | Total |
|---|---:|---:|---:|
| Publicações | 13 | 16 | 29 |
| Linhas publicadas de itens | 334 | 55 | 389 |
| Resultados homologados | 38 | 37 | 75 |
| Contratos | 0 encontrados neste piloto | 2 | 2 |

O zero de linhas de contrato no piloto de Ipatinga não significa ausência de contratos municipais. As 18 entradas de índice de atas são evidências auxiliares de atualização, não 18 novas compras nem quantidades consolidadas. Linhas retornadas por páginas sobrepostas não foram contadas novamente como fatos atuais. Há 509 versões persistidas, 495 atuais; histórico anterior preservado.

`COBERTURA_PNCP_POR_ESCOPO.csv` e `E3_LEDGER.json` registram plano, tarefa, URL, data, status, hash, argumentos, município/CNPJ/modalidade quando determinados, fase e contagens. `E3_COBERTURA_2025.json`/2026 mantêm completude das fontes como desconhecida quando não há denominador. 100% do plano de requisições não é 100% das compras das cidades.

Foram distinguidos Prefeitura de Ipatinga (19876424000142), Prefeitura de Timóteo (19875020000134), Câmara de Timóteo (17112673000136) e outros compradores. Um órgão estadual localizado em Ipatinga não foi rotulado como prefeitura.

## E4 — associação nacional: CONCLUÍDO para a identidade comprovada; demais vínculos PARCIAIS

Em 410 linhas de respostas originais de itens, apenas uma declarou catálogo nacional verificável; as outras 409 não forneceram essa declaração. Esse denominador contém respostas sobrepostas, não representa 410 compras distintas.

Foi associada a identidade individual do **CATSER 14729 — Treinamento na Área de Administração Pública** ao item 1 da compra 44/2026 da **Câmara Municipal de Timóteo**. Unidade original UNIDADE; quantidade homologada 1; valor documentado R$ 1.590,00. Não é pesquisa formal de preço nem previsão de necessidade.

Fonte: https://pncp.gov.br/api/pncp/v1/orgaos/17112673000136/compras/2026/44/itens?pagina=1&tamanhoPagina=20

A regra exige simultaneamente objeto catálogo CNBS id 1, nome e URL oficiais, materialOuServico=S, código 14729, descrição compatível por correspondência explícita do título completo, versão e unidade originais, ausência de conflito de embalagem e hash da resposta íntegro. O produto contém somente essa identidade e versão; nenhum outro item foi fundido. O CSV nacional não define unidade de fornecimento; foi preservada a unidade declarada pelo órgão, sem conversão.

**O CATMAT também contém o número 14729 para outro material.** Testes rejeitam esse cruzamento. A associação automática prova origem declarada, não conferência humana, equivalência entre compras ou aprovação de necessidade. Essa distinção está na resposta, auditoria e interface.

Vínculo manual exige conferência explícita e justificativa; uma declaração nacional conflitante ou embalagem incompatível é recusada. Candidatos por descrição nunca são vinculados automaticamente. A ação de preparar conferência cria/reutiliza somente a identidade original e mantém a aprovação pendente. O endpoint de candidatos é limitado e informa truncamento.

**NOBREAK:** existe item oficial coletado, consultável pela sua identidade na fonte. Não possui código nacional declarado com catálogo verificável. A pesquisa nacional por NOBREAK também retorna acessórios, suportes e peças; palavra em comum não comprova o mesmo equipamento. O histórico do item coletado pode ser aberto sem fingir vínculo CATMAT. Sua associação nacional permanece para revisão documentada. Nenhuma confirmação humana foi fabricada.

### Percentuais separados, como solicitado

- Disponibilidade para pesquisar os arquivos oficiais importados: **CATMAT 100%; CATSER 100%; conjunto 100% (348.679/348.679)**.
- Códigos CATMAT com histórico nacional vinculado comprovado neste banco: **0/345.575 = 0%**.
- Códigos CATSER com histórico vinculado comprovado: **1/3.104 = 0,03221649%**.
- Conjunto com histórico vinculado comprovado: **1/348.679 = 0,00028680%**.

Essas últimas proporções medem códigos importados que já têm vínculo neste piloto, **não cobertura de todas as compras existentes**. Os 348.678 demais códigos continuam pesquisáveis; não se afirma que nunca foram comprados. Histórico de itens sem código nacional continua disponível separadamente.

## E5 — execução e testes: CONCLUÍDO com limites explicitados

| Execução real | Resultado |
|---|---|
| Pytest focado (catálogo, origem, fluxo de estudos, identidade) | 30 aprovados |
| Pytest completo backend em PostgreSQL descartável | 301 aprovados + 200 subtestes |
| Migrações banco novo e repetição | 0014, idempotente; seis tabelas verificadas com FORCE RLS |
| TypeScript + build Vite | Aprovado |
| Playwright Chrome no operacional | 1 jornada abrangente aprovada; 12 módulos acessíveis, sem troca de organização |
| Git diff --check | Aprovado |
| Integridade V4 | 8/8 hashes idênticos ao manifesto original |
| Identidade operacional | 1 organização, 1 operador, 1 vínculo; nenhum dado sintético em fatos/itens/cenários/documentos |

Comandos efetivamente executados, com configurações privadas referenciadas por ambiente (valores omitidos):

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/test_catalogue_source_binding.py backend/tests/test_catalogue_public_snapshot.py backend/tests/test_director_workflow.py backend/tests/test_observed_identity.py -q --tb=short
.venv/Scripts/python.exe .runtime/catalogo-historico-real/migrar-qa.py --evidence-dir .runtime/catalogo-historico-real
.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short --junitxml=.runtime/catalogo-historico-real/python.xml
# frontend/, IRPS_BASE_URL=http://127.0.0.1:5296 e IRPS_CATALOGUE_REAL=1
npx.cmd playwright test qa/catalogue-history-real.spec.ts
npm.cmd run build
# raiz
.venv/Scripts/python.exe .runtime/catalogo-historico-real/verificar.py
git diff --check
```

As primeiras execuções do novo teste de navegador identificaram expectativas incorretas do próprio teste: decimal serializado como texto, fase padrão homologado e seletor que encontrava texto dentro de detalhes fechados. Foram corrigidas as expectativas/esperas de requisições sem reduzir verificações de negócio. Um erro intermediário de sintaxe durante otimização SQL foi corrigido antes da execução final. Não houve alteração de produção para satisfazer fixture. O log consolidado contém a execução final; os registros intermediários continuam na pasta privada de execução.

Avisos restantes: depreciação Starlette/httpx, chave curta intencional no teste de JWT inválido e diretiva use client ignorada em dependência do build. Não impediram a execução; nenhum deles corresponde a chave operacional exposta. Não houve homologação de produção ou avaliação pixel-perfect nesta rodada.

## Arquivos e contratos

Novos: scripts/baixar_catalogos_oficiais.py; scripts/coletar_piloto_catalogo_historico.py; backend/app/catalogue_evidence.py; backend/tests/test_catalogue_public_snapshot.py; backend/tests/test_catalogue_source_binding.py; frontend/qa/catalogue-history-real.spec.ts.

Alterados nesta rodada: scripts/importar_catalogo_nacional.py; backend/app/national_catalogue.py; backend/app/history.py; backend/app/director.py; backend/app/director_routes.py; frontend/src/connected/Director.tsx; Catalogue.tsx; Opportunities.tsx. Os demais arquivos do diff pertencem ao trabalho local anterior e foram preservados.

- Importador: manifesto/backup e alvo local explícitos; conferência de hash e contagem.
- GET national-catalogue: campos aditivos de paginação, origem e totais.
- GET national-catalogue/{snapshot}/{code}/candidates: candidatos com provas e limites.
- POST national-catalogue/links: validation_mode e source_fact_id aditivos; modo humano anterior preservado.
- GET links: modo de validação e unidade original aditivos.
- GET history-collections/{id}: execução comprovada do plano, sem completude municipal presumida.

DIFF_LOCAL.patch contém o código acumulado desde HEAD, incluindo arquivos novos de código e o piloto anterior, sem repetir todos os documentos. DIFF_INCREMENTO_SOBRE_BACKUP.patch compara arquivos que tiveram cópia inicial nesta rodada. O segundo não é um patch completo independente. GIT_STATUS_FINAL.txt registra também os arquivos novos não versionados. Nenhuma alteração foi adicionada ao índice.

## Pendências e próximos limites

1. Ampliar períodos e modalidades em novos lotes controlados, não considerar duas semanas como todo 2025–2026.
2. Revisar associações nacionais sem declaração explícita, especialmente NOBREAK, com evidência de especificação/unidade/embalagem. Não há autorização implícita para aprovar equivalências ambíguas.
3. Contratos sem itens documentados não geram quantidades/preços unitários presumidos; índice de atas não substitui conteúdo integral.
4. Pagamento, entrega, consumo, estoque, anuência municipal, necessidade futura e manifestação formal não foram comprovados pelo piloto. Não foram fabricados.
5. Migrações novas não foram necessárias. Autenticação/RLS, planejamento e regressões existentes passaram na suíte; jornada institucional com documentos reais/manifestação não foi homologada novamente nesta rodada.
6. Não foi feita varredura nacional, integração paga, publicação oficial, auditoria de produção ou promessa de SLA. O operador único deve manter os dados administrativos e a revisão técnica.

## Evidências e segurança

Veja GALERIA.html para capturas separadas, TESTES.log/XML, VINCULOS_REVISAO.csv, planilha de cobertura e JSONs de provas. O ZIP contém somente relatórios, código em diff e evidências públicas/sanitizadas. Não inclui bancos, backups, senhas, sessões, arquivos de configuração privada, dependências, catálogos brutos volumosos ou documentos institucionais. A busca por valores privados conhecidos não encontrou ocorrência nos arquivos examinados; não se promete detecção absoluta de segredos desconhecidos.
