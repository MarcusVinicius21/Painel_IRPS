# T24 — Oportunidades

## Decisão que a tela apoia

Identificar quais itens merecem aprofundamento, com origem, situação e
cobertura claras. A tela não decide compra, fornecedor ou aprovação em nome do
usuário.

## Rotas e ações

| Rota | O que a pessoa vê | Ações disponíveis |
|---|---|---|
| `/#/oportunidades` | Recorte, cobertura e tabela de itens/equivalências | Filtrar, abrir análise, atualizar histórico |
| `/#/oportunidade?key=…` | Histórico mensal, preços, municípios, fontes e pendências | Registrar revisão, criar rascunho, acompanhar |
| `/#/coleta-oportunidades` | Recorte PNCP, limite, páginas e pontos de retomada | Preparar, coletar próxima página, pausar, retomar |
| `/#/alertas` | Acompanhamentos e mudanças já comprovadas | Verificar dados já coletados |

## Dados, estados e texto

O recorte inicial mostra fonte, situação e datas. O bloco avançado permite
municípios, grupo, órgão, categoria, item do catálogo, fornecedor, modalidade,
mês, ano, quantidade, valor e preço. Preferências ficam na sessão atual.

Cada linha traz item, unidade, histórico, municípios, valor conhecido, mediana
comparável e prioridade ou a primeira pendência relevante. Cobertura parcial
usa o aviso: “Há registros no recorte, mas a cobertura ainda não está
comprovada.” Um resultado vazio diz que não comprova ausência de compra.

No desktop a tabela prioriza comparação e abre a decisão em uma coluna clara.
No mobile filtros avançados continuam recolhidos, cartões/tabela preservam
unidade e origem e não há rolagem horizontal. Foco, labels, teclado e anúncio
de carregamento seguem os componentes do Observatório.

## Critérios de aceite executados

- Fonte sintética identificada; ela não é apresentada como dado público.
- Fonte oficial mostra fase e cobertura antes da ausência de registros.
- Preço não comparável não recebe mediana inventada.
- Revisão pede evidências para os seis critérios, jurídico e operacional.
- Cenário criado não contém necessidade, estoque, preço ou anuência presumidos.
- Testes Playwright em 1440 e 390 px passam com zero violações axe WCAG A/AA.
