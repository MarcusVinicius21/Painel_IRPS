> Registro da rodada local original. O envio inicial ao GitHub foi autorizado posteriormente. Consulte README.md para os caminhos atuais.

# Implementação local sobre o Observatório

P0: FastAPI, PostgreSQL isolado, migrações, JWT/JWKS e autorização por organização antes dos dados. P1: núcleo V4 idêntico, cenários versionados A/B, documentos revisáveis, cotações privadas, relatórios e assistente offline com ferramentas estritas. P2: consultas públicas pequenas PNCP/IBGE, persistindo fontes e cobertura separadas das amostras.

Frontend: preservar shell, componentes, Manrope, cores e navegação Observatório. Usar APIs nas telas conectadas; marcar amostras e áreas não conectadas. Contas locais são sintéticas com autenticação verificável por emissor de teste, sem alegar login produtivo. Provedores pagos permanecem bloqueados.

Executar migrações, testes negativos, regressões V4, contratos de fontes, exportações reabertas e Playwright em cinco larguras. Originais, Radar e skills são somente leitura. Sem commit, push, deploy ou instalação de serviço global.

## Execução

P0/P1/P2 locais implementados e testados. Entrega em docs/implementacao. O fluxo Observatório e o V4 foram preservados; provedores pagos e produção seguem fora desta rodada.
