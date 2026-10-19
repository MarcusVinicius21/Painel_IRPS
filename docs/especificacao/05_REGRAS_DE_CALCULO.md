# Regras definitivas de cálculo e rastreabilidade

## Base preservada

`../IRPS_PROJETO_MESTRE_V4/codigo/irps_core` é o núcleo auditado. A auditoria anterior executou 48 testes originais e 17 adicionais. Os 65 não foram repetidos nesta entrega por ausência de alterações no core. A demonstração tem adaptador TypeScript/Decimal para operar sem servidor; sua conformidade é testada em novas amostras de entradas/saídas do núcleo, sem alegar que o browser passou a executar o Python ou produzir resultados oficiais.

Um resultado pertence a organização + versão do cenário + período + município + item/versão + unidade + método. Manter quantidade solicitada, calculada, proposta e aprovada em campos separados. O protótipo calcula hipóteses, sem quantidade aprovada oficial.

## Método A - necessidade independente

`B = D × r × (1 + s)`; `L = max(0, B - E - R)`; `Q = ceil(L/passo) × passo`.

- D é direcionador pertinente ao objeto; r é taxa técnica para o horizonte; s é reserva justificada aplicada antes das deduções, conforme V4.
- E é estoque utilizável com data, destino e validade. R é recebimento confirmado e elegível no prazo/destino. Ausência de informação em E/R bloqueia conclusão; defaults zero da biblioteca não são evidência.
- Todos os números precisam ser finitos, não negativos e dimensionalmente compatíveis. Reserva acima de 100% exige outro método; passo positivo.
- Piso maior que teto bloqueia. Q fora de limites permanece visível para revisão: não cortar ao teto nem elevar ao piso automaticamente.
- Consolidar apenas o mesmo item/versão/unidade/horizonte. Ao retirar cidade, remover sua parcela; quantidades das demais não mudam. Reincluir recupera sua própria necessidade, sujeita à validade das entradas.

Exemplo sintético de papel: Ipatinga `150 × 1 - 30 - 0 = 120 caixas`; Alfenas `110 - 25 = 85 caixas`; Miracema tem estoque ausente e permanece sem Q conclusiva. Com referência fictícia de R$250, as duas primeiras parcelas somam R$51.250. Isso não é demanda real das cidades.

## Estratégias por família

| Família | Direcionador / horizonte | Guardas |
|---|---|---|
| Materiais | Atividade/unidades atendidas × taxa no período | Embalagem, estoque utilizável e entregas; histórico contratado não é consumo |
| Medicamentos | Demanda assistencial/protocolo × dose/ciclos/apresentação | Concentração, vencimento, protocolo e área farmacêutica; não mg→comprimido sem dado |
| Veículos | Rotas/capacidade/frota disponível/reposição | Não usar população como multiplicador automático; distinguir expansão e substituição |
| Serviços contínuos | Postos/jornada/cobertura × horas ou meses no horizonte | Não multiplicar por 12 se a taxa já é anual; contratos sobrepostos precisam revisão |
| Obras | Projeto/dimensões/trecho × coeficiente e medições | m² não vira m³ sem espessura; projeto e engenheiro responsável; custos não fornecem Q |
| Educação | Elegíveis por rede/etapa/ciclo, grade/tamanho quando pertinente | Matrícula não é necessariamente pessoa única; método por item |
| TI e outros | Usuário-mês, licença, equipamento ou outra dimensão declarada | Implantação única separada de recorrência; sem método, manter pendência |

O catálogo é aberto. Uma estratégia composta pode exigir serviço especializado em vez de forçar toda necessidade em D×r. Documento nunca injeta expressão executável no motor.

## Método B - meta física fundamentada

Envelope: meta T, item/versão/unidade, passo g, horizonte, documento, responsável, participantes autorizados, fontes dos pesos, pisos/tetos e revisão. Exigir todos os valores múltiplos de g e `Σpisos ≤ T ≤ Σtetos`.

1. Converter a passos discretos e atribuir pisos.
2. Distribuir o saldo proporcionalmente aos pesos de quem tem capacidade.
3. Saturar capacidades alcançadas e recalcular somente o saldo livre.
4. Na rodada sem saturação, atribuir partes inteiras das quotas.
5. Distribuir unidades restantes pelos maiores restos da mesma rodada. Empate por IBGE ordenado.
6. Pesos zero não recebem saldo, mas podem receber piso fundamentado. Saldo sem peso ativo é inviável.

V4 usa Fraction para quotas exatas. Caso obrigatório: `T=5`, pesos `1:2:3`, pisos zero e tetos folgados → `1/2/2`, soma 5. Com g=0,1 e T=0,5 → 0,1/0,2/0,2. Meta fora da capacidade ou não múltipla não produz distribuição válida. Maiores restos não garante monotonicidade em qualquer alteração de meta; comparar versões.

No protótipo, uma meta é definida por item. Itens sem envelope continuam pendentes. Alterar participantes invalida a revisão global e bloqueia o novo consolidado desse modo até confirmar a nova meta. Não redistribui a meta antiga silenciosamente. Produção deve conservar o antes/depois; manter meta após retirada exige justificativa e nova competência, nunca necessidade inflada no modo A.

## Preço, valor e recursos

`valor_linha = round_half_up(Q × preço_ref, 2)`; valor por cidade = soma das linhas monetárias; total = soma das cidades = soma por item. Unitário admite mais casas que o valor de linha. Moeda/horizonte devem ser compatíveis.

Preço precisa de especificação, fase, data, condição, amostra, exclusões, método, fonte, revisor e validade. `validated=True` no core é condição técnica, não aprovação administrativa. Preço ausente ou sigiloso mantém valor ausente. Mostrar subtotal parcial, quantidade de linhas elegíveis e faltas; não “total aprovado”. Orçamento insuficiente mostra diferença sem alterar Q física. Receita fiscal agregada, CMED, anúncio de transferência e SINAPI não são saldo livre do item.

## Simulação comercial privada

`receita = money(Q_venda × preço_venda)`.

`mercadoria = money(Q_venda × (aquisição_unitária + variável_unitária))`.

`tributos = money(receita × alíquota)`.

`custo_total = money(mercadoria + frete_fixo + despesas_fixas + tributos)`.

`lucro = money(receita - custo_total)`; `margem = money(100 × lucro/receita)` se receita>0; `acréscimo = money(100 × lucro/custo_total)` se custo_total>0.

`equilíbrio = ceil_centavo(((aquisição + variável) × Q + frete + fixos) / (Q × (1-alíquota)))` se Q>0.

Taxa é hipótese efetiva sobre receita e deve ser <100%, com conferência contábil real. Ausente não é zero. Q=0 pode gerar prejuízo de frete/fixos; margem e equilíbrio ficam sem base. Venda zero não gera margem. Markup do V4 significa lucro/custo total, incluindo tributos; não o multiplicador tradicional somente sobre aquisição.

Exemplo fictício: quantidade 100; aquisição R$ 20/un.; despesa variável R$ 2/un.; venda R$ 35/un.; frete R$ 100; despesas fixas R$ 200; tributos 6% → receita R$ 3.500; custos R$ 2.710; lucro R$ 790; margem 22,57%; acréscimo 29,15%; equilíbrio R$ 26,60/un. Venda a R$ 36/un. → receita R$ 3.600; custo R$ 2.716; lucro R$ 884. Aquisição a R$ 0,1001/un., com os demais custos zerados, exige preço de equilíbrio de R$ 0,11/un.. Não é recomendação comercial ou apuração fiscal.

## Histórico, previsões e fases

O núcleo histórico filtra município/item/unidade/fase e exige versões equivalentes e eventos deduplicados. Por padrão, três anos distintos. O adaptador deve provar anos completos e data de corte anterior ao horizonte; três anos presentes não provam completude. Sem coleta não preencher zero.

Mediana de contratado projeta contratação, nunca consumo. Para adoção real: backtest temporal por família, baseline simples, MAE/WAPE quando denominador válido, descarte e cobertura documentados. Cenários baixo/base/alto são sensibilidade, não probabilidades calibradas.

Publicado/estimado, homologado, contratado, solicitado, entregue, consumido, empenhado, liquidado e pago são naturezas distintas. Pago requer parcela conciliada; consumido requer registro próprio. Retificação substitui observação, estorno reverte evento e aditivo precisa indicar acréscimo versus valor global. Somar tudo causaria dupla contagem.

## Memória e reprodução

Guardar fórmula/versionamento, entrada normalizada e original, unidade, passo, precisão, origem/página, validade, critérios de exclusão, quantidade/status e revisor. Snapshot imutável permite reproduzir o relatório. Alteração relevante cria derivada; não reescrever o resultado aprovado anterior. A demo exporta todos os selecionados, inclusive faltas, e mantém arquivo público livre de custos privados.
