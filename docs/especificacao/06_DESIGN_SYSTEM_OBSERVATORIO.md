# Observatório - sistema visual final para a demonstração

## Direção preservada

Escolha do usuário: Observatório, painel analítico para tomada de decisão. Manter a identidade do Gate C e melhorias do D. EVA orienta consistência e profundidade documental, sem copiar marca, roxo, fluxos de proteção ou estatísticas da referência. O estudo integral anterior dos PDFs 203/1/6 páginas foi reutilizado; os documentos anteriores permanecem íntegros.

Manus governa contexto → decisão → evidência → ação → feedback. Humanização IRPS governa toda mensagem visível. Frontend Design orienta composição intencional e densidade; Web Design Guidelines e React Best Practices orientam semântica, estados e custo de renderização. Regras privadas não foram modificadas.

## Tokens concretos

| Token | Valor | Uso |
|---|---|---|
| Estrutura/texto | #102C37 | Navegação, títulos, números |
| Ação | #006772 | Ação principal, foco de tarefa, barras comparáveis |
| Secundário | #52646D | Ajuda e unidade, com contraste verificado no contexto |
| Fundo | #F2F5F7 | Área de trabalho |
| Papel | #FFFFFF | Leitura, tabelas e formulários |
| Apoio | #E6F2F3 | Contexto e estado informativo |
| Borda | #D7E0E5; controles #71838D | Separação de leitura; limites funcionais visíveis |
| Atenção | #805000 sobre #FFF0D5 | Pendência, sempre com texto |
| Foco | #A35D00 | 3 px, afastamento de 4 px |

Manrope variável local, 200-800; licença preservada em prototipo/public/fontes. Fallback Arial/sans-serif. Números tabulares e Intl pt-BR. Título desktop 31 px, mobile 26/24; início tem composição editorial 30–38 px. Corpo 14/13; conteúdo de formulário 12–13; metadados 9–11 são secundários, nunca a única explicação da pendência. Se o usuário precisar ampliar, zoom não é bloqueado. Não usar cor como único estado.

Espaçamento 4/8/12/16/20/24/32/40. Raio 5–8; diálogo 10. Sombra apenas em camada contextual; sem cards repetidos, gradiente decorativo ou gráficos sem tarefa. Bordas separam registros; informação financeira usa alinhamento/tabularidade.

## Arquitetura visual

```
Desktop: [trilho] [contexto e espaço                                 ]
                 [título útil                       ação principal]
                 [busca / resumo do cenário / recorte              ]
                 [tabela ou tarefa              ][evidência/ajuda  ]
Mobile: [contexto / espaço / mais]
        [título e propósito]
        [resultado ou busca principal]
        [registros: valor + unidade + estado + ação]
        [Início | Pesquisar | Licitação | Negócio | Mais]
```

A marca não ocupa uma tela de apresentação. A busca recebe a atenção principal; o planejamento é uma tarefa contínua. Comparação por cidade/item não mistura unidades. Mobile usa lista de atributos, não cem colunas comprimidas. Desktop tem ordenação, paginação, filtros e fixação no quantitativo. Tabelas longas renderizam só a página, sem limitar o agregado.

## Componentes e comportamento

| Componente | Responsabilidade e estados |
|---|---|
| Shell | Contexto, espaço simulado, trilho e navegação mobile; ação de pular ao conteúdo |
| Page | Um h1, propósito, recorte e ação principal; foco no título ao mudar de superfície |
| Panel | Agrupa uma decisão ou conjunto coerente; sem KPI decorativo |
| Field / NumberField | Label associado, unidade, validação, decimal brasileiro e estado ausente |
| DataTable | Semântica desktop e registros mobile; ordenação anunciada, ID estável, paginação e foco |
| CityPicker | Visíveis e selecionados separados, grupo 118, filtro, cancelar/aplicar, teclado |
| Summary | Subtotal/total, linhas calculáveis, faltas, quantidade de itens/cidades e método |
| Notice / Badge | Fato, consequência e próximo passo; ausência/sigilo não viram erro inventado |
| Dialog | Nativo, nomeado, contenção de foco, Escape/cancelar e retorno ao disparador |
| Bars | Comparação de mesma unidade/fase com valores escritos e tabela equivalente; limite visual declarado |
| Export | Mesmo snapshot/seleção; nomes de arquivo com versão e marca de demonstração |

Hover não desloca conteúdo. Ícones Lucide têm rótulo/nome acessível e os decorativos são ocultos da leitura assistiva. Redução de movimento respeitada. Não há autoplay decorativo.

## Linguagem e credibilidade

Usar “Pesquisar compras”, “Conferir parâmetros”, “Preço não informado”, “Falta confirmar o estoque”, “Subtotal parcial” e “Revisão do exemplo”. Evitar termos internos de engenharia na interface comum. Não dizer “tudo pronto” sem dados/competência; calculado não é aprovado. Custos privados não são preço público. A faixa e os relatórios identificam números sintéticos. As 118 identidades reais não transformam esses números em fatos governamentais.

## Critério visual de fechamento

Revisar todas as superfícies em desktop/mobile e estados importantes. Conferir hierarquia, leitura de unidade/fase/preço, campos contidos, foco, tamanho de toque e tabelas financeiras. Capturas do navegador e análise axe apoiam a revisão; não certificam WCAG nem percepção humana. Galeria, resultados e limitações ficam no índice. A avaliação de acabamento pelo usuário é posterior à entrega completa, sem reiniciar a escolha da direção.
