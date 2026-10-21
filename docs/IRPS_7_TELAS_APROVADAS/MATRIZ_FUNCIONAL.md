# Matriz das referências e da implementação

Legenda de rotas: D=`#/inicio`; I=`#/inteligencia?etapa=selecao`; H=`etapa=historico`; P=`etapa=planejamento`; R=`etapa=preparacao`; M=`etapa=manifestacoes`; C=`etapa=consolidacao`. R/M/C incluem `estudo=ID`. APIs abaixo usam o prefixo `/api/v1`.

| Referência e elemento | Componente real e rota | API ou operação | Fonte dos dados | Estado e evidência | Limite |
|---|---|---|---|---|---|
| 00 Sidebar e cabeçalho | `App` · todas | contexto de autenticação existente | Sessão e organização | Integrado; rotas desktop/mobile testadas | Identidade real deriva do material fornecido, sem copiar textos distorcidos das artes |
| 00 Etapas | `WorkflowNav` · I/H/P/R/M/C | estudo e rascunho persistidos | Backend | Integrado; percurso Playwright | Etapas são navegação, não assinatura ou aprovação oficial |
| 00 Voltar e avançar | `WorkflowFooter` | rotas com estudo/código/snapshot | Seleção e estudo | Integrado; percurso e reabertura | Requer item; etapas posteriores exigem estudo salvo |
| 00 Salvar progresso | `Director` · I/H/P | POST/GET `/director/progress` | PostgreSQL `director_progress` | Implementado e testado, inclusive recarga e conflito | Rascunho incompleto não aprova a técnica nem cria V4 |
| 00 Abrir estudos anteriores | `Director` · I | `/director/studies`, `/director/progress` | Snapshots da organização | Integrado e testado | Lista até 50 versões recentes; links diretos continuam disponíveis |
| 01 Indicadores de catálogo | `Executive` · D | `/director/dashboard/catalogue` | Snapshots nacionais | 348.679 códigos reais importados | Não significa compras; inclui ativos/inativos |
| 01 Municípios e cobertura | `Executive` · D | `/director/dashboard/history` | Fatos oficiais atuais por município | Três municípios com registros; escopo parcial | Não significa cobertura municipal completa |
| 01 Tendência visual | `Executive`/`Bars` · D | série mensal separada por fase | Registros observados | Gráfico real; filtro de fase funcional | Meses ausentes não viram zero; barras contam registros |
| 01 Produtos observados | `Executive` · D | itens/versões por fase | Fatos oficiais atuais | Links reais para pesquisa e oportunidades | Não aprova equivalência nem viabilidade comercial |
| 01 Estado das coletas | `Executive` · D | `/director/dashboard/operations` | Tarefas oficiais da organização | Estados separados; falha não vira sucesso | Tarefa concluída não comprova universo completo |
| 01 Atividades e retomada | `Executive` · D | estudos e auditoria filtrada | Organização autenticada | Integrado; isolamento testado | Exibe registros recentes, sem dados comerciais privados |
| 01 Falha secundária | `ResourceStatus` | consultas independentes | Respostas HTTP | Teste controlado 503 preserva histórico | Mensagem identifica a consulta indisponível |
| 02 Buscar materiais/serviços | `Director` · I | `/national-catalogue?q=...` | CSVs versionados e indexados | Busca real por texto/código, incluindo acentos | Origem corrente/atualização nacional não certificadas |
| 02 Categoria e situação | `Director` · I | filtros kind/active/group/classification | Campos originais do catálogo | Funcional por tipo, situação e códigos de grupo/classe | Não há novo seletor hierárquico de descrições de todas as categorias |
| 02 Paginação | `DataTable` e busca | offset/limit de servidor | Máximo 25 por busca na UI | Regressão de paginação e recortes | Não carrega todo o catálogo no navegador |
| 02 Item selecionado | `SelectedItem` · I/H/P | `/national-catalogue/{snapshot}/{code}` | Descrição e código originais | Recuperação exata testada | Ícone substitui foto inexistente; unidade exige conferência |
| 02 Municípios e datas | `Director` · H | `/director/history/{product}` | Cadastro + histórico revisado | Filtros municipais/fase/período preservados | Não agrega órgãos ou fases incompatíveis |
| 02 Vínculo técnico | `Director`/catálogo existente | `/national-catalogue/links` | Produto canônico e evidência revisada | Serviço existente integrado, sem vínculos inventados | Zero vínculos oficiais revisados no banco atual |
| 02 Documentos e preços | `HistoryDetails` · H | resposta de histórico com evidências | Fato, fonte, versão, unidade e data | Abas reais; estados sem informação | Não calcula mediana entre itens incompatíveis |
| 02 Comparação temporal | matriz e `HistoryDetails` · H/P | janelas/annual do backend | Mesmo recorte e fase | 1/3/6/12 meses e anual | Médias/projeções sem denominador permanecem indisponíveis |
| 03 Modos A/B | `Director` e `WorkflowPlanning` · P/V4 | cenários/cálculos anteriores | Núcleo V4 | Preservados e regressões executadas | Nenhuma fórmula no frontend |
| 03 Meta 200 | formulário do estudo · P | POST `/director/studies` | Hipótese explicitamente informada | Teste garante inputs/allocations vazios | Sem distribuição automática, necessidade ou anuência |
| 03 Matriz municipal | `Director` · P | histórico + `/calculations/{id}/item-lines` | Contextos identificados | V4 além da página 20 protegido por regressão | Ausência de histórico não exclui município |
| 03 Sugestão editável | `IRPRegister` view suggestions · P | operações versionadas | Quantidade e justificativa humanas | Registro e revisão testados | Não substitui V4 nem confirmação municipal |
| 03 Retorno ao estudo | `WorkflowPlanning` | seleção de cenário do estudo | `scenario_id` persistido | Teste entra no V4, recarrega e retorna | Mudança do cenário invalida contexto documental anterior |
| 04 Modelo e campos | `Director` · R | POST `/director/studies/{id}/drafts` | Estudo e pedido conferido | Seis variantes reutilizadas | Autoridades/cláusulas/número oficial exigem validação |
| 04 Prévia central | `DraftPreview` · R | GET `/irp-drafts/{id}/preview` | Mesmas seções do gerador | Conteúdo real; screenshots e teste | Paginação definitiva está no arquivo exportado |
| 04 Conferência e versões | `Director` · R | GET drafts, GET draft | Versões imutáveis | Versão anterior reaberta; stale bloqueia exportação | Nova manifestação exige reconferência da minuta |
| 04 DOCX/PDF | `DraftPreview` · R | POST `/irp-drafts/{id}/exports/{fmt}` | Modelo derivado e estudo | Gerados, baixados e renderizados para revisão | Não constituem publicação ou assinatura |
| 05 Quadro e filtros | `IRPRegister` · M | GET register | Operações vigentes por município | Tabela/cartões e detalhe funcionais | Não há conta de prefeitura |
| 05 Recebimento documental | `IRPRegister` · M | POST `/documents` | Arquivo recebido | Upload local testado | Sem envio externo automático |
| 05 Conferência da prova | detalhe municipal · M | POST `/documents/{id}/review` | Original + parecer expresso | Obrigatória antes da confirmação; teste UI | Não atesta competência institucional automaticamente |
| 05 Comunicação e manifestação | formulário interno · M | POST operations | Documento, canal, data, quantidade, competência | Estados e concorrência testados | Silêncio, prazo vencido e recusa permanecem distintos |
| 05 Histórico | detalhe municipal · M | register.history | Snapshots de operações | Versões preservadas e exibidas | Exibição limitada às últimas 500 operações; resumo vigente não truncado |
| 06 Quantitativos | `IRPRegister` · C | register | Apenas confirmações documentadas atuais | Teste de confirmação, recusa e invalidação | Pendências não são zero nem consolidado final |
| 06 Excel | painel de exportação · C | POST consolidation/xlsx | Município/item/pendências/contexto | Arquivo real e inspeção por openpyxl | Um item por estudo na jornada nova |
| 06 PDF | painel de exportação · C | POST consolidation/pdf | Mesmo resumo vigente | Extração e renderização visual verificadas | Relatório interno; sem ato oficial |
| 06 Dossiê | painel de exportação · C | POST dossier | Minutas atuais + relatórios + trilha | ZIP real, hashes e conteúdo testados | Exclui originais recebidos e custos privados |
| 06 Próximos atos externos | avisos + registro de prova | módulo existente de atos externos | Evidência anexada pelo operador | Registro protegido reutilizado | Não opera pregão, assinatura, publicação ou protocolo |

Testes centrais: `backend/tests/test_approved_workflow.py`, `test_director_workflow.py`, `test_irp_register.py`, `test_municipal_history_regressions.py`, `test_catalogue_coverage.py`; frontend `approved-workflow.spec.ts`, `director.spec.ts`, `catalogue.spec.ts`, `opportunities.spec.ts`, `real.spec.ts`, `recovery.spec.ts` e `routes.spec.ts`. A matriz não atribui teste visual pixel a pixel a comportamentos validados apenas por API.
