# Revisão local das telas aprovadas do IRPS

A implementação está no IRPS existente. Não há frontend paralelo. As seis etapas funcionais e a visão geral foram conectadas aos serviços persistidos, com dados oficiais e demonstrações separados.

- [Relatório técnico e limites](RELATORIO_TECNICO.md)
- [Relatório visual por referência](RELATORIO_VISUAL.md)
- [Galeria de referências, desktop e mobile](galeria.html)
- [Matriz de funcionalidades, APIs e evidências](MATRIZ_FUNCIONAL.md)
- [Contratos e execução local](CONTRATOS_E_EXECUCAO.md)
- [Testes e segurança](QA.md)
- [Fluxograma editável](FLUXO.mmd)
- [Arquivos alterados](ARQUIVOS_ALTERADOS.md)
- [Minuta demonstrativa DOCX](demonstracao/minuta-demonstrativa.docx), [PDF](demonstracao/minuta-demonstrativa.pdf)
- [Excel de consolidação](demonstracao/consolidacao-demonstrativa.xlsx), [PDF](demonstracao/consolidacao-demonstrativa.pdf), [dossiê](demonstracao/dossie-demonstrativo.zip)

## Abrir a aplicação

[Dashboard local](http://127.0.0.1:5248/#/inicio) · [Estudo demonstrativo de automóvel](http://127.0.0.1:5248/#/inteligencia?estudo=71314dc8-facb-40a1-a167-ae82e65aad66&etapa=planejamento) · [Consolidação demonstrativa](http://127.0.0.1:5248/#/inteligencia?estudo=71314dc8-facb-40a1-a167-ae82e65aad66&etapa=consolidacao).

Se solicitado, entre com o perfil fictício de teste “Equipe de compras A”. A demonstração tem meta preliminar de 200 unidades, 30 unidades registradas com prova fictícia em Ipatinga e Alfenas pendente. Não atribui necessidade V4 nem participação real a esses municípios. O total conhecido é parcial.

Jornada: dashboard → pesquisar automóvel → escolher código → histórico municipal → planejamento → preparar minuta → registrar e conferir documento → manifestação → consolidação. Salve progresso para retomar um rascunho ainda incompleto. A alteração de uma manifestação exige nova conferência das minutas anteriores.

## O que os percentuais significam

**Consulta ao catálogo: 100% dos 348.679 códigos dos arquivos fornecidos. Histórico oficial associado a esses códigos por vínculo técnico revisado: 0%.** Não confundir importação do catálogo com cobertura de compras. O banco possui fatos oficiais parciais em três municípios, ainda sem esses vínculos revisados.

As imagens conceituais são referências, não evidências de compras. Os PNGs em `telas/` são capturas da aplicação executada. As versões `-completa` mostram o restante da página e não representam telas adicionais.

**Alterações somente locais. Sem commit, push, merge, atualização de PR ou deploy.** Núcleo V4 e originais preservados. Este pacote complementa a base `e65375414792d4baef6ec1eaa6d7384c398448ca` e contém o overlay de código/diff; não é instalador autônomo com banco ou credenciais.

Os dois patches distinguem esta rodada do trabalho local anterior. Confira `BASES_DO_DIFF.json` para a normalização textual de finais de linha de um arquivo; os hashes físicos e os arquivos atuais completos foram preservados para revisão.
