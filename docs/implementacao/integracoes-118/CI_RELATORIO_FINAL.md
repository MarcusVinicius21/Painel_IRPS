# IRPS — relatório executivo CI01–CI09

**Resultado: entrega operacional parcial.** Não há comprovação de doze meses completos de compras dos 118 municípios. Aplicação local: http://127.0.0.1:5298/#/portfolio. Login único preservado; nenhum push, PR, merge ou deploy.

## Números comprovados

| Indicador | Resultado |
|---|---:|
| Alvos municipais validados no IBGE e ativados | 118 |
| Filiações formalmente confirmadas nesta rodada | 0 |
| Grupos prioritários | 20 |
| Códigos distintos selecionados | 7.917 |
| Selecionados com preço nacional | 2.219 — 28,03% |
| Selecionados com vínculo municipal revisado confirmado | 0 |
| Selecionados sem nenhum desses históricos identificado | 5.698 |
| Municípios com registros candidatos relacionados ao portfólio | 3: Água Boa, Ipatinga e Timóteo |
| Municípios com páginas oficiais consultadas no recorte | 22; não equivale a cobertura completa |
| Catálogo preservado | 348.679 códigos: 345.575 CATMAT + 3.104 CATSER |
| Preços nacionais preservados | 2.078.067 registros físicos; 24 snapshots / 12 meses |
| Códigos do catálogo validado com preço nacional | 127.779 — 36,65% do catálogo |

Todos os códigos do catálogo validado continuam pesquisáveis; 36,65% mede presença de preço nacional, **não cobertura de compras municipais**. Os candidatos por descrição não são vínculos confirmados. O universo dos arquivos de preços contém ainda nove códigos não encontrados nesse snapshot do catálogo, excluídos desse percentual. Estoque: **ESTOQUE NÃO DISPONÍVEL**.

## Fontes realmente utilizadas

| Integração | Instalação / teste / uso real | Novos dados e limites |
|---|---|---|
| PNCP oficial | Adaptador existente reutilizado; coleta real e agenda ativa | 28 identidades de publicações e 66 de itens novas, sem identidades repetidas. Destas, 24 publicações e 65 itens são de órgãos municipais no período. Não somar como compras independentes. |
| Compras.gov.br | Preços oficiais locais consultados nos testes | Nenhuma reimportação; base anterior preservada. |
| IBGE oficial | Consultas reais de MG/RJ, validação dos 118 | 2 documentos novos; identificação territorial, não compras. |
| CGU + MCP Portal da Transparência | Adaptador Python e ferramenta CEIS executados com chave protegida; HTTP 200 | 1 documento de consulta; zero registros de sanção retornados na página. Não atesta regularidade nem compras. MCP somente POC: 3 alertas altos e 2 moderados em dependências; produção bloqueada. |
| CATMAT.com.br | Busca, item e 74 categorias retornados; cliente com hash/data/cache | Complemento secundário, sem importação massiva e sem novos fatos municipais. |
| Max-Martins/pncp-consulta | Venv isolado, 12 testes upstream e consulta oficial real aprovados | Cliente de comparação; não criado coletor concorrente ou duplicado o registro oficial. |
| Licitei | POC AGPL isolada; PGlite Windows corrigido; amostra oficial persistida após dois reinícios | Busca local continua vazia. Sem incorporação ao produto; busca e conformidade AGPL pendentes. Nenhum novo fato municipal por esse caminho. |
| thiagosy/PNCP | Não incorporado; API PNCP oficial usada como alternativa | Licença não identificada. |
| MCP Brasil / Licinexus / Querido Diário | Não instalados nesta rodada | Nenhuma capacidade adicional única validada; não apresentados como fontes integradas. |

Delta comprovado por comparação exata com o backup CI01 restaurado, por provedor/identidade/revisão; corte **24/10/2026 03:24:05 BRT**. Os indicadores da planilha têm corte próprio registrado. A agenda pode acrescentar páginas posteriormente. Não foram acrescentados resultados homologados, contratos, atas ou preços nacionais nesta rodada. Nenhuma fonte secundária foi promovida a registro oficial.

## Automação e intervenção

**Automático:** worker do backend com cursor persistente, lock, tentativas limitadas e checkpoints; rotação dos 118 alvos e 12 meses fechados mais o atual; publicações e descoberta limitada de itens/resultados. A execução real avançou após reinício do backend. Requer servidor ligado; não foi instalado serviço Windows ou feito deploy. O portfólio mostra snapshot, última/próxima execução, fila e pedido manual limitado.

**Manual ou pendente:** arquivos CATMAT/CATSER somente por importação explícita sábado 08h–11h59, com checksum e prévia. Snapshots preservados; rollback da seleção ativa ainda pendente. Atualização automática adicional de arquivos de preços, contratos/atas/retificações e conectores municipais incompleta. Revisão técnica dos códigos, oferta comercial, filiação, documentos municipais e decisão de implantação continuam humanos. TCE-MG sem recurso validado; Ipatinga devolveu exportação fora do período; Timóteo retornou acesso negado nos testes anteriores preservados.

## Testes, segurança e skills

- Python: **573 aprovados + 200 subtestes**; após ajustes aditivos finais, **11 testes direcionados aprovados**. Mutação do cursor detectada pela regressão; código restaurado. Nenhuma asserção removida.
- Migrações: upgrade fresco até **0018**, segundo upgrade idempotente e RLS em banco descartável aprovados. Build React aprovado. Playwright: **4 aprovados**, mais **1 revalidação** após o contador de fila, desktop/mobile, sem capturas.
- Chave CGU protegida com DPAPI, fora do Git e do frontend. Varredura do segredo nos arquivos versionáveis e XLSX sem achados. Oito módulos V4, sete referências e doze arquivos de skills privadas intactos; diff-check aprovado. Dependências MCP com alertas não foram declaradas seguras para produção.
- Acionadas: ECC (segurança/TDD/verificação), Agent Skills (TDD, revisão e contratos), Manus, Humanização e Playwright; Spreadsheets aplicada à planilha. **Taste apenas disponível**, sem rodada de design; nenhuma alegação pixel-perfect.

## Checkpoints locais

CI01/02/03 aprovados; CI04/05/06/07 parciais pelos limites acima; CI08 aprovado na apresentação e testes; CI09 parcial no aceite integral das integrações. Não reabrir a fila antiga M/D/X nem refazer FCP.

| Etapa | Commit local |
|---|---|
| CI01 | 2396f85f8215db270ad3f738f6bfd358463e2e97 |
| CI02 | 5c0a41e037b873cd42c22479673d67586fa6a584 |
| CI03 | 53845149f7cd5f3f959e1e43080b882c940cc393 |
| CI04 | cb9eb471d964f0e8ca6f285dd4f01f9b32dd8c8e |
| CI05 | e97fe9f622e02bf27d8d0b01a437d06aa15ec40d |
| CI06 | 4dcd2a56f8d320d24c97749b436012dc0a565ad7 |
| CI07 | 20d05a9372b3f6fa27132a91d6c2b3ab14f14b76 |
| CI08 | c5bd42cea7acd0d21619df19a8b5a13279e4afbc |
| CI09 | Commit que contém este relatório; SHA final registrado na cópia de entrega. |
