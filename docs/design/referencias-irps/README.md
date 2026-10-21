# IRPS — Referências visuais oficiais de conceito (7 telas)

Estas sete imagens são **referências de design aprovadas para refinamento**, não evidência de funcionalidades existentes, resultados reais, compras oficiais ou de aprovação legal. O sistema real deve manter dados verificáveis e estados de ausência de informação.

| Etapa | Referência | Viewport de origem | Diretriz |
|---|---|---|---|
| 00 | [Visão geral e jornada](00_visao_geral.png) | 1536×1024 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 01 | [Dashboard com produto selecionado](01_dashboard_produto.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 02 | [Inteligência por produto](02_inteligencia_por_produto.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 03 | [Planejamento municipal](03_planejamento_municipal.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 04 | [Preparação da IRP](04_preparacao_irp.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 05 | [Manifestações municipais](05_manifestacoes.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |
| 06 | [Consolidação da IRP](06_consolidacao.png) | 1672×941 | Reproduzir layout, componentes, tipografia e hierarquia sem inventar fatos públicos |

## Como usar no refinamento

1. Analise **cada PNG isoladamente** e compare com a rota/etapa real correspondente.
2. Faça capturas reais com viewport igual ao da referência, DPR 1, sem ajustar escala ou recortar a imagem.
3. Compare geometria, textos, sidebar, grids, tabelas, cards, campos, estados, densidade e comportamento.
4. Priorize funcionalidade real, acessibilidade e integridade. Dado desconhecido não se transforma em zero ou valor fictício.
5. Relatórios de QA ou imagens sintéticas devem ser identificados e mantidos separados dos dados oficiais.
6. Não use estas imagens como saída final: cada componente deve ser implementado no React do IRPS, com API, persistência e testes próprios.

## Público e confidencialidade

O repositório GitHub foi verificado como **público** em 21/10/2026. As artes originais conceituais são distintas das capturas do ambiente local e dos documentos internos do CONSORMULTI. Antes de subir qualquer captura adicional, confira se há nomes, CNPJs, documentos, sessões, identificadores sensíveis e dados reais.

O `manifest.json` registra hashes SHA-256 exatos dos originais. **Não otimizar, reencodar, redimensionar ou alterar estas sete referências no commit de publicação.**
