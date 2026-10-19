# Implementação após o aceite do projeto

## Estado de conclusão

Projeto, escopo, arquitetura, modelo, regras, design Observatório, especificação desktop/mobile e protótipo demonstrativo estão entregues nesta pasta. Este plano organiza a implementação real; não reinicia os Gates A-D nem condiciona a entrega atual ao encerramento das integrações.

As 118 identidades e a direção Observatório estão resolvidas. V4, Comando5 e Gates6R A-D foram reaproveitados. V3 permanece não localizada; não foi alegada auditoria desse pacote. Os 65 testes V4 e 16 C5 são históricos; os ensaios novos do adaptador e navegador são registrados separadamente.

## Incrementos implementáveis

| Pacote | Entrada/dependência | Entrega real e condição de conclusão | Responsável proposto |
|---|---|---|---|
| 1. Base segura e versões | Escopo atual, política de acesso e responsáveis definidos | Identidade/membership, autorização por recurso e classe, migrações, snapshot transacional e conflitos; testes negativos entre organizações e backup restaurado | Arquitetura, backend e segurança |
| 2. Fontes e catálogo | Contratos por provedor, termos e recortes permitidos | Adaptadores PNCP/Compras por janelas/páginas; fatos deduplicados, originais, órgãos e catálogo curado; matriz de cobertura rastreável | Engenharia de dados e curadoria |
| 3. Necessidade individual e preços | Estoques/entradas, métodos setoriais e pesquisa compatível | Core V4 servido por contratos, N participantes, unidades/versões, memória, preço/total, recursos e revisão competente; invariância de retirada | Domínio, municípios, técnico e financeiro |
| 4. Quantidade global fundamentada | Envelope de meta e responsabilidade administrativa | Pesos/limites, inviabilidade e mudanças versionadas; soma exata, revisão e aprovação próprias; sem meta de faturamento | Técnico e autoridade competente |
| 5. Documentos e relatórios | Leitores seguros, corpus e escopo/classificação | Extração por página/célula, confiança, revisão, lote/retomada, exportação da mesma versão e revogação | Documentos, backend e QA |
| 6. Comercial privado | Segurança empresarial, custos e hipóteses válidos | Simulação V4, versões, exportação privada e acesso negativo; conferência contábil das premissas | Empresa, contador e segurança |
| 7. Piloto e operação | Recorte real representativo e pessoas dos papéis | Compreensão, tempo humano, aparelhos, acessibilidade, carga, custo e manutenção medidos; ajustes antes de expansão | Produto, QA, operação e usuários |
| 8. Previsão ampliada | Séries completas/comparáveis e avaliação por família | Corte temporal, baseline, erros, cobertura e limitações; consumo só com prova própria | Dados e especialista setorial |

Não há prazo, tamanho de equipe, custo ou assinatura aprovados. Estimá-los por pacote após dados de volume, responsabilidade e capacidade. Cadastro aberto não implica automatizar todas as categorias com uma regra única.

## Critério de pronto por alteração

Função F e fonte identificadas; contrato validado; unidade/fase/tempo consistentes; permissão no serviço; ausência/falha/concorrência; regressão necessária do core; memória reproduzível; UI humanizada desktop/mobile; versão/exportação conciliadas; evidência e revisão competentes. Atualizar documentação e testes do incremento, sem repetir testes inalterados sem razão.

## As 21 dependências com tratamento efetivo

| ID | Estado real | O que esta entrega concluiu | O que permanece para produção / prova | Responsável futuro |
|---|---|---|---|---|
| D01 | Dependente da organização | Seleção N, participação e acesso especificados | Atos, anuência por cenário/objeto e competência | Consórcio e municípios |
| D02 | Parcial | Contratos, cobertura e estados; pesquisa sintética | Paginação, janelas e universo de órgãos comprovados | Dados |
| D03 | Não comprovado real | Fases, parcelas, estorno e ausência funcionais no exemplo | Obrigações e pagamentos oficiais conciliados | Dados e financeiro |
| D04 | Parcial | Variantes/unidades separadas e contrato de curadoria | Amostra técnica e conversões aprovadas | Curadoria |
| D05 | Dependente da organização | Fórmula, memória e edição por cidade/item | Estoques, taxas, entregas e método reais | Técnicos municipais |
| D06 | Parcial | Referência editável e totais reconciliados | Pesquisa competente e validade | Compras |
| D07 | Dependente da organização | Recurso separado, diferença e Q preservada | Documento financeiro específico | Financeiro |
| D08 | Concluído na demonstração | Modo B interativo, limites e invalidação | Meta/ato/pesos e aprovação reais | Técnico/autoridade |
| D09 | Não comprovado em produção | Espaço/avisos e custo somente fictício | Autorização, segregação, cache/exportação e revogação | Segurança |
| D10 | Parcial | Versões locais, comparação e desfazer | Banco transacional, concorrência e trilha competente | Backend |
| D11 | Concluído na demonstração | Relatórios dinâmicos da seleção/versão; sem custo público indevido | Entrega autorizada e revogação de artefatos | Backend/QA |
| D12 | Parcial | CSV real local, revisão e duplicidade; binários honestos | Leitores/OCR, corpus, confiança e retomada segura | Documentos |
| D13 | Não comprovado real | Estados de falha e conservação do exemplo | Conectores com timeout/429/TLS/checkpoint medidos | Dados/operação |
| D14 | Não validado real | Cenário estimativo e limitações explícitas | Série, backtest e precisão por família | Dados/técnico |
| D15 | Parcial | Eventos de tarefas automatizadas e resultados reais | Esforço/compreensão humanos e comparação equivalente | Produto/QA |
| D16 | Parcial no aceite humano | Design completo, galeria e revisão do executor | Pessoas, leitores de tela, motores/aparelhos e percepção | Design/usuário |
| D17 | Hipótese comercial | Público, utilidade e fronteiras do SaaS documentados | Modelo de contratação, suporte e disposição de uso/pagamento | Produto/comercial |
| D18 | Não comprovado por conjunto | Licenças/custo/retenção especificados | Direitos, política e custo medido por volume | Governança/operação |
| D19 | Dependente da origem | Casos IRP010/pregão002/004/anexos isolados | Esclarecimento ou documento oficial conciliado | Gestor documental |
| D20 | Não localizado | Ausência V3 registrada sem bloquear reuso | Pacote somente se necessário ao confronto | Gestão do projeto |
| D21 | Especificado | Arquitetura/DDL/API/handoff e demo executável | Infraestrutura, migrações, backup, carga e operação | Engenharia |

Nenhuma dependência acima impede abrir a galeria, navegar pelo protótipo ou implementar os contratos definidos. Dados ausentes bloqueiam a conclusão oficial da função afetada, não a documentação e o design.

## Decisões preservadas

Não inflar quantitativos ao retirar cidades; não inferir saldo de receita; distinguir quem compra e território; contratado não é pago/consumido; preservar documentos e skills; custos públicos e privados separados; linguagem humana; autoridade aprova; tarefas repetitivas automatizadas quando a evidência permitir. Sem implantação, commit ou push nesta entrega.
