> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Fontes operacionais e cobertura comprovada

As consultas abaixo foram GETs públicos, sem autenticação externa, em 19/10/2026. Os resultados foram gravados no PostgreSQL, com URL, conteúdo, SHA-256, data, órgão, fase e cobertura. Os fixtures dos testes ficam em outro banco.

| Fonte | Contrato validado | Consulta e gravação real | Quantidade observada | O que não comprova |
|---|---|---|---:|---|
| IBGE localidades | [Documentação](https://servicodados.ibge.gov.br/api/docs/localidades) | [Ipatinga, 3131307](https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3131307) | 1 cadastro | População, indicadores setoriais, necessidade de qualquer item ou atualização das 118 cidades |
| PNCP Consulta | [OpenAPI](https://pncp.gov.br/api/consulta/v3/api-docs) | Publicações de 18–19/10/2026, modalidade 6, página 1, tamanho 10, recorte geral | 10 publicações | Contrato, entrega, consumo ou pagamento |
| PNCP Consulta | Mesmo contrato | Publicações de 13–19/10/2026, modalidade 6, página 1, tamanho 10, IBGE 3131307 | 2 publicações | Histórico integral de Ipatinga ou de outros participantes |
| PNCP itens | [OpenAPI da API PNCP](https://pncp.gov.br/api/pncp/v3/api-docs) | Duas publicações já preservadas; página 1, tamanho 10 por publicação | 20 itens | Quantidade contratada, efetivamente entregue ou consumida |
| PNCP contratos | [API de Consulta](https://pncp.gov.br/api/consulta/v3/api-docs) | Coleta limitada de 13–19/10/2026, com CNPJ obtido da resposta de item, uma página | 1 contrato | Itens, quantidade, preço unitário, entrega, pagamento ou consumo |
| Compras.gov.br CATMAT | [OpenAPI](https://dadosabertos.compras.gov.br/v3/api-docs) | [10 descrições de materiais](https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial?pagina=1&tamanhoPagina=10) | 10 descrições | Quantidade adquirida, preço pago, unidade de fornecimento pronta para cálculo |
| Compras.gov.br CATSER | Mesmo contrato | [10 descrições de serviços](https://dadosabertos.compras.gov.br/modulo-servico/6_consultarItemServico?pagina=1&tamanhoPagina=10) | 10 descrições | Contratação, medição do serviço, quantidade ou pagamento |

O banco de execução possui **32 fatos oficiais PNCP: 12 cabeçalhos de publicação e 20 itens**. Não são 32 contratações realizadas. Não somar valores de cabeçalhos e itens entre si. Catálogos são armazenados em tabela própria, sem criar fatos de compra.

Dez itens consultados informam orçamento sigiloso. Seus preços e totais permanecem ausentes, mesmo quando a resposta pública contém zero nesses campos. Quantidades e unidades são preservadas como publicadas. Equivalência técnica entre itens de diferentes compras ainda precisa ser curada; nenhum item oficial é convertido silenciosamente em item fictício.

## Identidade municipal e órgão

As 118 identidades conciliadas no Comando 5 foram reutilizadas. Isso não é uma consulta nova das 118 cidades. A carga de teste usa nomes/códigos reais, parâmetros físicos fictícios e identificação explícita.

Comprador é órgão/CNPJ/unidade. Município é território. Quando um código territorial do PNCP ainda não está no cadastro, ele fica na evidência original; não inventamos uma vinculação na FK. É possível consultar e incluir outra identidade pelo IBGE. O cadastro regular admite expansão nacional, sem teto de 20 participantes; o cenário admite até 6 mil identidades e 100 itens, sujeito aos limites de transporte/recursos. O volume **efetivamente testado** é 118 × 100.

## Resiliência executável

- URLs e rotas fixas por provedor; não há URL arbitrária enviada por usuário ou IA.
- TLS normal, sem ignorar certificados; timeout de conexão e de leitura; limite de resposta de 4 MB.
- Janela de publicações PNCP limitada a sete dias e uma página por job; tamanho 10–20.
- Pausa em 429/503 respeita `Retry-After`, limitada entre 60 e 3.600 segundos. Não há retentativa agressiva.
- Cache de respostas preservadas por até cinco minutos, mantendo a data da observação original.
- Jobs e consulta têm identidade, idempotência e checkpoint. Retomada é explícita e revalida a permissão.
- Falha não apaga histórico; cobertura indisponível não significa “não comprou”.
- Alteração de identidade IBGE não corrige silenciosamente o cadastro. O resultado informa conflito para revisão.

## Limites e fontes ainda não operacionais

Resultados PNCP são consultados somente quando a resposta de item informa disponibilidade; a rota foi validada por teste controlado e não foi acionada na pequena coleta real porque o limite de páginas foi atingido. A coleta de contratos está ativa, mas não converte contrato sem item documentado em quantidade ou preço.

Execução financeira PNCP; histórico de preços/contratos Compras.gov.br; INEP; SICONFI; TCE-MG/RJ; portais municipais; Transferegov; diários; BPS/CMED; SINAPI/SICRO; SIOPS/SIOPE continuam sem coletor ativo. Os estudos anteriores continuam válidos como referências de implementação, sem serem anunciados como integrações concluídas.

Fonte para necessidade física depende do item: população isolada não calcula medicamentos, veículos, serviços ou obras. A entrada atual aceita base/taxa/fontes revisáveis e usa o V4. Não há previsão municipal validada com o histórico oficial desta pequena amostra.

## Evidências reproduzíveis

`evidencias/fontes-publicas-execucao.json`, `fontes-itens-catalogos-execucao.json`, `registros-oficiais-persistidos.json`, OpenAPIs salvos e jobs com estado concluído. Os scripts `validar_fontes_publicas.py` e `validar_itens_e_catalogos.py` repetem consultas públicas pequenas; não precisam de chaves e não ativam serviços pagos.

## Atualização do incremento de cobertura (20/10/2026)

O quadro acima documenta a execução anterior e mantém suas contagens históricas. Nesta branch há coleta real adicional de resultados PNCP e pesquisa pontual de preços Compras.gov.br; as contagens, comprovantes, recortes e limites atuais estão em [`PILOTO_COBERTURA_CATALOGO.md`](../validacao/PILOTO_COBERTURA_CATALOGO.md). Atas/PCA e seus índices têm conectores limitados e testes controlados; não são compras adicionais. TCE-MG/Sicom e portais municipais continuam sem conector autenticado por contrato público verificado. Consulte [`COBERTURA_HISTORICA_CATALOGO.md`](COBERTURA_HISTORICA_CATALOGO.md) para a matriz de rotas e estados vigente.
