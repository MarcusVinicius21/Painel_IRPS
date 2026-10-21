> Registro da rodada local original. O envio inicial ao GitHub foi autorizado posteriormente. Consulte README.md para os caminhos atuais.

## Incremento autorizado: oportunidades CONSORMULTI

Branch `feat/oportunidades-consormulti`, originada no commit publicado. Preservar os oito módulos V4 e a composição Observatório. Acrescentar serviços `history` e `opportunities`, migração 0006, contratos fechados, área de oportunidades/detalhe/curadoria/coleta e testes. Dados oficiais e sintéticos continuam separados.

Fluxo: recorte histórico → páginas/checkpoints → fatos de uma fase → equivalência revisada → indicadores com cobertura → viabilidade humana → prioridade explicada → rascunho de licitação sem necessidade presumida. A interface reutiliza Manrope, paleta petróleo, tabelas desktop e registros mobile, com a ação principal junto ao contexto e evidências. Sem nova direção visual.

Validar retomada e limites de fontes, duplicação/retificação, filtros combinados, matemática dos indicadores, revisão e pesos, ausência de pontuação incompleta, organizações/atores, criação de cenários vazios e alertas comprovados. Executar regressão V4, integração e Chrome em desktop/mobile. Auditar antes de commits; publicar somente a branch e abrir PR, sem deploy.

## Incremento atual: cobertura histórica e catálogo inteligente

Base exata `9a7883c566d07b2b9c95bfd8952327d4dfe7ef8e`, branch `feat/cobertura-historica-catalogo-inteligente`. Ampliar somente rotas públicas documentadas; testar um piloto MG limitado antes de ampliar. Separar publicação, resultado, contrato, ata, PCA e preço de referência. Inventariar páginas por fonte/município/modalidade e fatos por órgão/CNPJ; só calcular percentual com denominador de consultas verificável. Normalizar preservando originais, revisar equivalência humana e reprocessar de forma imutável. Validar Python, migrações PostgreSQL, frontend, Playwright e auditoria antes do commit e do novo PR. Não fazer merge nem deploy.

# Implementação local sobre o Observatório

P0: FastAPI, PostgreSQL isolado, migrações, JWT/JWKS e autorização por organização antes dos dados. P1: núcleo V4 idêntico, cenários versionados A/B, documentos revisáveis, cotações privadas, relatórios e assistente offline com ferramentas estritas. P2: consultas públicas pequenas PNCP/IBGE, persistindo fontes e cobertura separadas das amostras.

Frontend: preservar shell, componentes, Manrope, cores e navegação Observatório. Usar APIs nas telas conectadas; marcar amostras e áreas não conectadas. Contas locais são sintéticas com autenticação verificável por emissor de teste, sem alegar login produtivo. Provedores pagos permanecem bloqueados.

Executar migrações, testes negativos, regressões V4, contratos de fontes, exportações reabertas e Playwright em cinco larguras. Originais, Radar e skills são somente leitura. Sem commit, push, deploy ou instalação de serviço global.

## Execução

P0/P1/P2 locais implementados e testados. Entrega em docs/implementacao. O fluxo Observatório e o V4 foram preservados; provedores pagos e produção seguem fora desta rodada.

## Diretriz Mestra V2 — pacote A local
Preservar o diff de estabilização anterior e os oito hashes V4. Importar snapshots CATMAT/CATSER com índices PostgreSQL e paginação. Uma tela no Observatório reúne código, recorte, histórico 1/3/6/12 meses, meta preliminar e criação de estudo/cenário. O estudo é imutável, mantém evidências e não fornece entradas V4 por inferência. Minutas derivadas usam campos estruturados, revisão de coerência, versões e exportação DOCX/PDF. Itens internos recebem escopo de organização para não vazar especificações entre contas. Modelos jurídicos permanecem pendentes de validação; nenhuma publicação oficial ou assinatura será simulada.
# Telas aprovadas — incremento local de 20/10/2026

Auditoria inicial: branch feat/cobertura-historica-catalogo-inteligente, HEAD e65375414792d4baef6ec1eaa6d7384c398448ca. Diff preexistente preservado; inventário de hashes em .runtime/sete-telas/estado-inicial.json. Sem AGENTS.md aplicável encontrado. Sete PNGs conceituais e três capturas anteriores examinados individualmente. Pacote anterior disponível, sem aplicação de patches.

Reutilizar catálogo paginado, vínculos revisados, histórico municipal, cenários V4, minutas, operações e documentos. Separar Director em seleção, histórico, planejamento, preparação, manifestações e consolidação, usando o estudo persistido como contexto. Dashboard consulta métricas oficiais separadas por fase. UI institucional clara, azul, sidebar clara, tabelas compactas e painel contextual como referências, sem copiar números fictícios ou aprovação jurídica.

Arquivos previstos: App, Director, IRPRegister, componentes de jornada, dashboard e CSS compartilhado; director_routes e serviços focados de dashboard/exportação. Não duplicar cálculo nem alterar núcleo V4. Reaproveitar schema; novas migrações somente se inevitáveis. Quantidade sugerida utiliza irp_operation e conferência vigente.

Validar PostgreSQL isolado, catálogo, histórico, cenários, V4, documentos, isolamento, exportações, build e Playwright em 1440/390. Capturar antes/depois por tela e documentar diferenças. Testes prévios não são aceitos como evidências atuais. Vínculos oficiais, séries comparáveis e revisão jurídica permanecem dependências reais, sem bloquear estados honestos ou o fluxo interno.

## Refinamento visual rigoroso — 21/10/2026
Preservar estado local e oito hashes. Comparar 00 em 1536×1024 e 01–06 em 1672×941. Shell e tokens compartilhados; três colunas de seleção, modos/decisão compactos, prévia A4 e estados municipais. Evidências em docs/IRPS_REFINAMENTO_PIXEL_PERFECT. Não alterar V4, fórmulas, produção ou remotos. APIs atuais, contratos e autenticação reutilizados. QA: banco isolado, suíte Python, build, Playwright, documento renderizado e geometrias por seletor. Dados sem vínculo exigem placeholders. Nenhuma alegação de fidelidade sem medição.
