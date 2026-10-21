# Validação executada

## Backend e banco

- `IRPS_LOCAL_CONFIG=.runtime/config-increment-test.json .venv/Scripts/python.exe -m pytest backend/tests -q --junitxml=.runtime/pixel-perfect/python.xml`: **185 passed, 200 subtests passed**, 2 avisos. Execução completa nesta rodada, preservada em evidencias/python.*.
- Avisos: depreciação do TestClient/httpx e chave curta usada deliberadamente em teste negativo de JWT. Não são credenciais produtivas.
- Migrações: `scripts/validar_migracoes_diretriz.py --evidence-dir .runtime/pixel-perfect`: banco novo local; head 0012; upgrade repetido idempotente; seis tabelas com RLS forçada. Sem downgrade e sem banco real.
- Oito hashes V4 inalterados em integridade-v4.json. Não houve nova implementação matemática no frontend.

## Frontend e navegador

- Build TypeScript/Vite executado: consulte evidencias/build-entrega.txt. O resultado final do navegador está em evidencias/playwright-confirmacao.json e .txt quando concluído.
- `approved-workflow.spec`: seleção, filtros municipais, janelas, progresso, CSV, meta, V4, minuta, zoom, DOCX/PDF, upload, revisão, confirmação, invalidade da minuta após mudanças, reconfirmação, XLSX/PDF/dossiê.
- `pixel-refinement.spec`: sete referências, caixas de ±4 px, desktop exato e 320/390/768/1024, axe WCAG A/AA, overflow e erros JS.
- Demais testes existentes: catálogo, 20+ municípios, falha parcial da cobertura, oportunidades, isolamento comercial, cenários de 118 municípios/100 itens, exportações, teclado, recuperação e rotas.
- As execuções intermediárias falharam e foram preservadas. Houve contraste insuficiente no rodapé, região rolável sem foco, busca em detalhes fechados e editor que fechava após upload. As correções correspondentes não foram substituídas por supressão dos testes.
- Uma execução intermediária falhou em Oportunidades durante atualização do frontend; resultado da confirmação estabilizada deve prevalecer somente se executada e aprovada. Não se altera a classificação da execução anterior.

## Documentos

- Exports DOCX e PDF retornaram HTTP 201 e download HTTP 200. Consolidação PDF também exportada.
- DOCX convertido pelo LibreOffice e rasterizado pelo renderer de documentos; PDF e consolidação rasterizados pelo Poppler. Todas as páginas inspecionadas visualmente, sem corte de tabelas na amostra.
- Primeira tentativa de renderização falhou porque LibreOffice não estava no PATH; segunda passou com o executável local já instalado. Logs preservados no runtime.
- Diferença conhecida: PDF do exportador atual e DOCX não possuem acabamento idêntico. Não foi aprovado como documento institucional final.

## Avaliação visual

32 caixas principais com medição no JSON consolidado. Essa verificação não cobre todos os controles internos. O julgamento integral está em RELATORIO_DIVERGENCIAS.md: não há aprovação pixel-perfect sem os controles e acabamentos ausentes. Não se converte erro RGB em porcentagem de fidelidade.

Tela cheia está implementada, porém sem teste automatizado de acionamento nesta rodada. Não declarar esse controle como teste aprovado. A fixture visual com oito cidades é sintética, isolada e sem gravação oficial.

## Confirmação final executada

- Playwright: **32 passed**, 0 falhos, 0 ignorados, 0 testes flaky, em 3,8 minutos, após estabilização do código. A suíte contém sete testes de caixas/axe/overflow em desktop e 320/390/768/1024.
- Python: **185 passed + 200 subtests passed**, dois avisos documentados.
- Build: **aprovado**, TypeScript e Vite.
- Migrações: **aprovadas** em novo PostgreSQL local descartável, head 0012 e reaplicação idempotente.
- `git diff --check`: saída sem erros; somente avisos do Git sobre normalização CRLF/LF.
- V4: oito arquivos com hashes preservados. Auditoria de padrões: nenhuma credencial encontrada no escopo verificado.

Isso aprova as verificações funcionais e as caixas medidas, não certifica fidelidade visual integral. Nenhum commit, push, merge, PR ou deploy.
