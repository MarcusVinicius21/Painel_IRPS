# IRPS — Portfólio CONSORMULTI e histórico municipal

Rodada FCP01–FCP09 executada em sequência, em 23/10/2026 no horário de Brasília (evidências UTC também alcançam 24/10). Aplicação real verificada em **http://127.0.0.1:5298/#/portfolio**, API 5297. Mesmo banco, operador e senha existentes. Sem push, PR, merge, deploy, imagens ou envio externo de documentos institucionais.

## Entregue e demonstrado

- Vinte grupos como entrada operacional, busca nacional preservada e busca prioritária paginada por código/descrição, namespace, subgrupo, ativo/inativo e estado técnico.
- Classificação e motivos por código/snapshot, com confirmação comercial independente. Nenhum código foi rotulado como ofertado sem confirmação.
- Preços nacionais consolidados de doze meses por código; consulta demonstrada com CATMAT 463562, sem misturar com compra municipal.
- Histórico municipal local por grupo ou código vinculado, fonte, órgão/CNPJ, município, período e fase. Candidatos por descrição permanecem explicitamente sem vínculo técnico aprovado.
- Documento original acessível; quantidade/unidade, preço e valor conhecidos preservados. Fornecedores PJ somente quando resultado/contrato os documenta, sem inferir fornecimento ao CONSORMULTI.
- Comparação por identidade técnica exata e matriz de consultas por município/mês/fonte. Sem previsão, consumo presumido ou total geral de grandezas incompatíveis.
- Preferências persistidas com RLS, migração aditiva 0016, backup integral restaurado e oito módulos V4 byte a byte preservados.

## Matriz das nove tarefas

| Tarefa | Entrega comprovada | Limitação final |
|---|---|---|
| FCP01 | Baseline, ancestralidade, banco, segurança e backup restaurado | Gate inicialmente pendente, concluído antes da importação operacional |
| FCP02 | Vinte regras conservadoras, CSV auditável, matriz e negativos testados | Revisão técnica/comercial ainda necessária; termo do grupo 09 pendente |
| FCP03 | Migração/RLS, importação versionada, API e filtros persistentes | Preferência não substitui estudo formal; regra comercial não é aprovação automática |
| FCP04 | Auditoria de sete repositórios e cliente CATMAT opcional testado | Nenhum wrapper adotado; AGPL/licença ausente/chave permanecem bloqueios específicos |
| FCP05 | Histórico municipal real, matriz e lote PNCP de 24 páginas | Doze meses ainda não integralmente conciliados; vínculos de código limitados |
| FCP06 | Fontes, fallback local e estados de bloqueio expostos | Zero fatos financeiros novos de TCE/portais; exportações não aprovadas |
| FCP07 | Indicadores por identidade e fornecedores com evidência | Sem recorrência comprovada, previsão ou necessidade V4 inferida |
| FCP08 | Interface integrada, build e navegador real desktop/mobile | Revisões/dados pendentes não foram mascarados para preencher telas |
| FCP09 | 551 testes + 200 subtestes, navegador, integridade, segurança e operação local | Aceite integral de dados/fontes ainda parcial; nenhuma alegação de 100% |

O status registrado de cada commit continua PARTIAL quando seus critérios integrais não foram atendidos; isso não significa ausência de código funcional. Pendências inicialmente operacionais resolvidas depois estão identificadas, preservando o histórico dos relatórios.

## Catálogo e preços: denominadores diferentes

| Métrica | Resultado | Significado |
|---|---:|---|
| CATMAT importados | 345.575 | Códigos dos snapshots oficiais validados |
| CATSER importados | 3.104 | Códigos dos snapshots oficiais validados |
| Total disponível para consulta | **348.679 — 100% desses snapshots** | Inclui ativos/inativos; não afirma catálogo universal eternamente atualizado |
| Registros nacionais de preço | **2.078.067** | Preservados em 24 arquivos/snapshots de 12 competências |
| Códigos materiais com preço | 125.493 | Namespace de materiais |
| Códigos serviços com preço | 2.286 | Namespace de serviços; órfãos não foram reclassificados |
| Códigos conhecidos com preço | **127.779 — 36,6466% do catálogo** | Não representa cobertura de compras municipais |
| Correspondências técnicas diretas | 2.365 | Triagem técnica, sem confirmação comercial |
| Candidatos para revisão técnica | 5.552 | Não constituem equivalência aprovada |
| Indiretos / exclusões explícitas | 525 / 2.711 | Fora da seleção prioritária pesquisável |
| Confirmações comerciais | **0** | Não foram inventadas para habilitar a busca |

Classificação não abrange automaticamente todos os itens indiretamente relacionados: o restante do catálogo continua disponível no modo nacional. Matriz dos vinte grupos em FCP02_MATRIZ.md; CSV integral de triagem privado na entrega local.

## Histórico municipal efetivamente comprovado

Cadastro atual: **Ipatinga e Timóteo**, ambos MG; não existem 118 municípios confirmados no banco operacional. Há evidências dos dois, sem afirmar compras completas de nenhum deles.

- Ipatinga, prefeitura CNPJ 19876424000142: publicação 2025/164 tem Van (1 unidade; estimado R$ 298.000,00) e utilitário (2 unidades; estimado R$ 240.480,00). Resultado do utilitário: 2 unidades e R$ 219.000,00 homologados, com fornecedor identificado na fonte. Publicação e homologação não são somadas. Evidências: https://pncp.gov.br/api/pncp/v1/orgaos/19876424000142/compras/2025/164/itens e https://pncp.gov.br/api/pncp/v1/orgaos/19876424000142/compras/2025/164/itens/1/resultados .
- Timóteo, **Câmara** CNPJ 17112673000136: publicação 2025/62 tem conector RJ45 (400 unidades) e placa periférica (2 unidades). São candidatos técnicos para conferência, sem código CATMAT inventado. Evidência: https://pncp.gov.br/api/pncp/v1/orgaos/17112673000136/compras/2025/62/itens . Não são apresentados como compra da prefeitura.

Snapshot final: **1.755 versões físicas de fatos**, contra 1.642 no início. Acréscimo físico não significa novas compras distintas. Por compradores com esfera municipal declarada na fonte, no recorte outubro/2025–setembro/2026: 459 publicações, 341 linhas de itens publicadas, 96 resultados, 33 contratos e 4 instrumentos de empenho. **Essas contagens não são somáveis como compras**; revisões/documentos e identidade de processo permanecem rastreáveis.

Matriz final: **264 células município × mês × fonte**, com 161 parciais, 89 não coletadas e 14 bloqueadas. Não há denominação de cobertura municipal integral nem meses completos de mercado. As bases temporais diferem: publicação, atualização, vigência de ata e descoberta por item/contrato. O numerador/denominador de páginas é exposto somente onde verificável. O painel informa a última consulta.

## Aceite funcional, sem percentual de mercado

Checklist original de quinze critérios: **11 comprovados integralmente e 4 parciais**, sem ponderação (**73,33% dos critérios funcionais completos**). Esse percentual é do checklist, não de compras, fontes, municípios ou aceitação comercial.

Parciais: (5) vínculo técnico/humano de todo histórico com código/produto; (6) todas as fases/documentos, incluindo atas e execução financeira, plenamente navegáveis; (10) cobertura de todas as combinações de órgão/fase/fonte, além da matriz de requisições já entregue; (11) operação prioritária contínua de atualização, além da retomada limitada já comprovada. Demais critérios foram demonstrados pelos testes indicados, mantendo limitações explícitas.

## Testes e operação

- Python em QA **novo**, migração 0016: **551 testes + 200 subtestes aprovados**, zero falhas/erros/skips, 150,81 s. Depois dos últimos controles de filtro e paginação de fornecedor: oito testes direcionados aprovados.
- Build TypeScript/Vite aprovado. Avisos de bundle >500 kB e diretiva lucide registrados, não omitidos.
- Playwright/Chrome real: **3 testes aprovados**, 18,0 s na última execução; consultas oficiais locais, filtros/reload, preço nacional, fornecedor e fontes bloqueadas.
- Conteúdo novo em 320/390/1536 px: sem overflow horizontal e **zero violações axe**. Sem capturas e sem certificação pixel-perfect/global de módulos antigos.
- Migração fresca, segundo upgrade, downgrade QA vazio e reupgrade aprovados. RLS/FORCE RLS e isolamento por organização preservados; não houve seed operacional.
- Auditoria de 558 arquivos textuais rastreados: zero possíveis segredos detectados, nenhum arquivo rastreado >5 MB. Oito V4 e referências originais inalterados.
- HTTP real autenticado: vinte grupos em 0,030 s; código em 0,014 s; histórico em 0,072 s; matriz em 1,930 s. Medidas locais com banco aquecido, sem promessa de desempenho universal.

Comandos de iniciar/parar/testar e endereço observado em README.md. O script de início foi analisado e executado reutilizando os serviços; não encerrou processos antigos. Não existe coletor contínuo novo em segundo plano. O worker limitado pode retomar pelo checkpoint com backoff/trava; a fila histórica M/D/X permanece pausada.

## Pendências reais e próximo passo

1. Conferir tecnicamente candidatos e vínculos com códigos, apresentações, embalagens e unidades; registrar confirmação comercial por código sem confundi-la com pertinência técnica.
2. Confirmar o termo “casqueamento de estrada” com o gestor. Não foi convertido automaticamente em serviço genérico.
3. Avançar a coleta municipal e reconciliar períodos/órgãos/fases com limites reais da fonte. Não chamar doze competências planejadas de doze meses completos de compras.
4. TCE-MG: recurso/esquema inacessível; Timóteo/Betha: 403 anônimo; exportador Ipatinga: retornou 2010 para 2025/2026. Zero pagamentos importados dessas respostas. Não contornar restrições.
5. Manter Licitei/AGPL e repositório sem licença fora do código; chave federal somente com autorização apropriada. APIs oficiais existentes continuam prioritárias.

Todos os commits desta rodada são locais na mesma branch. Relação em FCP_COMMITS.md e ledger de entrega, com o SHA final informado ao usuário. Nenhuma informação fictícia foi introduzida no banco operacional para aparentar funcionamento.
