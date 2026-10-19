> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Esforço observado nas operações

Medição Playwright local. C = eventos de clique DOM; F = controles alterados; N = mudanças de rota; t = segundos observados. Não é benchmark humano.

| Jornada | C | F | N | t (s) | Indicador IF |
|---|---:|---:|---:|---:|---:|
| Procurar comprador em exemplos fictícios | 1 | 2 | 1 | 1.199 | 8.04 |
| Comparar o recorte de três cidades | 1 | 1 | 0 | 0.160 | 3.01 |
| Criar e calcular 118 × 100 fictício | 3 | 3 | 0 | 8.310 | 9.28 |
| Calcular lucro da hipótese privada | 1 | 0 | 0 | 0.192 | 1.01 |

**Definição interna:** IF = C + 2F + 3N + min(t/30, 5). Menor é melhor apenas sob a mesma tarefa, ponto de partida, dados e ambiente. É uma proposta operacional, sem validação estatística.

Os eventos de `selectOption` alteram controles sem simular cada clique físico de uma lista. Portanto C não é contagem universal de gestos humanos. F registra controles distintos por rótulo, não teclas nem cada célula de uma edição em lote.

A busca inclui seleção de dados fictícios; a comparação parte de três cidades previamente indicadas e preserva resultados vazios. O cenário grande usa preenchimento artificial explícito. Isso não prova que informações reais de 11.800 linhas foram encontradas automaticamente.

O fluxo regular de calcular um cenário já preenchido ou uma simulação comercial usa uma ação principal. Criar o exemplo e calcular exige três botões e três controles alterados. Não declaramos atingida a meta de 1–2 cliques para todas as operações.

A tabela de resultados usa páginas do servidor de 20 registros, sem outra paginação intermediária nessa página. Seleção de municípios e itens permanece separada do filtro visível.

Não houve entrevista ou estudo com pessoas nesta rodada. Tempos são uma amostra automatizada em computador compartilhando servidor, banco e navegador. Não são SLA.
