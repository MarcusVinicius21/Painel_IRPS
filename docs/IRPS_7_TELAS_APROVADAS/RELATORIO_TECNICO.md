# Implementação das telas aprovadas do IRPS

## Resultado

A jornada foi implementada no frontend React existente, com PostgreSQL e APIs FastAPI: dashboard, seleção do item, histórico municipal, planejamento, preparação documental, manifestações e consolidação. A sétima referência orienta os componentes compartilhados e a visão de seleção, sem criar outro aplicativo. O fluxo demonstrativo foi executado no navegador com dados fictícios identificados, catálogo real importado e estados honestos para o histórico ainda não vinculado.

**Validação:** 185 testes Python e 200 subtestes aprovados; 25 testes Playwright aprovados; build aprovado; migração até `0012` aplicada duas vezes em banco novo descartável. Após a revisão do texto do PDF, os 31 testes dirigidos de documentos, rascunhos e manifestações passaram novamente. As duas quantidades de testes Python se sobrepõem: não devem ser somadas.

## Auditoria inicial e preservação

Raiz: `Painel_IRPS`. Branch inicial e final: `feat/cobertura-historica-catalogo-inteligente`. HEAD: `e65375414792d4baef6ec1eaa6d7384c398448ca`. Remote: `git@github.com:MarcusVinicius21/Painel_IRPS.git`. Nenhum `AGENTS.md` aplicável foi encontrado. Não houve commit, push, merge, alteração de PR ou deploy.

O estado inicial continha código não commitado da Diretriz Mestra V2 e das correções anteriores. Seus arquivos foram inventariados antes das edições. Os 63 arquivos de código/evidências do ZIP anterior correspondiam aos hashes do estado local inicial. Nenhum patch desse ZIP foi aplicado. Os originais do pacote visual foram copiados byte a byte para documentação; os arquivos de origem permanecem intactos.

Os oito módulos em `backend/irps_core` continuam com os hashes iniciais. Nenhum arquivo preexistente foi excluído. O inventário final discrimina os arquivos desta rodada, os anteriores preservados e o diff acumulado. Alterações em arquivos já modificados foram integrações pontuais sobre o conteúdo encontrado.

O pacote contém um diff desta rodada e outro acumulado contra HEAD. `BASES_DO_DIFF.json` registra a exceção de `Opportunities.tsx`: seu checkout inicial tinha finais de linha mistos e o diff textual usa o objeto Git normalizado. O hash físico inicial permanece registrado, sem alegação de reconstrução byte a byte desse checkout. O arquivo atual completo também está no overlay de código.

## Funcionalidades reaproveitadas

Catálogo nacional versionado e paginado; produtos canônicos com revisão de equivalência; histórico por município; comparação de fases e unidades; cobertura por evidência; oportunidades; cenários e cálculo V4; parâmetros dos modos A/B; gerador de seis variantes de minutas; preservação e revisão de documentos; registro versionado de sugestões/comunicações/manifestações; autenticação, permissões, isolamento por organização e exportação protegida.

O planejamento V4 continua atendendo cenários com múltiplos itens e até 118 participantes. A jornada da diretoria usa um item específico por estudo, conforme o contrato anterior. Não foi introduzido um agrupamento de vários estudos em uma única IRP multiitem.

## Implementado e testado nesta rodada

- **Dashboard executivo:** três consultas independentes para catálogo, histórico oficial e operações da organização. Mostra códigos importados, vínculos revisados, municípios com registros, eventos mensais por fase, itens observados, tarefas de coleta, estudos e atividades. Uma falha no catálogo não elimina os dados históricos. As barras contam registros; não representam consumo, demanda futura ou compras independentes.
- **Jornada em etapas:** navegação explícita e retorno, seis subetapas na área existente, mantendo estudo/código/versão. Os documentos e as operações ficam vinculados ao estudo persistido. A seleção inicial e o histórico possuem subetapas próprias.
- **Progresso incompleto:** botão “Salvar progresso”, recuperação após recarregar, snapshots imutáveis e controle de sucessão. Unidade e justificativas podem estar incompletas. A conferência técnica não é restaurada como aprovada; o rascunho não cria entradas V4 nem manifestações.
- **Inteligência:** busca por descrição ou código, CATMAT/CATSER, situação, grupo/classe, paginação de servidor, seleção municipal e fase, períodos de 1/3/6/12 meses, histórico anual, preços documentados e fontes. Sem vínculo técnico, exibe informação insuficiente. Não cria médias ou percentuais de recorrência sem denominador comprovado.
- **Planejamento:** matriz municipal com histórico, V4, sugestão conferida e confirmação em colunas distintas. Meta preliminar editável, justificada e independente. Registro de sugestão reutiliza a trilha de auditoria existente. Os modos A/B abrem o módulo V4 original. O cenário correto é restaurado pelo estudo, inclusive após recarregar a rota V4.
- **Preparação:** formulário, prévia central e conferência lateral. A prévia usa as mesmas seções do gerador. Seis variantes, seleção municipal de formulário, referência/prazo/entrega, histórico de minutas e DOCX/PDF. Mudanças de cenário ou manifestações tornam a minuta anterior desatualizada e exigem nova conferência explícita antes da exportação.
- **Manifestações:** filtro e detalhe municipal, prova anexada no IRPS, conferência documental expressa, canal/data/responsável/competência, quantidade e estados distintos. O servidor continua exigindo os documentos e as permissões necessários. Ausência de resposta não vira recusa.
- **Consolidação:** soma somente confirmações vigentes. Recusa documentada resolve o convite sem adicionar quantidade. Alterar a revisão do comprovante invalida tanto a confirmação quanto a recusa anterior. Mostra total conhecido parcial e mantém o total consolidado indisponível quando há pendências.
- **Relatórios:** Excel com abas por município, item, pendências e contexto; PDF; dossiê com estudo, manifestações, minutas atuais e quadros de consolidação XLSX/PDF. Células textuais potencialmente interpretadas como fórmula são escapadas. O dossiê não embute originais recebidos nem consulta simulações comerciais privadas.
- **Interface:** tokens compartilhados, sidebar clara, identidade do cabeçalho institucional fornecido, azul, tabelas compactas, foco visível, mensagens humanas e adaptação mobile com cartões e navegação inferior. Nenhuma fotografia de produto foi inventada.

## Dados efetivamente disponíveis

| Universo fornecido | Códigos armazenados e indexados | Cobertura de consulta dos arquivos | Códigos com histórico oficial tecnicamente vinculado |
|---|---:|---:|---:|
| CATMAT | 345.575 | 100% | 0 · 0% |
| CATSER | 3.104 | 100% | 0 · 0% |
| Total | 348.679 | 100% | 0 · 0% |

Hashes dos CSVs atuais foram conciliados com os snapshots importados e suas contagens. Os catálogos incluem códigos ativos e inativos. Esses percentuais se referem aos arquivos fornecidos, não à atualização corrente de todo o catálogo nacional nem à cobertura das compras brasileiras.

Existem fatos oficiais em Alfenas/MG, Ipatinga/MG e Turmalina/MG: 14 cabeçalhos publicados, 507 linhas de itens publicados, 126 resultados homologados e 1 cabeçalho de contrato. **Não são 648 compras independentes.** Publicação, resultado e contrato não foram somados para calcular demanda. Nenhuma coleta oficial nova foi feita nesta rodada; foram consultados os registros já armazenados.

Não foram criados vínculos por semelhança de descrição. O relacionamento existente exige produto canônico revisado, par exato de item/versão e conferência da unidade/especificação/embalagem. Sem correspondência determinística comprovada, a revisão humana permanece necessária.

## Migração e segurança

`0012_director_progress.py` acrescenta somente a tabela de progresso, com RLS forçada, permissões SELECT/INSERT, snapshots imutáveis e sucessão única para detectar concorrência. Não remove tabelas ou registros. A migração foi aplicada nos bancos locais autorizados e validada em um banco novo descartável, sem downgrade destrutivo.

Os testes cobrem isolamento entre organizações, leitura/exportação permitida ao perfil de consulta, bloqueio de escrita sem permissão, documentos privados excluídos, concorrência e invalidação após mudança de contexto. A role da aplicação não recebeu privilégios adicionais de administração. Uma consulta de auditoria à tabela de migrações foi corretamente negada à role da aplicação; a conferência de versão foi feita separadamente em leitura pelo proprietário local autorizado.

A varredura de segredos abrange o diff e arquivos não ignorados; não certifica a ausência de todo tipo possível de dado sensível. O ZIP é montado por seleção explícita e conferência de hashes/CRC, excluindo banco, `.env`, configurações reais, sessões, uploads, dependências e logs brutos. Não foram alterados Radar, skills privadas ou credenciais. Auditorias de dependências não apontaram vulnerabilidades conhecidas nas dependências Python fixadas nem nas dependências frontend de produção consultadas.

## Falhas encontradas e corrigidas

Foram preservados os resultados das tentativas em execução local. Houve build intermediário sem o CSS ainda criado, uma restrição TypeScript em ramo já estreitado, um fixture não importado e uma expectativa incorreta de teste sobre exportação pelo perfil leitor. Foram corrigidos antes da validação final.

O navegador revelou o uso de data UTC como “hoje” no calendário brasileiro, estrutura semântica inválida dos indicadores, contraste de etapas indisponíveis, seletores que ainda esperavam a antiga Home e sobreposição da mensagem ao assistente em mobile. As correções foram verificadas em nova execução. A última revisão documental substituiu um booleano técnico por “sim/não” no PDF, com regressão dirigida.

O PostgreSQL local iniciou com recuperação automática após encerramento anterior; foi aguardada sua conclusão. Não houve reinicialização do cluster, exclusão de arquivos ou recriação do banco existente. O timeout inicial do `pg_ctl` não foi tratado como prova de falha permanente: a disponibilidade foi conferida depois da recuperação.

## Limites e itens não implementados

1. Não há cobertura de compras por código CATMAT/CATSER comprovada enquanto faltarem vínculos técnicos revisados. Gráficos municipais de produtos, médias, recorrência e projeções podem permanecer indisponíveis por esse motivo.
2. O novo estudo da diretoria e sua consolidação são de um item por vez. Agrupamento de múltiplos estudos em um processo/documento multiitem e consolidação por lotes ainda não foram implementados nesta jornada; o V4 multiitem anterior foi preservado.
3. Não foram criados novos conectores, coleta nacional, Banco de Preços comercial, envio de comunicações, assinatura, protocolo, publicação ou homologação. Atos externos são apenas registrados mediante prova.
4. Modelos e cláusulas continuam sujeitos à validação institucional/jurídica. O número interno do estudo não é número oficial de IRP. Nenhuma autoridade ou aprovação foi inventada.
5. A aparência foi comparada com as sete referências, mas não é reprodução pixel a pixel. Componentes, proporções e estados foram adaptados aos dados disponíveis, à acessibilidade e ao mobile. Não há percentual artificial de fidelidade visual.
6. Os testes comprovam o ambiente local. Não equivalem à homologação institucional, auditoria de invasão independente, teste com leitores de tela humanos ou operação em produção.

## Evidências

Consulte [QA](QA.md), [matriz funcional](MATRIZ_FUNCIONAL.md), [relatório visual](RELATORIO_VISUAL.md), [galeria](galeria.html), [contratos e execução](CONTRATOS_E_EXECUCAO.md) e os arquivos em `evidencias/`. O inventário Git final e os hashes V4 acompanham a entrega.
