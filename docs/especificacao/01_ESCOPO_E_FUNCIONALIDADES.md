# Projeto Mestre final: contrato funcional

Escopo fechado para implementação e aprovação do projeto. Não é aprovação de despesa nem atestado de produção. As 25 funções abaixo abrangem RF01-RF21 e extensões 6R, sem apagar os contratos anteriores.

## Limites e papéis

Catálogo aberto a produtos, serviços e obras; conjunto variável N, começando com 118 identidades. Sem limite de vinte participantes. Segurança de produção por organização, recurso e ação. Consulta pública não vê estoque, proposta restrita nem custo privado. Gestor prepara; curadoria revisa método/equivalência; autoridade decide conforme ato; administrador opera acesso, sem competência automática.

## Inclusão e exclusão

Incluídos: inteligência pública, necessidade por cidade, meta global fundamentada, memória, preço/recursos, versões, relatório, importação revisável, simulação comercial privada e fontes/alertas. Não incluídos nesta entrega: operação produtiva, implantação externa, transmissão de atos oficiais, integração bancária, homologação automática ou garantia de ganho/compra futura. Todos os contratos de produção estão definidos; as integrações não foram simuladas como reais.

## F01 - Busca universal

**Correspondência:** RF01. **Superfícies:** pesquisa/resultados.

**Objetivo:** Candidatos separados por tipo e registros da fase selecionada.

**Entradas e dados:** Termo, código de item, IBGE, CNPJ, descrição, família e recorte. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** PNCP, Compras.gov.br, catálogo curado e IBGE. Público autorizado. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Identificar o tipo de entidade; buscar descrição e atributos; apresentar homônimos com UF. Preservar termo e filtros na URL. Não assumir equivalência pela semelhança textual.

**Retorno e próximos passos:** Candidatos separados por tipo e registros da fase selecionada. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Termo desconhecido retorna vazio no recorte. Fonte indisponível mantém último dado datado.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Busca real local por descrição, família, cidade e dois CNPJs do exemplo. Sem busca semântica externa.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Pesquisa e recuperação; cinco famílias; CNPJ federal.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F02 - Quem compra

**Correspondência:** RF02. **Superfícies:** resultados/produto/municipio.

**Objetivo:** Lista de compradores, territórios e abrangência do recorte.

**Entradas e dados:** Item/versionamento, órgão, município-território, fase, período. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** PNCP/Compras; documentos da entidade. Consulta pública conforme origem. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Contar órgãos por identidade canônica; municípios por IBGE. Não multiplicar um contrato do consórcio pelos participantes. Universidade federal não é prefeitura.

**Retorno e próximos passos:** Lista de compradores, territórios e abrangência do recorte. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Órgão sem vínculo territorial confirmado fica pendente. Não inferir participante a partir da sede.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Registros sintéticos para as 118 identidades; caso UNIFAL explicitamente federal.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Órgão federal e CNPJ; consulta municipal.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F03 - Histórico de contratação

**Correspondência:** RF03, RF13. **Superfícies:** processo/municipio.

**Objetivo:** Histórico temporal com valores da fase e vínculo à origem.

**Entradas e dados:** Observação, obrigação, documento, item original, quantidade, unidade, fase e datas. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** PNCP, contratos, anexos e portais. Público se documento publicável; interno por organização. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Agrupar por obrigação e evento. Versão substituída não conta outra vez. Pedido, entrega e contrato não são três compras independentes.

**Retorno e próximos passos:** Histórico temporal com valores da fase e vínculo à origem. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Quantidade desconhecida permanece desconhecida, mesmo havendo preço ou valor financeiro.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Histórico e retificação ilustrativos, com alteração refletida na pesquisa.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Retificação sem soma da versão anterior.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F04 - Preços comparáveis

**Correspondência:** RF04, RF21. **Superfícies:** produto/comparar.

**Objetivo:** Tabela e faixa da mesma apresentação, com amostra e descarte.

**Entradas e dados:** Item, apresentação, embalagem, unidade, fase, data, região, condições e observações elegíveis. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Compras, PNCP; BPS/CMED/SINAPI/SICRO quando pertinentes. Consulta pública e curadoria. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Filtrar equivalência antes de mediana/faixa. Não combinar estimado e pago; não converter massa/volume sem fator técnico. Excluir observações com motivo revisável.

**Retorno e próximos passos:** Tabela e faixa da mesma apresentação, com amostra e descarte. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sigilo e ausência impedem completar uma referência. CMED não é preço pago.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Comparação sintética da mesma versão; variantes mantidas separadas.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Unidades diferentes; fase mantida no filtro.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F05 - Pagamentos e despesas

**Correspondência:** RF13 + extensão financeira 6R. **Superfícies:** pagamentos.

**Objetivo:** Pago líquido documentado, fases separadas e lacunas.

**Entradas e dados:** Obrigação, empenho, liquidação, parcelas pagas, estornos, competência e documento. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Portais municipais e TCE; vínculo ao processo. Conforme publicidade e escopo da origem. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Conciliar eventos financeiros; valor pago líquido é pagamentos menos estornos válidos. Não somar fases. Quantidade consumida exige evidência própria.

**Retorno e próximos passos:** Pago líquido documentado, fases separadas e lacunas. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sem conciliação: pagamento não comprovado no recorte. Estorno não reduz silenciosamente o contrato.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Razão sintética 5.000 + 3.000 - 500 = 7.500, com estado ausente reversível.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Fases e pagamento líquido.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F06 - Frequência de compras

**Correspondência:** RF13 + extensão de recorrência. **Superfícies:** necessidades/produto.

**Objetivo:** Recorrência observada e limite de cobertura.

**Entradas e dados:** Eventos deduplicados, janela, anos completos e órgão/item/unidade/fase. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Histórico conciliado e cobertura. Consulta pública conforme origem. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Medir intervalos somente com cobertura suficiente. Ano não coletado não é ano zero. Compra anualizada não deve ser multiplicada novamente.

**Retorno e próximos passos:** Recorrência observada e limite de cobertura. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Série insuficiente não produz periodicidade ou data garantida.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Três anos de histórico explicitamente fictício; frequência real não validada.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Cenário temporal e estados de cobertura.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F07 - Possível nova necessidade

**Correspondência:** RF06, RF13. **Superfícies:** necessidades/memoria.

**Objetivo:** Cenário estimativo, premissas, confiança qualitativa e pendências.

**Entradas e dados:** Histórico comparável e/ou parâmetros físicos do método setorial. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Fontes setoriais, estoque/recebimentos e histórico. Consulta pública ou planejamento autorizado. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Separar previsão de contratação de necessidade física e de consumo. Mediana anual V4 requer por padrão três anos distintos, cuja completude o serviço valida. Avaliar contra baseline temporal.

**Retorno e próximos passos:** Cenário estimativo, premissas, confiança qualitativa e pendências. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sem série, parâmetros ou estoque: não calcular conclusão oficial. Sem precisão inventada.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Mediana fictícia 180/210/195 e necessidade física editável; sem promessa preditiva.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Estoque ausente; mediana ilustrativa.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F08 - Perfil municipal e do órgão

**Correspondência:** RF18, RF20. **Superfícies:** municipio/fontes.

**Objetivo:** Compras encontradas, órgãos, categorias e cobertura.

**Entradas e dados:** IBGE, nome/UF, natureza do órgão, CNPJ/unidade e recorte. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** IBGE; PNCP; SICONFI como contexto. Consulta pública e dados internos por vínculo. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Manter entidade compradora, território e participante em relações distintas. Resolver identidade não prova vínculo nem histórico.

**Retorno e próximos passos:** Compras encontradas, órgãos, categorias e cobertura. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Não consultado difere de consulta vazia; prefeitura não herda compra federal.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** 118 identidades reutilizadas e contexto municipal navegável.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Cadastro e seleção de 118; órgão federal.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F09 - Perfil de produto, serviço ou obra

**Correspondência:** RF01, RF17. **Superfícies:** produto.

**Objetivo:** Equivalência, compradores, preços e memória contextual.

**Entradas e dados:** Descrição original/canônica, família aberta, versão, dimensões e unidade. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** CATMAT/CATSER, documentos e curadoria. Consulta e curadoria técnica. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Preservar original e atributos. Catálogo extensível não implica regra universal de necessidade.

**Retorno e próximos passos:** Equivalência, compradores, preços e memória contextual. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Nova variante não entra automaticamente num agregado anterior.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** 100 itens em cinco famílias; cadastro de item novo sem parâmetros automáticos.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Catálogo 100; cadastro e unidade.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F10 - Comparar municípios

**Correspondência:** RF02, RF04. **Superfícies:** comparar.

**Objetivo:** Diferenças de quantidade, preço e cobertura.

**Entradas e dados:** Municípios selecionados, mesmo item/unidade/fase/período. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Mesma população de fatos do histórico. Consulta autorizada. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Comparar o conjunto autorizado. Indicador por habitante somente se pertinente e fundamentado. Gráfico mostra até oito selecionados; tabela mantém todos.

**Retorno e próximos passos:** Diferenças de quantidade, preço e cobertura. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sem unidade compatível, separar comparação e explicar impedimento.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Tabela paginada e barras da mesma especificação.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Comparação e filtros sem perder selecionados.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F11 - Montar licitação: objetos

**Correspondência:** RF01, RF07, RF17. **Superfícies:** itens.

**Objetivo:** Conjunto explícito de itens do cenário.

**Entradas e dados:** Itens, unidades, versões, embalagem, período e passos. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Catálogo e importação revisada. Preparador autorizado. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Adicionar qualquer família. Não misturar unidades nem executar fórmula proveniente de documento. Itens sem método entram pendentes.

**Retorno e próximos passos:** Conjunto explícito de itens do cenário. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Item sem preço ou parâmetros mantém pendência; não completa zeros.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** 100 itens selecionáveis e cadastro local extensível.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: 100 itens; importação e cadastro.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F12 - Montar licitação: participantes

**Correspondência:** RF05, RF18. **Superfícies:** participantes/licitacao.

**Objetivo:** Conjunto N, contagem total/visível, inclusão e reversão.

**Entradas e dados:** IDs municipais, grupo salvo, filtro, ato/anuência em produção. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Cadastro IBGE; atos da organização para uso oficial. Preparador no escopo competente. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Seleção independente de visibilidade. Lote explicita resultados do filtro ou cadastro completo. Remover não apaga o município.

**Retorno e próximos passos:** Conjunto N, contagem total/visível, inclusão e reversão. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Vínculo não comprovado impede aprovação, não consulta de cadastro.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** 3/10/20/118 e seletor por nome/UF/IBGE, cancelar/desfazer.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Modo A; 118×100; modal teclado.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F13 - Necessidade individual

**Correspondência:** RF06. **Superfícies:** quantidades/memoria.

**Objetivo:** Quantidade calculada, status, memória e subtotal.

**Entradas e dados:** Direcionador, taxa, reserva, estoque, recebimentos, limites, unidade, fontes e horizonte. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Métodos setoriais e evidências locais. Preparador e revisor técnico. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Executar calculate_need V4 com insumos válidos. Somar parcelas independentes do mesmo item. Retirar participante só subtrai sua parcela.

**Retorno e próximos passos:** Quantidade calculada, status, memória e subtotal. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Ausente não usa defaults zero. Limite violado bloqueia, sem truncar/inflar Q.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Adaptador decimal local com parâmetros sintéticos e comparação adicional ao core.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Modo A; estoque; limites; orçamento preserva Q.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F14 - Quantidade global fundamentada

**Correspondência:** RF08. **Superfícies:** distribuicao.

**Objetivo:** Distribuição por cidade, soma exata e nova revisão.

**Entradas e dados:** Meta física, passo, participantes, justificativa, pesos, pisos, tetos e fontes. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Documento de meta e método; core allocate_total. Responsável técnico e autoridade competente. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Pisos, saturação, maiores restos da mesma rodada; empate por IBGE. Alterar conjunto invalida revisão. Não recalcular meta antiga silenciosamente.

**Retorno e próximos passos:** Distribuição por cidade, soma exata e nova revisão. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Meta fora da capacidade ou pesos insuficientes: bloquear distribuição.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Modo B interativo por item; T=5 pesos 1/2/3 produz 1/2/2.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Modo B válido/inviável; mudança de participantes.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F15 - Preços e total da licitação

**Correspondência:** RF09, RF21. **Superfícies:** precos/licitacao.

**Objetivo:** Total estimado ou subtotal parcial com contagem de faltas.

**Entradas e dados:** Quantidade revisável, preço por item/versão, moeda e condições. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Pesquisa de preço validada e V4. Preparador; revisor competente para preço. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Arredondar linha em centavos HALF_UP; somar linhas por cidade e item. Totais reconciliam. Não somar quantidades de unidades distintas.

**Retorno e próximos passos:** Total estimado ou subtotal parcial com contagem de faltas. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Preço ausente/sigiloso/incompatível não é zero; referência validada tecnicamente não é ato administrativo.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Preço editável altera cenário e exports.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Preço ausente; relatórios dinâmicos.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F16 - Recursos e contexto financeiro

**Correspondência:** RF09, RF16. **Superfícies:** precos.

**Objetivo:** Diferença financeira e tarefa de comprovação.

**Entradas e dados:** Recurso, item, período, documento, vinculação e validade. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Documento financeiro específico; contas públicas como contexto. Financeiro competente. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Comparar recursos evidenciados ao valor. Preservar quantidade física diante de insuficiência. SICONFI/transferência não geram saldo livre.

**Retorno e próximos passos:** Diferença financeira e tarefa de comprovação. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Ausência de recurso fica pendente. Não reduzir Q para aparentar adequação.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Recursos fictícios editáveis com diferença e aviso; Q invariável.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Orçamento insuficiente.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F17 - Versões, revisões e aprovação

**Correspondência:** RF16, RF19. **Superfícies:** revisao/relatorios.

**Objetivo:** Antes/depois, responsável, decisão e histórico.

**Entradas e dados:** Versão de cenário, entradas, competência, revisão, evidências e decisão. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Organização, atos e trilha de auditoria. Revisor e autoridade dentro do escopo. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Snapshot imutável; entrada alterada invalida revisão da nova versão. Conflito exige versão esperada. Administração não concede competência automaticamente.

**Retorno e próximos passos:** Antes/depois, responsável, decisão e histórico. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Versão antiga não é sobrescrita; submissão não é aprovação oficial.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Versões locais, comparação e revisão demonstrativa identificada.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Versões diferentes; desfazer; papel de revisão.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F18 - Simulação comercial privada

**Correspondência:** RF10, RF15. **Superfícies:** negocio.

**Objetivo:** Receita, custo, lucro/prejuízo, margem e equilíbrio.

**Entradas e dados:** Quantidade de venda, aquisição, preço de venda, variável, frete, fixos e tributos. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Informação da empresa e contador; nunca presumida de fonte pública. Somente empresa e sujeitos autorizados. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Receita/custos/resultado via calculate_quote; margem sobre receita e acréscimo sobre custo total. Equilíbrio arredonda para cima. Separar resultado privado, valor público e receita do IRPS.

**Retorno e próximos passos:** Receita, custo, lucro/prejuízo, margem e equilíbrio. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Custo ausente não é zero. Receita zero não dá margem; q=0 pode ter prejuízo fixo. Taxa ≥100% inválida.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Área visualmente restrita à empresa; valores fictícios; salvamento separado e export privado.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Comercial e limites; arquivo público sem custos.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F19 - Importação revisável

**Correspondência:** RF11. **Superfícies:** documentos.

**Objetivo:** Campos extraídos, proposta revisável e vínculo à origem.

**Entradas e dados:** Originais PDF/DOCX/XLSX/CSV, conteúdo, página/célula, confiança e classe. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Arquivos autorizados da organização. Preparador documental; curadoria. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Preservar original; deduplicar por conteúdo; validar unidade/quantidade; revisar exceções; lote com falhas parciais e retomada idempotente. Não executar fórmulas anexadas.

**Retorno e próximos passos:** Campos extraídos, proposta revisável e vínculo à origem. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Conflito, formato e confiança insuficientes exigem revisão. Binário sem leitor não recebe falsa extração.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** CSV realmente lido no navegador, duplicidade e revisão. PDF/DOCX/XLSX limitados a recebimento local.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Leitura CSV; duplicidade; binários e erro de formato.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F20 - Relatório versionado

**Correspondência:** RF12. **Superfícies:** relatorios.

**Objetivo:** PDF/CSV/XLSX demonstrativos, soma e memória reconstruíveis.

**Entradas e dados:** Snapshot, seleção, recorte declarado, entradas, fontes, versão e classificação. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Snapshot e observações autorizadas. Consulta da versão dentro da organização. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Recalcular a mesma versão; exportar conjunto declarado incluindo linhas pendentes. Filtro visual não remove selecionados. Permissões e revogação na entrega em produção.

**Retorno e próximos passos:** PDF/CSV/XLSX demonstrativos, soma e memória reconstruíveis. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Falha não gera documento de outra versão. Privado não entra em relatório público.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** PDF/CSV/XLSX dinâmicos; versão atual/salva e recorte por item.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Arquivos antes/depois; 11.800 linhas; PDF analisado.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F21 - Fontes e cobertura

**Correspondência:** RF20. **Superfícies:** fontes.

**Objetivo:** Matriz de cobertura, data e limites.

**Entradas e dados:** Cidade, órgão, fonte, janela, objeto, fase, páginas e versão do conector. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** 16 contratos de fontes do Gate A. Consulta; operação autorizada. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Distinguir não consultado, vazio do recorte, indisponível, sigiloso, retificado e fora da jurisdição. Guardar último sucesso.

**Retorno e próximos passos:** Matriz de cobertura, data e limites. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** HTTP 200 de documentação não encerra integração. Falha não zera histórico.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Inventário real do estudo separado de estados simulados de fonte.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Fonte indisponível preserva exemplo; filtros.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F22 - Alertas e acompanhamentos

**Correspondência:** RF14. **Superfícies:** alertas.

**Objetivo:** Pendências acionáveis e acompanhamento contextual.

**Entradas e dados:** Recorte salvo, documentos, prazos, retificações e preferências. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Conectores e versões de fontes. Dono do acompanhamento. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Alertar mudança comprovada, respeitando permissão, frequência e decisão de acompanhamento. Não garantir nova licitação.

**Retorno e próximos passos:** Pendências acionáveis e acompanhamento contextual. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sem atualização não inventar notificação ou prazo; canal externo depende autorização.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Acompanhamentos locais e três pendências navegáveis, sem envio remoto.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Acompanhar/desacompanhar; origem da retificação.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F23 - Acessos e organizações

**Correspondência:** RF15. **Superfícies:** entrada/administracao.

**Objetivo:** Visões adequadas e trilha autorizada.

**Entradas e dados:** Identidade confiável, memberships, papel, cidade/recurso, classe e ação. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Provedor de identidade e política da organização. Conforme ação; admin não herda custo privado. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Autorizar no servidor antes de retornar qualquer dado; cache/exportação/jobs seguem escopo. Revogação invalida acesso ao artefato.

**Retorno e próximos passos:** Visões adequadas e trilha autorizada. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Negar sem revelar payload. Flags fornecidas pelo navegador nunca comprovam autorização.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Entrada e perfis visuais simulados. Sem segurança real ou dados privados verdadeiros.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Área comercial/admin por perfil; limites documentados.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F24 - Métodos por família

**Correspondência:** RF17, RF06. **Superfícies:** administracao/memoria.

**Objetivo:** Método com parâmetros, memória e aceite.

**Entradas e dados:** Entradas, dimensões, algoritmo seguro, referência técnica, unidade, validade e testes. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Técnicos de saúde, frota, engenharia, serviços e materiais. Curadoria/área competente. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Publicar estratégia versionada após revisão setorial; invalidar derivadas quando critério muda. Não executar código de documento ou fallback populacional universal.

**Retorno e próximos passos:** Método com parâmetros, memória e aceite. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Sem estratégia publicada, item mantém cadastro e histórico, mas não quantidade oficial.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Contratos de cinco famílias e edição local de parâmetros por município/item.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Memória e parâmetros; família nova pendente.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## F25 - Catálogo extensível

**Correspondência:** RF17. **Superfícies:** itens/documentos.

**Objetivo:** Item novo com estado de método e preço explícitos.

**Entradas e dados:** Família, descrição, versão, unidade, passo, aliases, embalagem e conversões. Preservar tipo, unidade, fase, período e versão.

**Origem e acesso:** Catálogos oficiais e curadoria documental. Curadoria e preparadores conforme política. Fontes do estudo e dados sintéticos ficam separados.

**Regra:** Adicionar categoria sem alterar enums de domínio. Equivalência/conversão exige fonte e curador; preservar versões anteriores.

**Retorno e próximos passos:** Item novo com estado de método e preço explícitos. A ação de tela deve retornar ao contexto que a iniciou. Alterações relevantes exigem versão/revisão.

**Exceções:** Cadastro novo não inventa taxa, preço ou necessidade.

**Texto para o usuário:** “Confira a origem e o período antes de usar este resultado.” Em pendências, informar fato, impacto e próxima ação disponível.

**Demonstração entregue:** Novo item local, inclusive outra família, começa sem parâmetros conhecidos.

**Critério de aceite:** entradas válidas produzem as saídas descritas; erros preservam contexto e não inventam números; acesso segue o escopo; desktop/mobile completam a tarefa com unidade/fase. Verificação específica: Novo item; importação; unidades incompatíveis.

**Produção:** exige autorização no serviço, persistência, observação oficial rastreável quando aplicável e teste de contrato/ponta a ponta. Nenhuma passagem de teste local autoriza o ato oficial.

## Matriz de aceite assinável

| Dimensão | Entrega | Aceite formal |
|---|---|---|
| Escopo e contratos | F01-F25, fontes e regras consolidados | Responsável do projeto: a preencher |
| Design | Observatório escolhido; galeria desktop/mobile | Revisão de acabamento pelo usuário |
| Demonstração | Código e QA reproduzíveis, sem efeito oficial | Conferência de tarefas e limites |
| Produção | Fora desta implantação; plano e critérios especificados | Autorização posterior, por incremento |

Não há requisito funcional abandonado: os que dependem de fonte/autoridade têm contrato completo e alternativa sintética explicitada. A prova de operação real continua independente da conclusão do projeto/design.
