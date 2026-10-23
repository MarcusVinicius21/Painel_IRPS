# IRPS — Entrega dos 12 meses oficiais

Período: **01/10/2025 a 30/09/2026**. Resultado: **12 competências × 2 arquivos conferidos**, consulta anual funcional e 27 microtarefas com commits locais individuais. Nenhum push, PR, merge ou deploy.

## O que pode ser consultado

| Tipo | Códigos do catálogo pesquisável | Códigos com preço nos 12 meses | Presença de preço no catálogo |
|---|---:|---:|---:|
| CATMAT | 345.575 | 125.493 | 36,31% |
| CATSER | 3.104 | 2.286 | 73,65% |
| Total | 348.679 | 127.779 | 36,65% |

Os 348.679 códigos dos catálogos validados estão disponíveis para pesquisa. Ter cadastro não comprova preço ou compra. A presença de preço foi contada uma vez por tipo+código na janela, sem somar distintos mensais.

São **2.078.067 registros lógicos de itens de compra**, iguais às linhas físicas neste conjunto, sem conflito de chave encontrado. **38.613 não têm unidade informada**; nenhum preço está ausente neste conjunto. Nove códigos de serviço da origem não constam do catálogo e permanecem sinalizados. Quantidades não foram somadas entre apresentações distintas.

[Manifesto completo de cobertura](COBERTURA_12_MESES.json) contém as 24 origens oficiais, hashes, contagens e qualidade por arquivo.

## Consulta local

Abra http://127.0.0.1:5296/ com o operador já configurado. Pesquise o código em Inteligência e Planejamento. Em Preços praticados, use **Consultar últimos 12 meses fechados** ou informe o período. O consolidado, as versões originais e a API são opções separadas. Expanda **Meses consultados** e **Conferir registro original** para revisar as fontes.

- CATSER 14729: 1.290 registros anuais; API setembro tem 223 e CSV 224. Uma chave extra identificada no arquivo; causa da ausência na API ainda indeterminada.
- CATMAT 463700: 89 registros anuais. É gordura vegetal/margarina, não café.
- CATMAT 10006: sem preços no recorte verificado; não significa que nunca foi comprado.
- NOBREAK: publicação PNCP original estimada, sem código de catálogo presumido.

O histórico PNCP permanece separado e não representa consumo. Os registros mensais não preenchem entradas do V4 nem confirmam participação municipal.

## Validações

351 testes Python + 200 subtestes aprovados em banco novo; três testes Playwright reais aprovados; build e migrações até 0015 aprovados. Oito módulos V4 e sete referências intactos. Um operador preservado. Onze backups realmente restaurados antes das cargas. Catálogo preservado; PNCP conserva 509 fatos físicos, dos quais 495 atuais. Auditoria Git sem achados pelos padrões executados.

Consulta por código medida entre cerca de 0,02 e 0,30 s. Primeiro resumo global demorou 299 s; sua reutilização levou 0,032 s. A busca do produto não aguarda esse resumo. O custo inicial do agregado global é uma limitação real.

## Pendências reais

- 38.613 unidades ausentes; sem preenchimento presumido ou médias automáticas.
- Nove códigos de serviço fora do catálogo: conferência com a origem, sem troca automática para material.
- Causa da diferença API/CSV de 14729 não comprovada.
- No estudo real aberto, dois municípios permanecem pendentes. Não há manifestações confirmadas ou total consolidado. Documentos, conferência municipal e atos administrativos continuam necessários.
- Arquivos importados não comprovam todas as compras nacionais ou municipais, entrega, pagamento ou consumo.
- Produção, segurança de hospedagem e publicação continuam fora desta rodada.

## Relatórios por microtarefa

- [B00_01](B00_01.md)
- [R0_01](R0_01.md)
- [R0_02](R0_02.md)
- [R0_03](R0_03.md)
- [R1_01](R1_01.md)
- [R1_02](R1_02.md)
- [R1_03](R1_03.md)
- [R2_01](R2_01.md)
- [R2_02](R2_02.md)
- [R2_03](R2_03.md)
- [R2_04](R2_04.md)
- [R2_05](R2_05.md)
- [R2_06](R2_06.md)
- [R2_07](R2_07.md)
- [R2_08](R2_08.md)
- [R2_09](R2_09.md)
- [R2_10](R2_10.md)
- [R2_11](R2_11.md)
- [R2_12](R2_12.md)
- [R2_13](R2_13.md)
- [R3_01](R3_01.md)
- [R3_02](R3_02.md)
- [R3_03](R3_03.md)
- [R3_04](R3_04.md)
- [R4_01](R4_01.md)
- [R4_02](R4_02.md)
- [R4_03](R4_03.md)

No ZIP final, `COMMITS_27.csv` informa os 27 SHAs, inclusive o commit final. O pacote também contém capturas, resultados dos testes, manifesto e patch da campanha. Bancos, credenciais, sessões e arquivos oficiais brutos foram excluídos. A fonte executável permanece na branch local `checkpoint/irps-historico-12-meses-2026-10-23`.
