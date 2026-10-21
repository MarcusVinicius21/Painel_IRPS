# Relatório técnico — rodada de refinamento visual

Estado inicial e final: branch `feat/cobertura-historica-catalogo-inteligente`, HEAD `e65375414792d4baef6ec1eaa6d7384c398448ca`. Nenhum commit, push, merge, PR ou deploy. Não foi encontrado AGENTS.md aplicável no repositório; ocorrências em dependências não governam o código do IRPS.

O estado inicial já continha alterações de catálogo, cobertura, diretoria, estudos, minutas, manifestações e consolidação. Não se atribuem essas funcionalidades inteiramente a esta rodada. A cópia física inicial e os hashes estão em `.runtime/pixel-perfect/baseline`; os oito módulos V4 foram comparados e permanecem iguais.

## Alterações desta rodada

- CSS compartilhado: shell claro, cabeçalho administrativo, sidebar, navegação, tipografia, cartões, grids, tabelas e breakpoints.
- Director: catálogo/ficha/resumo simultâneos; histórico na mesma página; abas e matriz compartilhada; modos A/B no topo; parâmetros, resumo e CTA do planejamento; modelos documentais como ações reais; aviso sintético compacto e progresso preservado.
- Executive: composição em três regiões superiores, filtros laterais, matriz e três regiões analíticas; visão com estudo selecionado em `#/inicio?estudo=...`, sem retirar o dashboard geral. Fase e contexto do estudo permanecem explícitos.
- MunicipalMatrix: separa histórico, V4, sugestão e confirmação. Não soma fases ou unidades. Indicadores ausentes usam travessão com explicação. CSV inclui classificação, municípios, fase, período, unidade e fontes; protege células contra fórmulas.
- DraftPreview: folha A4 mantida sem minuta, zoom funcional e tela cheia; prévia e downloads continuam vinculados à versão validada no servidor.
- IRPRegister: banner antes dos totais, cartões conforme situações reais, detalhe municipal antes da edição e editor controlado que não fecha após upload; exportações existentes preservadas.
- Ilustração original em SVG identificada como categoria, sem usar fotografia como prova de especificação.
- QA: comparação exata 1536×1024 / 1672×941, DPR 1; capturas real/parcial e sintética isolada; caixas DOM; ±4 px para as 32 caixas inventariadas; axe e overflow em 320/390/768/1024.

Não houve alteração de contrato HTTP, fórmula V4, RLS ou schema nesta rodada. Migrações existentes foram verificadas em novo banco local descartável e reaplicadas sem mudança. Backend e autenticação existentes foram reutilizados.

## Preservação e segurança

Auditoria por padrões em arquivos alterados e novos não ignorados: nenhuma ocorrência de credencial nos padrões verificados. Não é prova absoluta de inexistência de segredo. Configurações locais, bancos, cookies, tokens, sessões, uploads de usuários e dependências ficam fora do pacote. Evidências usam contas locais de QA; documentos exportados são explicitamente fictícios.

## Reprodução

A aplicação atual permanece em `http://127.0.0.1:5248/`, API em `http://127.0.0.1:5247/`. Use “Equipe de compras A”, conta fictícia de QA. O banco de testes é separado da aplicação; não use credenciais de produção.

- Build: `npm --prefix frontend run build`.
- Python: configure IRPS_LOCAL_CONFIG para o JSON local do banco isolado; execute `.venv/Scripts/python.exe -m pytest backend/tests -q`.
- Navegador, a partir de frontend: IRPS_FRONTEND_PORT=5248 e `npx playwright test`.
- Capturas, na raiz: `node scripts/capturar_refinamento_visual.cjs`. Cria um estudo interno de QA e intercepta respostas sintéticas somente no navegador, sem chamadas externas. Exige dados locais de catálogo e o estudo demonstrativo de referência, descritos em evidencias/estados.json.
- Comparações: `.venv/Scripts/python.exe scripts/relatorio_refinamento_visual.py`. Exige as referências fornecidas e capturas locais; não executa importação de código de ZIP.

A comparação sintética é exclusiva do teste; não há botão produtivo que troque dados reais por números demonstrativos. Estudos internos não recebem confirmações municipais inventadas. O ambiente continua local e não pronto para produção.

## Confirmação final executada

- Playwright: **32 passed**, 0 falhos, 0 ignorados, 0 testes flaky, em 3,8 minutos, após estabilização do código. A suíte contém sete testes de caixas/axe/overflow em desktop e 320/390/768/1024.
- Python: **185 passed + 200 subtests passed**, dois avisos documentados.
- Build: **aprovado**, TypeScript e Vite.
- Migrações: **aprovadas** em novo PostgreSQL local descartável, head 0012 e reaplicação idempotente.
- `git diff --check`: saída sem erros; somente avisos do Git sobre normalização CRLF/LF.
- V4: oito arquivos com hashes preservados. Auditoria de padrões: nenhuma credencial encontrada no escopo verificado.

Isso aprova as verificações funcionais e as caixas medidas, não certifica fidelidade visual integral. Nenhum commit, push, merge, PR ou deploy.
