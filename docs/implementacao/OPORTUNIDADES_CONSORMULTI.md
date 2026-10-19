# Inteligência de oportunidades — implementação verificável

## Propósito e limite

Este incremento permite encontrar itens com histórico registrado, comparar o
recorte entre municípios e encaminhar um **rascunho** ao módulo Montar
Licitação. Ele não presume demanda futura, estoque, recurso, anuência,
aprovação, entrega, pagamento ou consumo.

Dados oficiais, demonstração sintética e informações comerciais privadas ficam
separados. Publicação, resultado, contrato, empenho, liquidação, pagamento e
consumo são situações distintas; a consulta mostra uma situação por vez e
nunca soma essas fases como compras independentes.

## O que está executável

| Capacidade | Implementação | Critério de verdade |
|---|---|---|
| Coleta histórica PNCP | `history.py` agenda publicações por janelas de sete dias, itens, resultados e contratos; `history_collection`/`history_task` guardam retomada, pausa, limite e tentativas | Cada página tem URL, data, SHA-256 e estado. O limite encerra como `limited`, não como cobertura completa. |
| Histórico e filtros combinados | `POST /api/v1/opportunities/query` recebe município, grupo, órgão, categoria, item, período, mês, ano, modalidade, fornecedor, quantidade, valor e preço | Filtros ausentes não viram valor inventado; datas futuras são recusadas. |
| Indicadores | O serviço calcula registros, municípios, meses ativos, recorrência, valores conhecidos, concentração e preços comparáveis | Um preço só é comparável com mesma unidade e item/ equivalência revisada. |
| Equivalência técnica | `opportunity_equivalence` exige membro, unidade, justificativa, evidência e revisor | Sem revisão, só a mesma versão de item e unidade é agrupada. |
| Prioridade | Gera 0–100 somente após portas mínimas e revisão humana | Sem dados suficientes, a tela mostra o que falta em vez de pontuar. |
| Viabilidade | Seis critérios (logística, padronização, fornecedores, exigências, prazo e disponibilidade), mais análise jurídica e operacional | Cada avaliação exige evidência; revisão não aprova fornecimento. |
| Detalhe e cenário | Detalhe mostra mensalidade, cobertura, preços, municípios, fornecedores e documentos. O cenário usa participantes e item observados | O rascunho não recebe necessidade, estoque, preço, anuência ou aprovação inferidos. A chave de idempotência evita duplicação. |
| Acompanhamentos | Relaciona o conjunto exato de versões já visto e registra nova publicação ou mudança comprovada | Não consulta nem envia aviso externo automaticamente. |

## Pontuação configurável e auditável

A prioridade só é calculada quando o recorte contém pelo menos três registros,
três meses ativos, dois municípios, três preços comparáveis, 80% de cobertura
de cidades-dias e doze meses concluídos, além de revisão humana jurídica e
operacional viável. Caso contrário, retorna `needs_review_or_data` e a razão.

Quando todas as portas passam, os quatro componentes normalizados são
recorrência, dispersão municipal, comparabilidade de preço e facilidade de
fornecimento. A pessoa responsável escolhe pesos que somam 100; o valor é
`Σ(peso × componente) / 100`, limitado a 0–100. A facilidade vem da média das
seis avaliações de 1–5, convertida para 0–100. A fórmula, entradas, revisão e
fonte permanecem na resposta da API; ela ordena investigação, não garante
compra, margem ou contratação.

## Evidência de fonte pública executada em 19/10/2026

Uma coleta local, com conta de teste e sem credenciais externas, consultou o
PNCP entre 13 e 19/10/2026 para IBGE `3131307`, modalidade 6 e máximo de duas
páginas. Foram retornados três registros após duas chamadas e o estado final
foi `limited`; portanto a cobertura do município **não** é afirmada. As URLs
e digests estão em `source_observation`, acessíveis pela coleta, mas o corpo
bruto não é publicado neste repositório.

Uma segunda coleta, depois de o CNPJ constar na resposta de item, consultou a
rota pública de contratos do mesmo órgão, no mesmo período e com uma página.
Retornou um contrato e terminou `completed`. Contrato sem itens documentados
não produziu quantidade nem preço unitário e não entrou no ranking. A rota de
resultados está implementada e coberta por teste controlado; ela não foi
acionada nessa pequena prova porque o limite de páginas foi atingido antes.

| Chamada pública consultada | Evidência disponível |
|---|---|
| [Publicações do recorte](https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20261013&dataFinal=20261019&codigoModalidadeContratacao=6&pagina=1&tamanhoPagina=10&codigoMunicipioIbge=3131307) | URL e SHA-256 `ef9ddafe9eeb09c0289dd8d609b0f8582bc856a734b10d0351618f96682e5305` |
| [Itens da publicação identificada](https://pncp.gov.br/api/pncp/v1/orgaos/19876424000142/compras/2026/140/itens?pagina=1&tamanhoPagina=10) | URL e SHA-256 `80186508c8ef2de575a30e15b7e909163d176513a92acf7b1397a8a4e2f21af7` |
| [Contratos do órgão](https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20261013&dataFinal=20261019&pagina=1&tamanhoPagina=10&cnpjOrgao=19876424000142) | Uma página e um registro; gravados na coleta local |

Os contratos verificados da fonte são a [API de Consulta do PNCP](https://pncp.gov.br/api/consulta/v3/api-docs)
e o [Manual do PNCP](https://pncp.gov.br/manual/pt-br/latest/singlehtml/).
Disponibilidade, janela e conteúdo podem mudar; a coleta preserva esse fato em
vez de prometer cobertura histórica.

## Operação na interface

1. Em **Oportunidades**, selecione fonte, situação e período; campos avançados
   ficam recolhidos para reduzir esforço.
2. Veja cobertura antes de interpretar ausência de registros.
3. Abra a análise, confira histórico, documentos e preços comparáveis.
4. Registre a revisão humana somente com evidências.
5. Crie um rascunho de licitação e complete as quantidades no módulo V4.

O recorte sintético é mostrado explicitamente como exemplo e só existe para
teste de interface. Dados comerciais não são expostos nesses endpoints.

## Limites conhecidos

- PNCP é a primeira fonte ativa. Resultados, contratos e preços dependem de
  rotas e campos presentes na resposta, não de suposição.
- Não há previsão automática. O histórico apoia uma decisão, mas não declara
  que o município comprará novamente.
- Alertas registram diferenças de itens já coletados; agendamento, e-mail e
  monitoramento contínuo exigem uma etapa posterior.
- Cobertura nacional e cadastro de fornecedores/ exigências logísticas exigem
  coleta suficiente e revisão humana.

Consulte o [fluxo](FLUXO_OPORTUNIDADES.mmd), a [tela](../especificacao/telas/T24_OPORTUNIDADES.md)
e as [evidências](../validacao/OPORTUNIDADES_RESULTADOS.md).
