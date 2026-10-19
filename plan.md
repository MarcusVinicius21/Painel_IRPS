> Registro da rodada local original. O envio inicial ao GitHub foi autorizado posteriormente. Consulte README.md para os caminhos atuais.

## Incremento autorizado: oportunidades CONSORMULTI

Branch `feat/oportunidades-consormulti`, originada no commit publicado. Preservar os oito módulos V4 e a composição Observatório. Acrescentar serviços `history` e `opportunities`, migração 0006, contratos fechados, área de oportunidades/detalhe/curadoria/coleta e testes. Dados oficiais e sintéticos continuam separados.

Fluxo: recorte histórico → páginas/checkpoints → fatos de uma fase → equivalência revisada → indicadores com cobertura → viabilidade humana → prioridade explicada → rascunho de licitação sem necessidade presumida. A interface reutiliza Manrope, paleta petróleo, tabelas desktop e registros mobile, com a ação principal junto ao contexto e evidências. Sem nova direção visual.

Validar retomada e limites de fontes, duplicação/retificação, filtros combinados, matemática dos indicadores, revisão e pesos, ausência de pontuação incompleta, organizações/atores, criação de cenários vazios e alertas comprovados. Executar regressão V4, integração e Chrome em desktop/mobile. Auditar antes de commits; publicar somente a branch e abrir PR, sem deploy.

# Implementação local sobre o Observatório

P0: FastAPI, PostgreSQL isolado, migrações, JWT/JWKS e autorização por organização antes dos dados. P1: núcleo V4 idêntico, cenários versionados A/B, documentos revisáveis, cotações privadas, relatórios e assistente offline com ferramentas estritas. P2: consultas públicas pequenas PNCP/IBGE, persistindo fontes e cobertura separadas das amostras.

Frontend: preservar shell, componentes, Manrope, cores e navegação Observatório. Usar APIs nas telas conectadas; marcar amostras e áreas não conectadas. Contas locais são sintéticas com autenticação verificável por emissor de teste, sem alegar login produtivo. Provedores pagos permanecem bloqueados.

Executar migrações, testes negativos, regressões V4, contratos de fontes, exportações reabertas e Playwright em cinco larguras. Originais, Radar e skills são somente leitura. Sem commit, push, deploy ou instalação de serviço global.

## Execução

P0/P1/P2 locais implementados e testados. Entrega em docs/implementacao. O fluxo Observatório e o V4 foram preservados; provedores pagos e produção seguem fora desta rodada.
