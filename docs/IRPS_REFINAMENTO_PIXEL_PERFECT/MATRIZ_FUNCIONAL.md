# Matriz de controles e comportamento

| Print / elemento | Componente | Rota | Operação | Origem | Estado / exceção | Teste |
|---|---|---|---|---|---|---|
| Busca, tipo e filtros de catálogo | Director/catalogue-search-panel | /inteligencia | GET /national-catalogue | Snapshot importado | Operacional; filtro avançado em detalhes | director.spec + approved-workflow.spec |
| Ficha ilustrativa e descrição original | SelectedItem + VehicleIllustration | /inteligencia e /inicio?estudo | GET catálogo/estudo | Código e versão preservados | Operacional; ilustração diferente do raster | pixel-refinement.spec |
| Municípios, fase e período | Director/filter-panel | /inteligencia?etapa=historico | GET /director/history/{product} | Fatos elegíveis por produto revisado | Operacional; modalidade/fonte desabilitados com motivo | catalogue.spec + director.spec |
| Abas, janelas e evidências | MunicipalMatrix + HistoryDetails | /inteligencia | Histórico e links revisados | Recorte armazenado e fontes | Operacional; médias indisponíveis sem cobertura | approved-workflow.spec |
| Ordenação e paginação | DataTable | Jornada | Estado local; busca paginada no servidor | Oito linhas visíveis por página | Operacional; tamanho de página fixo | catalogue.spec + pixel-refinement.spec |
| Exportar tabela | MunicipalMatrix.exportTable | histórico | CSV local da resposta já autorizada | Mesmas linhas/escopo do histórico | Operacional; campos ausentes em branco; fórmula CSV protegida | approved-workflow.spec |
| Modos A/B e V4 | Director + WorkflowPlanning | /quantidades e /distribuicao | Cenários/cálculos existentes | Núcleo V4 preservado | Operacional sem recálculo no cliente | 185 Python + catalogue.spec |
| Meta, estudo e progresso | Director + WorkflowFooter | /planejamento | POST /director/studies e /progress | Hipóteses explícitas | Operacional; sem distribuição implícita | approved-workflow.spec + backend |
| Sugestão revisável | IRPRegister | planejamento | POST /operations | Operação versionada | Operacional no formulário; não inline | director.spec + backend |
| Modelos e prévia A4 | Director + DraftPreview | preparacao | POST drafts; GET preview | Estudo e versão | Operacional; lotes/multiitem não implementados | director.spec + backend |
| Zoom da prévia | DraftPreview | preparacao | Estado local de apresentação | Mesmo conteúdo da prévia | Operacional 75–150% | approved-workflow.spec |
| Tela cheia | DraftPreview | preparacao | requestFullscreen nativo | Mesmo conteúdo | Implementado; não testado automaticamente nesta rodada | Inspeção de código; teste de acionamento pendente |
| DOCX/PDF | DraftPreview | preparacao | POST exports | Versão conferida e não stale | Operacional; PDF e DOCX diferem em acabamento | Playwright + renderização Poppler/LibreOffice |
| Manifestação, anexo e conferência | IRPRegister | manifestacoes | documents/review/operations | Documentos locais preservados | Operacional; não há envio/login municipal | approved-workflow.spec + backend |
| Estados, ajuste e recusa | IRPRegister | manifestacoes | GET register | Somente registros válidos | Operacional; silêncio não é recusa | backend test_irp_register |
| Consolidação e exportações | IRPRegister | consolidacao | consolidation/{xlsx,pdf}; dossier | Confirmações vigentes | Operacional; parcial quando pendente | approved-workflow.spec + backend |
| Ajuda, notificações e conta | App + Director | /fontes, /alertas, /administracao | APIs existentes | Contexto autenticado | Operacional; troca de organização desabilitada | routes.spec + real.spec |
| Gráficos agregados por produto | HistoricalCharts | histórico/dashboard | Sem contrato agregado suficiente | Sem vínculo revisado | Geometria preservada; séries não preenchidas | pixel-refinement.spec; sem indicador inventado |