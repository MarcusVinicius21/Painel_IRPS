# Comparação visual por referência

As sete imagens foram examinadas individualmente. O resultado busca sua composição institucional e suas interações legítimas, com diferenças descritas abaixo. Não foi calculada similaridade artificial de pixels.

Os PNGs originais foram preservados byte a byte; o manifesto de origem e seus hashes estão em `referencias/`. As capturas são separadas por tela e resolução.

## 00 Visão geral e componentes compartilhados

A composição de três áreas de seleção, item e resumo foi aplicada junto à navegação lateral clara, ao cabeçalho e às etapas. A visão geral orienta o mesmo aplicativo e não é outra página com todas as funções. A busca e a análise têm subetapas próprias para evitar uma página única extensa. A arte mostra 342 municípios e quantitativos ilustrativos; a aplicação informa o universo e as lacunas reais.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/00_visao_geral_observatorio.png) · [Implementação desktop](telas/00-visao-geral-1440.png) · [Implementação mobile](telas/00-visao-geral-390.png) · [Desktop completo](telas/00-visao-geral-1440-completa.png) · [Mobile completo](telas/00-visao-geral-390-completa.png)

## 01 Dashboard executivo

Indicadores, busca e blocos de histórico, fontes, produtos e atividades consultam APIs independentes. A diretiva textual pede um dashboard executivo; por isso a organização não replica literalmente a arte, que concentra também a matriz histórica de um produto. As barras contam registros por fase, e não veículos ou consumo sem vínculo técnico. Nenhuma série dos PNGs foi copiada.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/01_dashboard_inteligencia.png) · [Implementação desktop](telas/01-dashboard-1440.png) · [Implementação mobile](telas/01-dashboard-390.png) · [Desktop completo](telas/01-dashboard-1440-completa.png) · [Mobile completo](telas/01-dashboard-390-completa.png)

## 02 Inteligência por produto

Selecionar item e analisar histórico preservam o mesmo contexto. Filtros à esquerda e matriz à direita em desktop; no mobile, controles e registros empilhados. Períodos, evidências e abas anual/preços/fontes são funcionais. Foto de automóvel foi substituída por ícone porque o catálogo não fornece imagem comprovada. Sem vínculo, os valores ficam indisponíveis em vez de repetir os números da arte.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/02_inteligencia_por_produto.png) · [Implementação desktop](telas/02-inteligencia-1440.png) · [Implementação mobile](telas/02-inteligencia-390.png) · [Desktop completo](telas/02-inteligencia-1440-completa.png) · [Mobile completo](telas/02-inteligencia-390-completa.png)

## 03 Planejamento municipal

Item, resumo, explicações dos modos A/B, matriz e painel de planejamento foram integrados. O V4 original abre com retorno ao estudo e restauração do cenário vinculado. Sugestão e confirmação ficam separadas. A captura principal registra a edição da meta fictícia de 200 unidades; a experiência salva usa o formulário de sugestões auditáveis. Não existe distribuição automática da meta ilustrativa.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/03_planejamento_municipal.png) · [Implementação desktop](telas/03-planejamento-1440.png) · [Implementação mobile](telas/03-planejamento-390.png) · [Desktop completo](telas/03-planejamento-1440-completa.png) · [Mobile completo](telas/03-planejamento-390-completa.png)

## 04 Preparação documental

Três colunas em desktop: formulário, documento e conferência. A prévia central contém as mesmas seções dos arquivos gerados. Em mobile, essas áreas ficam em sequência, com documento rolável e exportações reais. O seletor reutiliza os seis tipos existentes; não apresenta lotes ou documentos como gerados sem execução. Campos oficiais e revisão jurídica permanecem pendentes quando não fornecidos.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/04_preparacao_irp.png) · [Implementação desktop](telas/04-preparacao-1440.png) · [Implementação mobile](telas/04-preparacao-390.png) · [Desktop completo](telas/04-preparacao-1440-completa.png) · [Mobile completo](telas/04-preparacao-390-completa.png)

## 05 Manifestações municipais

Indicadores, busca, filtro de situação, tabela/cartões e detalhe municipal usam o registro real. Comprovante pode ser preservado e conferido sem sair do IRPS. A confirmação depende de prova e competência registradas. A arte possui pessoas e totais fictícios; a execução mostra operadores e demonstrações identificados. Não foram criadas contas para prefeituras ou envio de e-mail simulado.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/05_manifestacoes_municipais.png) · [Implementação desktop](telas/05-manifestacoes-1440.png) · [Implementação mobile](telas/05-manifestacoes-390.png) · [Desktop completo](telas/05-manifestacoes-1440-completa.png) · [Mobile completo](telas/05-manifestacoes-390-completa.png)

## 06 Consolidação

Quadro municipal, total conhecido, pendências e painel de exportação reproduzem a hierarquia da referência. O exemplo real de teste permanece em consolidação parcial: um município confirmado e outro pendente. Assim, o banner de sucesso oficial da arte foi substituído por aviso correto. Excel, PDF e dossiê são arquivos gerados, não botões cenográficos.

[Referência original](referencias/01_REFERENCIAS_VISUAIS/06_consolidacao_irp.png) · [Implementação desktop](telas/06-consolidacao-1440.png) · [Implementação mobile](telas/06-consolidacao-390.png) · [Desktop completo](telas/06-consolidacao-1440-completa.png) · [Mobile completo](telas/06-consolidacao-390-completa.png)

## Revisão de clareza e uso

A interface reutiliza Manrope local, tokens azuis, fundo claro, bordas discretas, hierarquia de títulos e estados textuais. Desktop mantém sidebar e painéis contextuais; mobile usa navegação inferior, etapas roláveis e cartões por registro. Tabelas largas permanecem em região de rolagem, sem comprimir unidades e identidades até perder legibilidade.

As telas foram verificadas com Playwright e Axe em 1440 e 390 px. A regressão também cobre 320, 768 e 1024 px. Os avisos distinguem falta de vínculo, dados insuficientes, hipótese, cálculo, sugestão e manifestação. Toda alegação de aprovação ficou subordinada ao contrato de evidências.

A construção aplica Manus (`governed-frontend-ui`), Humanização IRPS e Frontend Design. A revisão de acessibilidade consultou as [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md). Skills privadas não foram alteradas. Nenhuma imagem sintética nova foi necessária; a marca deriva do cabeçalho institucional fornecido, preservado no gerador.

As capturas “antes/capturado” registram as rotas disponíveis no início, algumas ainda em carregamento. As antigas etapas 3–6 compartilhavam uma única rota; essas imagens não comprovam que existiam telas separadas. As três capturas reais fornecidas no ZIP estão preservadas em `antes/fornecido/`.

A revisão visual humana comparou hierarquia, navegação, proporções, fontes, tabelas, cores, estados e responsividade. Não constitui aprovação do usuário nem atestado de reprodução integral de todos os detalhes ilustrativos.
