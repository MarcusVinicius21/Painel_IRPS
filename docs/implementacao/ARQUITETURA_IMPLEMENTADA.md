> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Implementação entregue

Esta entrega amplia o Projeto Mestre por código executável. Os documentos originais permanecem em suas pastas. O escopo completo anterior não é rebatizado como concluído: somente os módulos abaixo estão implementados.

## Componentes e responsabilidades

| Componente | Código | Responsabilidade real |
|---|---|---|
| Aplicação HTTP | `backend/app/main.py` | 47 operações, autenticação, erros redigidos e contratos |
| Sessão e acesso | `security.py` | Verificação RS256/JWK; vínculo ativo no banco; classe/permissão; CSRF e revogação |
| Banco | `db.py`, cinco migrações | Transação por organização com `set_config(..., true)`, SQL parametrizado, RLS e evidências |
| Planejamento | `scenarios.py` | Versões, concorrência, adapters V4 e persistência das linhas |
| Comercial privado | `scenarios.quote` | `calculate_quote`, revisões e acesso exclusivo da empresa |
| Fontes | `sources.py` | URLs fixas, GET limitado, timeout, cache curto, pausa Retry-After, jobs e gravação |
| Documentos | `documents.py` | Propostas com localização e revisão, sem execução de instruções |
| Assistente | `assistant.py`, `schemas.ToolCall` | Intenção por regras, argumentos fechados, autorização e fatos do banco |
| Exportações | `exports.py` | CSV/XLSX/PDF de cálculo/versão, arquivo e autorização |
| Observatório | `frontend/src/api.tsx`, `connected/` | Sessão do serviço; carregamento/erro/vazio; apresentação, sem fórmulas de cálculo |

## Modelo de dados real

30 tabelas, 55 chaves estrangeiras e 26 tabelas com RLS habilitada e forçada. O usuário da API é `irps_app`, sem superusuário e sem bypass de RLS. O proprietário só aplica migrações e prepara dados de teste.

- Identidade: `organization`, `actor`, `membership`, `auth_session`.
- Cadastro: `municipality`, `item_version`, `official_catalogue_entry`.
- Evidência: `source_observation`, `buyer`, `procurement_fact`, `coverage`, `source_backoff`.
- Cenário: `scenario`, `scenario_version`, `scenario_participant`, `scenario_item`, `calculation`, `calculation_line`.
- Comercial: `private_quote`, `quote_version`.
- Documentos: `document`, `extracted_document`, `artifact`.
- Trabalho e IA: `job`, `ai_session`, `ai_turn`, `ai_cache`, `ai_reservation`.
- Atividades: `audit_event`, `watch`.

`BANCO_IMPLEMENTADO.mmd` deriva do PostgreSQL executado. Os tipos e constraints completos estão em `001_schema.sql` e nas revisões `0002`–`0005`; não são apenas uma proposta de modelo.

Chaves de cenários, versões, linhas, documentos e artefatos incluem organização. FKs compostas impedem referências cruzadas nessas relações. Fontes oficiais são públicas entre organizações; dados sintéticos e internos permanecem isolados. CNPJ identifica o órgão/unidade; IBGE identifica o território. Um órgão federal sediado numa cidade não é a prefeitura.

## Matemática preservada

Importação direta dos oito módulos de `docs/IRPS_ENTREGA_FINAL/nucleo_v4/irps_core`. `core_hash()` registra o conjunto executado em cada cálculo. Não existe um segundo motor financeiro no frontend ativo.

| Operação | Função V4 utilizada | Proteção adicional do adapter |
|---|---|---|
| Necessidade individual | `calculate_need` | Estoque e recebimentos precisam estar conhecidos; ausente não vira zero |
| Consolidação individual | `allocate_independent` | Seleção explícita e mesma unidade/período/versão; retirada não redistribui |
| Quantidade global | `allocate_total` | Meta e justificativa; pesos/fontes/pisos/tetos; confirmação ligada à seleção |
| Valor estimado | `calculate_tender_value` | Preço da mesma unidade e versão, fonte HTTPS e data válida |
| Resultado comercial | `calculate_quote` | Área privada, números decimais e organização empresarial |
| Resumo histórico | `summarize_history` | Fase, item, versão, unidade, anos e municípios compatíveis |
| Sinal futuro | `forecast_from_history` | Pelo menos três anos; fase compatível; não equivale a consumo ou aprovação |

Valores são `Decimal`; colunas físicas/monetárias usam `NUMERIC`. A API apresenta decimais como texto para preservar ida e volta. `Intl` só formata na tela. O adapter verifica limites de armazenamento, sem alterar as fórmulas do V4.

No preço, o `validated=True` enviado ao V4 significa que os campos exigidos passaram na validação estrutural. Não comprova que um usuário juntou uma pesquisa oficial suficiente. A referência salva continua uma proposta de planejamento; anuência, dotação, competência e aprovação de despesa não são inferidas.

## Versões e concorrência

Alterar cenário exige `If-Match`. Ausência: 428. Versão obsoleta: 409. A linha principal é bloqueada transacionalmente, a versão é inserida e a revisão corrente avança. `scenario_version`, cálculos/linhas, versões comerciais, originais, extrações, artefatos e auditoria não podem ser alterados pelo usuário da API.

Modo A conserva as necessidades dos municípios restantes. Modo B usa uma impressão da seleção, insumos e critérios; mudanças invalidam a confirmação. Quantidades impossíveis são recusadas pelo V4. Revisão interna não emite ato oficial. Recuperar versão insere outro rascunho, preservando a origem.

## Contratos externos e internos

`OPENAPI_IMPLEMENTADO.json` foi obtido do FastAPI em execução. Pedidos usam Pydantic com campos extras proibidos. Ferramentas também recusam filtros incompatíveis com a operação. Não recebem SQL, URL livre, código ou papel/organização como autoridade.

Jobs têm organização, ator, argumentos, estado e chave de idempotência. A mesma chave com outro conteúdo retorna 409. O worker revalida o vínculo ativo e a permissão. Consultas incompletas permanecem registradas; há retomada explícita e limitada por script. Isso ainda não é um sistema distribuído de filas.

Uma revisão PNCP cria outro fato, ligado ao anterior; repetição exata de versão conhecida não duplica nem reativa uma versão antiga. Atualização de fatos públicos inicialmente gravados por outra organização aguarda um coletor centralizado de produção, em vez de conceder bypass à API.

## IA desligada para serviços pagos

O assistente executa somente funções autorizadas. A sessão/cache inclui organização, ator, papel e revisão de fontes; o vínculo é revalidado antes do cache. Perguntas ambíguas pedem esclarecimento. Papel higiênico não é papel A4; cidade/obrigação não são substituídas. Pagamento líquido considera estornos da mesma obrigação e não comprova consumo.

Há reserva transacional de orçamento com bloqueio no PostgreSQL. Valores incertos continuam ocupando o limite. A reconciliação real e as quotas distribuídas por usuário ainda dependem da integração do provedor. Nesta rodada, `/assistant/external` sempre recusa; não há credencial nem cobrança.

## Documentos e recuperação

PDF textual: até 50 páginas. DOCX/XLSX: ZIP limitado por tamanho, entradas e proporção; caminhos inseguros, macros, objetos e vínculos externos são recusados. Planilhas: até 20 mil células preenchidas. Arquivos: 2 MB. Texto: 500 mil caracteres.

Fórmulas permanecem texto, com aba/célula e valor proposto ausente. DOCX usa parser XML protegido. CSV não executa fórmulas; exportações neutralizam prefixos perigosos em células textuais. Cada original tem digest, armazenamento por organização e abertura autorizada. Revisão cria nova extração; não altera automaticamente quantitativos. Antivírus e isolamento de parser são próximos requisitos de produção.
