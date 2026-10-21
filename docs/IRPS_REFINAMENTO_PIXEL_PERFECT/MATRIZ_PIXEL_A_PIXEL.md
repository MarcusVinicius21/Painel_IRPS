# Matriz visual 1:1 — regiões e controles

Inventário inicial e avaliação após o refinamento. Os grupos enumeram controles visíveis da arte; a medição ±4 px é específica das caixas principais listadas no JSON, não de cada controle interno. Estados abaixo não representam aprovação integral.

## Referência 00

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/Director.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/Director.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/Director.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/Director.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Busca, CATMAT/CATSER, categoria e situação | `.catalogue-search-panel` | `frontend/src/connected/Director.tsx` | /national-catalogue | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seleção ativa e ficha ilustrativa | `.selected-item` | `frontend/src/connected/Director.tsx` | /national-catalogue/{snapshot}/{code} | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo, mini indicadores e período | `.selection-overview>.panel:last-child` | `frontend/src/connected/Director.tsx` | vínculos e estudo | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Filtros territoriais, municípios, datas, modalidade, fase, fonte e comparabilidade | `.workflow-filter-panel` | `frontend/src/connected/Director.tsx` | /director/history | Parcial: controles disponíveis ligados; modalidade/fonte/região sem equivalência integral, conforme relatório |
| Abas temporal, preços e evidências | `.workflow-tabs` | `frontend/src/connected/Director.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Matriz municipal, seleção, registros, janelas, última data, preço e cobertura | `.municipal-history-panel` | `frontend/src/components/MunicipalMatrix.tsx` | /director/history | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ordenação, paginação, tamanho de página e exportação | `.pagination` | `frontend/src/connected/Director.tsx` | DataTable | Operacional nos contratos existentes; apresentação ainda diferente do raster |
| Três gráficos: quantidade, evolução e distribuição | `.historical-charts` | `frontend/src/connected/Director.tsx` | histórico comparável | Bloqueado por dados para séries; região preservada. Representação do raster não integral |
| Meta, municípios, referências de quantidade e CTA | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | progresso/planejamento | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Referência 01

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/Executive.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/Executive.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/Executive.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/Executive.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ficha do produto, ilustração, código e atributos | `.executive-top>.panel:first-child` | `frontend/src/connected/Executive.tsx` | catálogo | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Quatro indicadores do recorte | `.executive-metrics` | `frontend/src/connected/Executive.tsx` | /director/dashboard | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Insights e limitações | `.executive-top>.panel:last-child` | `frontend/src/connected/Executive.tsx` | evidência/revisão | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Filtros estreitos por situação, escopo e período | `.executive-filters` | `frontend/src/connected/Executive.tsx` | estado local | Parcial: controles disponíveis ligados; modalidade/fonte/região sem equivalência integral, conforme relatório |
| Matriz municipal histórica e abas | `.executive-evidence>.panel` | `frontend/src/connected/Executive.tsx` | /director/dashboard/history | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Barras, curva mensal e distribuição | `.executive-charts` | `frontend/src/connected/Executive.tsx` | /director/dashboard/history | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo fixo, planejamento e relatório | `.executive-bottom` | `frontend/src/connected/Executive.tsx` | navegação | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Estados independentes de fontes | `.executive-reference` | `frontend/src/connected/Executive.tsx` | três APIs independentes | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Referência 02

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/Director.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/Director.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/Director.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/Director.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Busca com abas, botão, categoria e situação | `.catalogue-search-panel` | `frontend/src/connected/Director.tsx` | /national-catalogue | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ficha ilustrada, código, ativo, unidade, classe e detalhes | `.selected-item` | `frontend/src/connected/Director.tsx` | catálogo | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo com quatro indicadores e período | `.selection-overview>.panel:last-child` | `frontend/src/connected/Director.tsx` | vínculos revisados | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Abrangência, segmentação, municípios, datas e modalidade | `.workflow-filter-panel` | `frontend/src/connected/Director.tsx` | /director/history | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Abas histórico, preços, documentos e similares | `.workflow-tabs` | `frontend/src/connected/Director.tsx` | estado local | Parcial: histórico/evidências preservados; ausência de vínculo não vira quantidade zero |
| Matriz histórica com cobertura e paginação | `.municipal-history-panel` | `frontend/src/components/MunicipalMatrix.tsx` | histórico | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Barra de seleção, seis etapas e avançar | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Referência 03

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/Director.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/Director.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/Director.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/Director.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ficha do item | `.method-options>.selected-item` | `frontend/src/connected/Director.tsx` | estudo | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Modo A com critérios e acesso ao V4 | `.method-options>.panel:nth-child(2)` | `frontend/src/connected/Director.tsx` | /quantidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Modo B com critérios e acesso ao V4 | `.method-options>.panel:nth-child(3)` | `frontend/src/connected/Director.tsx` | /distribuicao | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Meta, critérios e seleção municipal | `.planning-parameters` | `frontend/src/connected/Director.tsx` | estudo | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Informações importantes | `.planning-parameters>.notice` | `frontend/src/connected/Director.tsx` | regras | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Matriz com histórico, V4, insuficiência, sugestão, ajuste, subtotal e situação | `.municipal-history-panel` | `frontend/src/components/MunicipalMatrix.tsx` | histórico/calculations/register | Parcial: histórico/evidências preservados; ausência de vínculo não vira quantidade zero |
| Ajuste auditável e revisão | `.irp-register[data-view=suggestions]` | `frontend/src/connected/Director.tsx` | operations | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo, total e preparar IRP | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | estudo | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Referência 04

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/Director.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/Director.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/Director.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/Director.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Introdução e formulário de preparação | `.preparation-panel` | `frontend/src/connected/Director.tsx` | drafts | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Lista: formulário, procedimento, planilha, lotes e anexos | `.document-choices` | `frontend/src/connected/Director.tsx` | kind do gerador | Parcial: seis modelos reais; documento multiitem/lotes não implementado |
| Cenário selecionado com ficha | `.preparation-panel` | `frontend/src/connected/Director.tsx` | estudo persistido | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Prévia, modelo, páginas, zoom e tela cheia | `.document-preview-panel` | `frontend/src/components/DraftPreview.tsx` | /irp-drafts/{id}/preview | Parcial: zoom e tela cheia implementados; paginação no PDF, sem navegação falsa de páginas HTML |
| Folha A4 com marca, títulos, tabelas e valores | `.document-paper` | `frontend/src/components/DraftPreview.tsx` | mesmo conteúdo do exportador | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Checklist por objeto, unidades, municípios e pendências | `.review-checks` | `frontend/src/connected/Director.tsx` | validações | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo da IRP e versões | `.workflow-preparation-layout>.panel:last-child` | `frontend/src/connected/Director.tsx` | drafts | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ações de revisão, PDF, DOCX, voltar e prosseguir | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | exports/workflowURL | Operacional nos contratos existentes; apresentação ainda diferente do raster |

## Referência 05

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/IRPRegister.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/IRPRegister.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/IRPRegister.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/IRPRegister.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Cinco indicadores no PNG; quatro solicitados no texto | `.executive-metrics` | `frontend/src/connected/IRPRegister.tsx` | register | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Busca, status, região e mais filtros | `.register-filters` | `frontend/src/connected/IRPRegister.tsx` | filtro local | Parcial: controles disponíveis ligados; modalidade/fonte/região sem equivalência integral, conforme relatório |
| Tabela com seleção, município, sugerido, informado, estado, documento, responsável, data e nota | `.manifestation-layout>.panel` | `frontend/src/connected/IRPRegister.tsx` | register | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Paginações e legenda de estados | `.pagination` | `frontend/src/connected/IRPRegister.tsx` | DataTable | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Detalhes da manifestação e status | `.municipal-detail` | `frontend/src/connected/IRPRegister.tsx` | operations | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Abas detalhes, documentos e histórico | `.municipal-detail` | `frontend/src/connected/IRPRegister.tsx` | documents/history | Parcial: histórico/evidências preservados; ausência de vínculo não vira quantidade zero |
| Comprovantes e upload | `.municipal-detail details` | `frontend/src/connected/IRPRegister.tsx` | /documents | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Parecer, responsável, data e salvar | `.municipal-detail .field` | `frontend/src/connected/IRPRegister.tsx` | review/operations | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Resumo e consolidar válidas | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | consolidacao | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Referência 06

| Elemento do PNG | Região / seletor | Arquivo principal | Operação | Estado atual e correção restante |
|---|---|---|---|---|
| Marca institucional | `rail .brand` | `frontend/src/connected/IRPRegister.tsx` | /inicio | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Navegação principal e ativo | `.rail nav` | `frontend/src/App.tsx` | rotas existentes | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Organização e conta | `.topbar` | `frontend/src/App.tsx` | /auth/context | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Aviso de ambiente | `.demo-ribbon` | `frontend/src/App.tsx` | estado local | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Título e introdução | `.page-heading` | `frontend/src/connected/IRPRegister.tsx` | rota atual | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Seis etapas e estados | `.workflow-steps` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Ação de ajuda ou exploração | `.page-heading .actions` | `frontend/src/connected/IRPRegister.tsx` | /oportunidades | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Foco de teclado | `*:focus-visible` | `frontend/src/connected/IRPRegister.tsx` | local | Presente; verificação axe e teclado executada, sem alegar auditoria humana exaustiva |
| Rodapé de continuidade | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Cabeçalho de estado, ícone e resumo do processo | `.consolidation-banner` | `frontend/src/connected/IRPRegister.tsx` | register | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Cinco cartões: participantes, quantidade, valor, documentos e pendências | `.executive-metrics` | `frontend/src/connected/IRPRegister.tsx` | register | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Distribuição visual e quantitativos documentados | `.executive-metrics` | `frontend/src/connected/IRPRegister.tsx` | register | Bloqueado por dados para séries; região preservada. Representação do raster não integral |
| Tabela municipal, busca, confirmado, unidade, conferência, documento e ação | `.consolidation-layout>.panel` | `frontend/src/connected/IRPRegister.tsx` | register | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Pendências e próximos passos | `.next-steps` | `frontend/src/components/WorkflowUI.tsx` | revisão humana | Parcial: região presente; estilo e microgeometria interna não idênticos |
| Exportar XLSX, PDF e dossiê | `.export-actions` | `frontend/src/connected/IRPRegister.tsx` | consolidation/dossier | Operacional nos contratos existentes; apresentação ainda diferente do raster |
| Paginação e ações de retorno | `.workflow-footer` | `frontend/src/components/WorkflowUI.tsx` | workflowURL | Parcial: região presente; estilo e microgeometria interna não idênticos |

## Restrições de aprovação

Veja RELATORIO_DIVERGENCIAS.md. Os estados não usam “idêntico” sem medição de todos os elementos internos. Nenhuma tela foi certificada como reprodução integral.