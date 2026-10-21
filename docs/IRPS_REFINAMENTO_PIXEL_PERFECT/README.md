# IRPS — revisão visual local

Esta é a entrega incremental de refinamento das sete telas. O código foi alterado dentro do IRPS existente. Todos os arquivos anteriores foram preservados.

- [Galeria comparativa](GALERIA.html): sete originais, capturas reais/parciais, demonstração sintética, lado a lado, sobreposição e mapas de diferenças.
- [Relatório técnico](RELATORIO_TECNICO.md): implementação, preservação, segurança e execução.
- [Julgamento visual e divergências](RELATORIO_DIVERGENCIAS.md): limitações por tela, sem aprovação artificial.
- [Inventário 1:1](MATRIZ_PIXEL_A_PIXEL.md) e [matriz funcional](MATRIZ_FUNCIONAL.md).
- [Testes executados](QA.md), [caixas e métricas](medidas-consolidadas.json) e [integridade V4](integridade-v4.json).
- [Diff incremental](diff-refinamento.patch): relativo ao estado físico anterior desta rodada, que já continha trabalho local não commitado.
- [Arquivos de código alterados](arquivos-alterados.json).

Aplicação local: http://127.0.0.1:5248/. Nenhum commit, push, alteração de PR ou deploy.

A fidelidade integral ainda não está aprovada. Geometria principal e testes não substituem a revisão dos controles internos. Não se apresentam números ilustrativos como dados oficiais. O pacote de revisão não contém banco, dependências, .env real ou credenciais.

## Confirmação final executada

- Playwright: **32 passed**, 0 falhos, 0 ignorados, 0 testes flaky, em 3,8 minutos, após estabilização do código. A suíte contém sete testes de caixas/axe/overflow em desktop e 320/390/768/1024.
- Python: **185 passed + 200 subtests passed**, dois avisos documentados.
- Build: **aprovado**, TypeScript e Vite.
- Migrações: **aprovadas** em novo PostgreSQL local descartável, head 0012 e reaplicação idempotente.
- `git diff --check`: saída sem erros; somente avisos do Git sobre normalização CRLF/LF.
- V4: oito arquivos com hashes preservados. Auditoria de padrões: nenhuma credencial encontrada no escopo verificado.

Isso aprova as verificações funcionais e as caixas medidas, não certifica fidelidade visual integral. Nenhum commit, push, merge, PR ou deploy.
