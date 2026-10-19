# Arquitetura final e contratos de integração

## Fronteiras executáveis

O protótipo entregue é React/TypeScript/Vite com dados tipados, adaptador decimal de demonstração e persistência local com chave `irps-final-demo-v1`. Não consulta órgãos públicos, não autentica usuários e não aplica migrações. Manrope local e Lucide mantêm a direção Observatório. Custos artificiais usam armazenamento separado, `irps-final-quote-demo`, e nunca entram no objeto de cenário público. Esta separação organiza a demonstração; não protege segredos no navegador.

Para produção, a decisão de arquitetura é manter o núcleo Python auditado e colocá-lo atrás de serviços de domínio. React envia comandos, não resultados oficiais. API Python/FastAPI é a proposta compatível com o núcleo; PostgreSQL conserva fatos, versões e acesso; armazenamento de objetos conserva originais e relatórios; trabalhadores processam consultas, extração e exportações. Essa arquitetura é especificação consolidada, sem infraestrutura instalada nesta fase.

## Componentes e responsabilidades

| Componente | Entrada / responsabilidade | Saída / contrato | Fronteira de confiança |
|---|---|---|---|
| Interface | Pesquisa, filtros, seleção e comandos; recupera contexto | Estado acessível e recorte explícito | Nunca confiar no perfil, preço validado ou Q enviados pelo cliente |
| Identidade e autorização | Sessão validada, organização e memberships | Escopo por ação/recurso/cidade e classe | Antes de buscar/serializar; admin não herda acesso privado |
| Serviço de consultas | Item/versão, órgão, município, fase e janela | Fatos elegíveis e cobertura | Página parcial não vira abrangência total |
| Adaptador por fonte | Contrato e limites do provedor | Observação bruta imutável e metadados | TLS estrito, URLs permitidas, sem executar anexos |
| Normalização | Original, chave de evento, item/unidade e órgão | Fato canônico e relação à observação | Sugestão de equivalência exige revisão |
| Reconciliação | Obrigações, contratos, aditivos, parcelas e estornos | Eventos sem duplicação e saldo por fase | Não somar estimado, contratado e pago como três despesas |
| Serviço de necessidade | Insumos autorizados e método versionado | Resultado V4 com memória e pendências | Ausência de estoque não usa default zero |
| Serviço de cenários | Participantes/itens, versão esperada e comando | Nova versão imutável e diferenças | Transação e idempotência; revisão da derivada invalidada |
| Serviço privado | Custos e hipóteses da empresa autorizada | Receita, lucro, margem e equilíbrio | Organização empresarial; sem derivação para consulta pública |
| Documentos e extração | Originais classificados, parser e página/célula | Proposta revisável e confiança por campo | Antivírus/limite/sandbox; OCR/IA não aprovam atos |
| Relatórios | Snapshot autorizado e classificação | Artefato da mesma versão, com expiração | Revalidar acesso na geração e entrega; revogação |
| Operação | Jobs, tentativas, custo, tempo e cobertura | Retomada, métricas e alertas operacionais | Não registrar custos integrais ou documentos sensíveis nos logs |

## Caminho de um comando

1. Autenticar e autorizar o sujeito, organização, recurso e ação no serviço.
2. Validar schema, identidade oficial, unidade, horizonte, entradas e versão esperada.
3. Obter snapshot de evidências, método, preços e participantes na mesma transação lógica.
4. Invocar funções puras V4; conferir precisão, invariantes e limites.
5. Gravar versão, resultados e pendências. A observação anterior permanece imutável.
6. Responder resultado completo, parcial ou tarefa assíncrona identificada. A interface não anuncia sucesso antecipado.
7. Relatórios referenciam exatamente esse snapshot; geração não recalcula com fontes mais novas sem criar versão.

## Semântica de fato e reconciliação

Chave mínima: provedor + identificação externa do evento + linha + fase + versão. Um instrumento pode ter observações retificadas. Uma obrigação liga contrato, aditivo, pedido, entrega, empenho, liquidação, parcela e estorno. `supersedes` substitui uma versão; `increments` acrescenta parcela; `reverses` desfaz evento; `references` não agrega. Relações conflitantes exigem revisão, preservando ambos os originais.

Órgão comprador tem CNPJ e unidade própria; município é território; participante tem anuência específica. Compras UNIFAL/Alfenas não são da prefeitura. Sede territorial CONSORMULTI não replica o valor por todos os participantes. Datas de evento, competência, publicação, atualização da fonte e consulta são campos distintos.

## As 16 fontes e seu estado

O inventário integral foi reaproveitado em [fontes/FONTES_CONTRATOS.csv](fontes/FONTES_CONTRATOS.csv). Os estados são do estudo de 18/10/2026, sem nova pesquisa funcional. Nenhum conector produtivo está ativo.

| Fonte | Domínio e semântica | Prova reaproveitada | Contrato para integração |
|---|---|---|---|
| PNCP | Processo, itens, estimativas, resultados, documentos, contratos | Sete processos, 44 itens em primeiras páginas e quatro resultados | Órgãos, janelas/páginas, retificações, vínculo ao contrato e cobertura |
| Compras.gov.br | CATMAT/CATSER, UASG e preços por conjunto | Dez materiais e dez serviços; uma consulta de preço vazia | Apresentação/unidade, códigos e registros comparáveis; vazio não é ausência geral |
| IBGE | Identidade e indicadores em competências próprias | 118 identidades resolvidas | Cadastro nacional extensível; população exige coleta própria por ano |
| INEP | Matrícula/escola por rede/etapa/ano | Documentação | Edição, dicionário, recorte e dupla contagem; não inferir pessoa/necessidade universal |
| SICONFI | Contas agregadas de ente e competência | Uma linha cadastral | Demonstrativos; não inferir saldo por item |
| TCE-MG | Despesas/contratos da jurisdição | Bloqueio de validação TLS no cliente do estudo | Corrigir confiança sem desativar TLS; amostra conciliada |
| TCE-RJ | Despesas/contratos conforme conjunto | Documentação | Entidade/competência e vínculo contábil |
| Portais municipais | Contratos, orçamento e execução quando publicados | Página de Ipatinga | Inventário por fornecedor/órgão, exportação, termos e recorte |
| Transferegov | Instrumentos/execução de transferências | Documentação | Convenente, fase e vínculo; transferência prevista não é saldo livre |
| Diários oficiais | Atos por edição/data/página | DOU documental | Mapear MG/RJ/local; ato específico e versão; DOU não cobre tudo |
| BPS | Preços/registros de saúde | Página oficial | Linhas, apresentação, fase, ano e condições |
| CMED | Limites regulados de medicamentos | Página oficial | Planilha/vigência/aplicabilidade; não é preço pago |
| SINAPI | Custos/composições de engenharia | Página oficial | UF/mês/regime e composição; Q vem do projeto |
| SICRO | Referências rodoviárias | Página oficial | Objeto/unidade/competência compatíveis |
| SIOPS | Contexto financeiro da saúde | Página oficial | Relatório/competência; não saldo livre do medicamento |
| SIOPE | Contexto financeiro educacional | Página oficial | Relatório/competência; não estoque escolar |

## Máquina de coleta e recuperação

`NAO_CONSULTADO → EM_COLETA → CONSULTADO_COM_RESULTADOS | CONSULTADO_SEM_RESULTADO_NO_RECORTE | PARCIAL | FONTE_INDISPONIVEL`. Sigilo, retificação, incompatibilidade e jurisdição são atributos semânticos adicionais; não substituir a cobertura por um booleano.

Cada execução guarda cidade/órgãos, janela, objeto/fase, consultas, páginas, cursor, adaptador, data do último sucesso, erros e cobertura atingida. Timeout/429/5xx podem gerar tentativas limitadas com espera exponencial, jitter e `Retry-After`; falha de TLS exige correção, nunca desativação. Cotas concretas são descobertas por fonte e não inventadas. Repetição usa idempotency key e checkpoint; não duplica observação ou zera histórico anterior. Atualização em segundo plano propõe nova versão, sem alterar uma aprovação vigente.

## Contratos HTTP de produção

Detalhes em [contratos/openapi.json](contratos/openapi.json). Convenções: IDs estáveis; `quantity` e `price` como strings decimais ou null; UTC para instantes e data civil separada; BRL identificado; paginação por cursor; `coverage`, `as_of`, `source_snapshot`, `notices` e versão acompanham dados. Classe de acesso e organização são validadas no serviço. Cliente não escolhe tenant por um campo não verificado.

- Consultas: `GET /items`, `/municipalities`, `/buyers`, `/facts`, `/obligations/{id}/events`, `/coverage`, `/opportunities`.
- Planejamento: `POST /scenarios`; `PUT /scenarios/{id}/draft` com `If-Match`; `POST /calculate`, `/allocations/validate`, `/versions`, `/reviews`, `/approvals` e `/exports` sob cenário.
- Documentos: criar lote, anexar original, obter campos extraídos e registrar revisão. Não promover texto de IA diretamente a fato.
- Privado: `POST /private/quotes`, versões e exports somente da organização empresarial. Sem inclusão no payload de consulta pública.
- Governança: memberships, métodos e auditoria conforme papel; administrador sem competência administrativa não aprova.

Erros: 400 formato; 401 sessão; 403 escopo; 404 sem revelar existência restrita; 409 versão/conflito; 422 inviabilidade ou dado incompatível; 429 limite; 503 fonte/tarefa indisponível. Resposta traz código técnico para administradores e mensagem humana/ação para o cliente. Repetição de comando com a mesma chave retorna a mesma operação, sem novo ato.

## Segurança, retenção e operação

Separar público, planejamento interno e empresa privada, inclusive origens, cache, assistente, relatórios e arquivos. RLS complementa autorização do serviço; não substitui identidade. Objetos têm classe, organização, expiração e checagem no download. Revogar usuário/ato deve bloquear trabalhos pendentes e artefatos ainda acessíveis. Auditoria append-only com detalhes minimizados; backup precisa ser restaurado num teste de recuperação antes de operação real.

Carga é N cidades × M itens × versões × fontes. Paginação/virtualização reduz DOM, não o consolidado. Filas e cache dependem de custo medido; metas locais propostas do Gate B (filtro p95 ≤200 ms, detalhe já carregado ≤500 ms) são metas de engenharia, não benchmarks comprovados desta entrega. Custos, retenção, licenças e disponibilidade são decisões operacionais por conjunto.
