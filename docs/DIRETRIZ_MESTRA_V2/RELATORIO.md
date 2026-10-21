# Diretriz Mestra V2 — implementação local para revisão

Referência: 20 de outubro de 2026. A aplicação existente foi ampliada no próprio repositório. Há código, persistência PostgreSQL, interface Observatório, minutas editáveis e testes executados. Esta entrega não declara implantação ou homologação jurídica.

## Estado inicial e preservação

- Raiz: `Painel_IRPS`.
- Branch: `feat/cobertura-historica-catalogo-inteligente`.
- HEAD: `e65375414792d4baef6ec1eaa6d7384c398448ca`.
- O remote SSH confirmou o mesmo HEAD dessa branch durante a rodada. A CLI `gh` não estava disponível nesta sessão; não foi feita nova leitura autenticada dos comentários do PR. Nenhuma informação remota foi alterada.
- Não foi encontrado `AGENTS.md` nos caminhos aplicáveis inspecionados.
- O diff local anterior de catálogo, cobertura, planejamento e testes foi mantido e incorporado. Não houve checkout, reset ou limpeza de trabalho anterior.
- Os oito arquivos de `backend/irps_core` mantêm os hashes registrados. Autenticação, permissões e RLS permanecem ativos. Itens internos de planejamento passaram também a ter escopo de organização.
- Nenhum commit, push, merge, deploy, serviço pago ou alteração do Radar foi executado.

## Entregas funcionais

| Fase | Resultado verificado | Limite prático |
|---|---|---|
| F0 | Branch, HEAD, diff, arquivos acessíveis, núcleo e anexos inventariados | A referência ao PR #2 continua histórica; não houve atualização do PR |
| F1 | Importação integral CATMAT/CATSER, snapshots imutáveis, checksum, reconciliação e busca paginada | Origem corrente/licença dos CSVs fornecidos ainda precisa de certificação; sem download recorrente |
| F2 | Vínculo humano explícito entre snapshot/código e produto canônico oficial revisado | Os fatos PNCP locais não trazem código CATMAT/CATSER confirmado. Não criamos vínculos por semelhança nem equivalências fictícias |
| F3 | Coletores, checkpoints, inventário e provas anteriores reaproveitados; cópia local dos fatos existentes | Sem coleta nacional nova; cadastro operacional ainda contém os 118 municípios iniciais |
| F4 | Nova área integrada “Inteligência e planejamento”: catálogo, municípios, UF do cadastro, fase, período, histórico por município e janelas 1/3/6/12 meses | Órgão/CNPJ, modalidade e fonte continuam nas áreas anteriores; ainda não estão todos reunidos nesta nova tela |
| F5 | Área Oportunidades e suas revisões anteriores preservadas e acessíveis | Sem nova fórmula de ranking ou previsão baseada no catálogo importado |
| F6 | Estudo imutável vinculado ao cenário, meta preliminar separada, contexto/evidências, V4 existente e sugestões municipais independentes | Estudo desta tela parte de um item; mudanças relevantes exigem novo estudo/conferência. Nenhuma meta é rateada automaticamente |
| F7 | Prévia e exportação de seis tipos de minuta em DOCX/PDF, bloqueio de incoerências conhecidas e de contexto alterado | Modelos jurídicos, lotes e numeração oficial não foram aprovados. Os documentos são minutas preparatórias, sem cláusulas jurídicas automáticas |
| F8 | Sugestões, comunicações, manifestações e comprovantes de atos externos com versões e responsáveis | Somente registro interno; nenhum envio, assinatura ou publicidade é realizado pelo IRPS |
| F9 | Dossiê ZIP com estudo, evidências, registros e minutas atuais | Originais recebidos são referenciados, não incluídos indiscriminadamente. ETP/TR exigem modelos aprovados e não foram gerados |
| F10 | Testes de café, veículos, uniformes, SaaS/serviço continuado, casos adversos e fluxo desktop/mobile | Cenários e manifestações dos testes são fictícios e identificados; não constituem validação institucional de demanda |
| F11 | Índices, paginação e scripts locais reproduzíveis; busca medida sobre o catálogo integral | Não há comprovação de carga multiusuário nacional, operação contínua, backup/recuperação ou prontidão de produção |

## Catálogo importado

| Arquivo | Registros | Ativos | Inativos | Códigos duplicados | Rejeições |
|---|---:|---:|---:|---:|---:|
| CATMAT | 345.575 | 250.034 | 95.541 | 0 | 0 |
| CATSER | 3.104 | 3.022 | 82 | 0 | 0 |
| Total | 348.679 | 253.056 | 95.623 | — | 0 |

Os códigos permanecem texto, inclusive zeros iniciais. O JSON original de cada linha, grupos, classes, PDM e demais campos recebidos ficam preservados. Uma importação inválida reverte integralmente sua transação. A reimportação do mesmo checksum retorna o snapshot anterior.

O índice de pesquisa foi ajustado para acentos e caixa independentemente do locale `C` do PostgreSQL local. “CAFÉ”, “café” e “CAFE” encontram o mesmo conjunto elegível, sem alterar o texto original. A primeira versão da busca ordenava dados em excesso; a consulta final limita cada snapshot pelo índice antes de combinar as páginas. As medições finais e seus tempos estão no `demo.json`; são medições locais, não garantia de SLA.

CATMAT SHA-256: `4c8c69973d4a3130421a79f95c5a11506f7c19439d812da3bebd08d37cb6e140`.

CATSER SHA-256: `06372173e2f3fd56b311e1504a6314082459d85556e450b7fdb14d4e74adf22f`.

## Histórico público realmente disponível

A cópia local utilizada na demonstração conserva fatos oficiais previamente coletados para Alfenas/MG, Ipatinga/MG e Turmalina/MG. O inventário detalha por município, fonte, situação, datas de evento e observações de consulta.

| Provedor | Situação/nível | Fatos atuais |
|---|---|---:|
| PNCP | Publicações estimadas, cabeçalhos | 14 |
| PNCP_ITENS | Itens publicados estimados | 507 |
| PNCP_RESULTADOS | Resultados homologados por item | 126 |
| PNCP_CONTRATOS | Contrato, cabeçalho | 1 |

Esses 648 fatos **não são 648 compras independentes**. Cabeçalhos não são somados aos itens e situações diferentes não são somadas entre si. Os eventos vão de agosto de 2025 a outubro de 2026, conforme cada provedor. A presente rodada reutilizou esses dados; não realizou nova coleta PNCP nem certificou sua atualidade perante o portal.

Não há vínculo CATMAT/CATSER tecnicamente confirmado para os fatos locais. A demonstração de café usa um código real do CSV e um estudo de planejamento fictício, com histórico indisponível. Essa ausência é exibida explicitamente e não vira zero. Para apresentar histórico quantitativo desse código, é necessária uma correspondência técnica revisada aos fatos originais.

## Histórico, V4, sugestão e confirmação

O histórico mantém correspondência exata `(item_id,item_version)` no SQL antes do limite, separa fases e considera apenas fatos atuais. O limite de 20 mil fatos elegíveis gera erro explícito, nunca truncamento silencioso. Revisões são deduplicadas pela identidade do evento. Quantidades dependem de unidade, embalagem e especificação compatíveis.

As janelas partem do primeiro dia do mês correspondente, contando 1/3/6/12 meses até a data final escolhida, e respeitam o início do recorte. Totais observados são parciais. Médias mensais e percentuais de recorrência permanecem nulos quando não há denominador adequado. Cada janela informa os fatos usados; evidências exibidas têm limite explícito.

No planejamento:

- Meta preliminar: hipótese informada e justificada, sem distribuição automática.
- Necessidade V4: somente o cálculo existente com entradas suficientes e validadas.
- Sugestão: registro municipal independente, com revisão, motivo e versão.
- Confirmação: quantidade documental conferida, com responsável, competência e versão da evidência.

Mudança no cenário invalida o contexto anterior. Nova revisão do documento recebido invalida a confirmação até reconferência. Mudança nos registros documentais torna a minuta anterior desatualizada para nova exportação. Os registros antigos são preservados.

Um município sem manifestação continua pendente. O total conhecido confirmado é identificado como parcial enquanto faltarem linhas; o consolidado completo fica nulo. Não foram criados logins municipais.

## Referências e geração documental

Foram encontrados o PDF Diretriz Mestra V2 de 11 páginas, o Plano Diretor DOCX, os três formulários, os três procedimentos, Lote Único, Planilha IRP 7, os dois DOCX dentro de `IRP UNIFORMES.zip`, os CSVs e o LEIAME. A extração textual dos arquivos e o inventário de hashes estão preservados localmente; a inspeção visual integral realizada nesta rodada abrange o formulário veicular de três páginas e os exemplos gerados, não todos os documentos longos.

Achados que orientaram os bloqueios:

- IRP 010 intitulada como veículos contém plataformas, reconhecimento facial e catracas, além de justificativas incompatíveis.
- Versões SaaS usam `R$/mês` e `R$/servidor/mês` sob unidade; isso não autoriza tratá-los como quantidade física.
- Uniformes apresentam unidades em branco e textos herdados de serviços.
- O rodapé do formulário de referência contém contatos de terceiro não certificados nesta rodada.

O gerador utiliza corpo estruturado próprio e derivado, sem copiar cláusulas, assinaturas, autoridades ou números dos originais. O cabeçalho gráfico da referência é preservado na cópia DOCX; o rodapé foi substituído por identificação neutra de minuta. O PDF usa composição própria para revisão, com o mesmo conteúdo estruturado; não promete réplica gráfica do timbrado.

Há seis variantes: procedimento, formulário municipal, planilha, especificações, municípios potenciais e quadro de quantitativos. O formulário exige município do estudo. Lotes aprovados e modelos jurídicos não foram inventados. A validação automática cobre inconsistências conhecidas e exige conferência humana; não é um validador semântico ou jurídico universal.

Uma falha de interoperabilidade DOCX foi descoberta pela renderização real. O pacote passou a ser normalizado por `python-docx`, recebeu grade e dimensões de tabela e ganhou regressão de destino/sanitização. Os exemplos finais foram abertos e renderizados pelo LibreOffice, e todas as suas páginas foram inspecionadas.

## Testes e segurança

Os resultados finais são registrados nas evidências da entrega:

- Suíte Python: **180 testes e 200 subtestes aprovados** em PostgreSQL real.
- Navegador: **22 testes aprovados** no conjunto completo; a jornada da diretoria foi repetida após seus ajustes, em 390 e 1440 px.
- Build TypeScript/Vite: aprovado, com avisos existentes da dependência de ícones sobre `use client`.
- Migrações: banco local novo de 0001 até 0011, segundo upgrade idempotente e RLS forçado conferidos. Downgrade destrutivo não foi executado; as novas migrações recusam apagar evidências.
- Autenticação, isolamento, cenários, oportunidades, catálogo e V4 protegidos pelas regressões existentes.
- `git diff --check`: sem erros de whitespace.
- Auditoria do diff e arquivos novos: regras de segredo, caminhos e integridade V4, sem valores de credenciais em saída. É uma inspeção por padrões, não certificação exaustiva.
- `pip-audit` encontrou um alerta em `certifi 2026.10.18`; a dependência foi atualizada para `2026.10.19`. A execução final sobre o lock completo não encontrou vulnerabilidades conhecidas. Não foram usados tokens ou serviços pagos.

Falhas intermediárias não foram ocultadas: consulta com parâmetros vazios, pesquisa sem índice suficientemente limitado, seletores de teste que alcançavam elementos desktop ocultos no mobile, comparação textual exata inadequada, busca com acentos/locale e interoperabilidade/sanitização DOCX foram diagnosticadas e corrigidas. Os testes finais substituem esses resultados para o aceite técnico; os logs intermediários permanecem no runtime local.

As métricas de interação novas registram cliques, campos, telas e duração do percurso automatizado. São evidências de uma jornada que inclui conferência humana e exportações, não uma promessa de que todo planejamento exige apenas dois cliques.

## O que ainda não está concluído

1. Certificação de origem/licença e atualização recorrente do snapshot CATMAT/CATSER.
2. Revisão técnica dos vínculos aos fatos públicos, com unidades e especificações. A base não foi preenchida com correspondências presumidas.
3. Cadastro municipal nacional completo e ampliação reconciliada da coleta por fonte, órgão, modalidade e período. O piloto não comprova cobertura geral dos três municípios.
4. Todos os filtros analíticos reunidos na nova tela da diretoria, parâmetros por tipo complexo de objeto e estudos de vários itens nessa experiência específica.
5. Modelos jurídicos, referências legais aplicáveis, responsáveis, competência, consorciados, canais e numeração oficial validados pelo CONSORMULTI.
6. Operação nacional contínua, carga, backups, recuperação, proteção dos leitores em produção e autenticação institucional configurada.

As pendências acima não impedem a revisão do código e do fluxo local entregue. Elas impedem declarar a aplicação pronta para emitir documentos oficiais ou conhecer todas as compras municipais.

## Git e revisão

O diff reúne as cinco correções anteriores e os incrementos desta diretriz. Novos arquivos concentram catálogo nacional, estudo da diretoria, documentos, registros internos, migrações, testes e scripts. Os CSVs de grande volume, os originais institucionais, configurações reais, chaves, uploads e bancos não fazem parte do pacote de código para revisão.

As alterações permanecem locais. Commit, push e atualização do PR aguardam autorização expressa.

Na conferência final, a revisão automática da ferramenta bloqueou um comando de reinício do servidor, sem apresentar uma razão específica. Os processos existentes foram preservados. O código final e os documentos foram testados pelo serviço em execução e pela fábrica de aplicação local; o último ajuste de composição PDF requer uma próxima inicialização normal do servidor para entrar no processo já aberto. Isso não altera a persistência nem as fórmulas.
