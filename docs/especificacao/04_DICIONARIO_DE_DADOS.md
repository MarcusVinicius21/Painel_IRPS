# Dicionário relacional de implementação

DDL completo em [04_MODELO_DADOS.sql](04_MODELO_DADOS.sql), não aplicado a um banco. IDs internos UUID; código IBGE identifica município, não organização. Instantes UTC e data/competência civil separadas. NUMERIC preserva precisão; JSON guarda snapshot/atributos, não substitui FKs ou autorização.

## Grupos e invariantes

Identidade: organização, sujeito, membership, município, órgão/unidade e participação com ato. Fontes: provedor estável e observação bruta imutável. Catálogo: família aberta, item estável, versão, unidade e conversão fundamentada. Compras: instrumento/obrigação/fato/link de retificação, incremento ou estorno. Planejamento: cenário e versões com participantes/itens/linhas explícitos. Administração: método, revisão/decisão e competência separadas. Empresa: cotação privada por organização. Operação: documentos, campos, jobs, cobertura, artefatos, acompanhamento e auditoria.

## Semântica dos campos comuns

`org_id` pertence ao escopo confiável da sessão, não a um valor livre do cliente. `version` conserva snapshot; atualização cria derivada. `source_id` aponta observação preservada; `source_line`, página ou célula permitem reconstrução. `quantity/value` null significa não disponível; zero é um valor conhecido e exige fundamento. `access_class` propaga a maior restrição das entradas. `actor/reviewer` são resolvidos/validados pelo serviço. `sha256` verifica conteúdo; não concede licença ou permissão.

## organization

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `name` | `text NOT NULL` |
| `kind` | `text NOT NULL CHECK(kind IN ('government','consortium','business'))` |
## actor

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `identity_provider` | `text NOT NULL` |
| `subject` | `text NOT NULL` |

Restrições: `UNIQUE(identity_provider,subject)`.

## membership

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid REFERENCES organization` |
| `actor_id` | `uuid REFERENCES actor` |
| `role` | `text NOT NULL` |
| `scope` | `jsonb NOT NULL DEFAULT '{}'` |
| `valid_from` | `timestamptz NOT NULL` |
| `valid_until` | `timestamptz` |

Restrições: `PRIMARY KEY(org_id,actor_id,role)`; `CHECK(valid_until IS NULL OR valid_until>valid_from)`.

## municipality

| Campo | Tipo e restrições SQL |
|---|---|
| `ibge` | `char(7) PRIMARY KEY CHECK(ibge ~ '^[0-9]{7}$')` |
| `name` | `text NOT NULL` |
| `uf` | `char(2) NOT NULL` |
| `verified_at` | `timestamptz NOT NULL` |
## provider

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `name` | `text NOT NULL` |
| `base_url` | `text NOT NULL` |
| `adapter_version` | `text NOT NULL` |
| `access_contract` | `jsonb NOT NULL` |
| `terms` | `text` |
| `retention_policy` | `text` |
## source_observation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `provider_id` | `uuid NOT NULL REFERENCES provider` |
| `external_key` | `text NOT NULL` |
| `source_version` | `text NOT NULL` |
| `sha256` | `char(64) NOT NULL` |
| `url` | `text NOT NULL` |
| `object_key` | `text NOT NULL` |
| `event_at` | `timestamptz` |
| `source_updated_at` | `timestamptz` |
| `retrieved_at` | `timestamptz NOT NULL` |
| `org_id` | `uuid REFERENCES organization` |
| `access_class` | `text NOT NULL CHECK(access_class IN ('public','government_internal','business_private'))` |

Restrições: `UNIQUE(provider_id,external_key,source_version)`; `CHECK((access_class='public' AND org_id IS NULL) OR (access_class<>'public' AND org_id IS NOT NULL))`.

## original_municipality_name

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |
| `row_number` | `int NOT NULL` |
| `raw_name` | `text NOT NULL` |
| `resolved_ibge` | `char(7) REFERENCES municipality` |
| `resolution_state` | `text NOT NULL` |
| `decision` | `jsonb NOT NULL` |

Restrições: `UNIQUE(source_id,row_number)`.

## buyer

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `cnpj` | `char(14) CHECK(cnpj ~ '^[0-9]{14}$')` |
| `unit_code` | `text NOT NULL DEFAULT ''` |
| `name` | `text NOT NULL` |
| `institution_kind` | `text NOT NULL` |
| `territory_ibge` | `char(7) REFERENCES municipality` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |

Restrições: `UNIQUE(cnpj,unit_code)`.

## buyer_alias

| Campo | Tipo e restrições SQL |
|---|---|
| `provider_id` | `uuid REFERENCES provider` |
| `external_key` | `text` |
| `buyer_id` | `uuid NOT NULL REFERENCES buyer` |

Restrições: `PRIMARY KEY(provider_id,external_key)`.

## consortium_membership

| Campo | Tipo e restrições SQL |
|---|---|
| `consortium_buyer` | `uuid REFERENCES buyer` |
| `municipality_ibge` | `char(7) REFERENCES municipality` |
| `valid_from` | `date` |
| `valid_until` | `date` |
| `authorization_source` | `uuid NOT NULL REFERENCES source_observation` |

Restrições: `PRIMARY KEY(consortium_buyer,municipality_ibge,valid_from)`.

## item_family

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `name` | `text NOT NULL UNIQUE` |
| `attributes_schema` | `jsonb NOT NULL` |
## unit

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `text PRIMARY KEY` |
| `name` | `text NOT NULL` |
| `dimension` | `text NOT NULL` |
## item

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `family_id` | `uuid NOT NULL REFERENCES item_family` |
| `stable_key` | `text NOT NULL UNIQUE` |
## item_version

| Campo | Tipo e restrições SQL |
|---|---|
| `item_id` | `uuid REFERENCES item` |
| `version` | `int CHECK(version>0)` |
| `description` | `text NOT NULL` |
| `unit_id` | `text NOT NULL REFERENCES unit` |
| `quantity_step` | `numeric(24,8) NOT NULL CHECK(quantity_step>0)` |
| `packaging` | `jsonb NOT NULL` |
| `attributes` | `jsonb NOT NULL` |
| `valid_from` | `date NOT NULL` |

Restrições: `PRIMARY KEY(item_id,version)`.

## item_alias

| Campo | Tipo e restrições SQL |
|---|---|
| `provider_id` | `uuid REFERENCES provider` |
| `catalog_code` | `text` |
| `source_version` | `text` |
| `item_id` | `uuid NOT NULL` |
| `item_version` | `int NOT NULL` |

Restrições: `PRIMARY KEY(provider_id,catalog_code,source_version)`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## unit_conversion

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `item_id` | `uuid NOT NULL` |
| `item_version` | `int NOT NULL` |
| `from_unit` | `text NOT NULL REFERENCES unit` |
| `to_unit` | `text NOT NULL REFERENCES unit` |
| `numerator` | `numeric(28,10) NOT NULL CHECK(numerator>0)` |
| `denominator` | `numeric(28,10) NOT NULL CHECK(denominator>0)` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |
| `reviewer` | `uuid NOT NULL REFERENCES actor` |
| `valid_from` | `date NOT NULL` |

Restrições: `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## instrument

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `provider_id` | `uuid NOT NULL REFERENCES provider` |
| `external_key` | `text NOT NULL` |
| `buyer_id` | `uuid NOT NULL REFERENCES buyer` |
| `kind` | `text NOT NULL` |
| `published_at` | `timestamptz` |

Restrições: `UNIQUE(provider_id,external_key)`.

## obligation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `instrument_id` | `uuid NOT NULL REFERENCES instrument` |
| `item_id` | `uuid` |
| `item_version` | `int` |

Restrições: `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## procurement_fact

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `obligation_id` | `uuid NOT NULL REFERENCES obligation` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |
| `source_line` | `text NOT NULL` |
| `event_identity` | `text NOT NULL` |
| `phase` | `text NOT NULL CHECK(phase IN ('planejado','publicado_estimado','homologado','contratado','solicitado','entregue','consumido','empenhado','liquidado','pago'))` |
| `event_date` | `date NOT NULL` |
| `competence` | `text` |
| `unit_id` | `text REFERENCES unit` |
| `quantity` | `numeric(24,8) CHECK(quantity>=0)` |
| `unit_price` | `numeric(24,8) CHECK(unit_price>=0)` |
| `amount` | `numeric(24,2) CHECK(amount>=0)` |
| `currency` | `char(3) NOT NULL` |
| `org_id` | `uuid REFERENCES organization` |
| `access_class` | `text NOT NULL` |

Restrições: `UNIQUE(source_id,source_line,event_identity,phase)`.

## fact_link

| Campo | Tipo e restrições SQL |
|---|---|
| `parent_id` | `uuid REFERENCES procurement_fact` |
| `child_id` | `uuid REFERENCES procurement_fact` |
| `relationship` | `text CHECK(relationship IN ('supersedes','increments','reverses','references'))` |
| `reviewer` | `uuid REFERENCES actor` |

Restrições: `PRIMARY KEY(parent_id,child_id,relationship)`; `CHECK(parent_id<>child_id)`.

## document

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `original_name` | `text NOT NULL` |
| `sha256` | `char(64) NOT NULL` |
| `object_key` | `text NOT NULL` |
| `classification` | `text NOT NULL` |
| `mime` | `text NOT NULL` |
| `byte_count` | `bigint NOT NULL CHECK(byte_count>=0)` |
| `received_at` | `timestamptz NOT NULL` |

Restrições: `UNIQUE(org_id,sha256)`.

## extracted_field

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `document_id` | `uuid NOT NULL REFERENCES document` |
| `page_number` | `int` |
| `cell_ref` | `text` |
| `raw_value` | `text NOT NULL` |
| `normalized_value` | `jsonb` |
| `confidence` | `numeric(5,4) CHECK(confidence BETWEEN 0 AND 1)` |
| `validation_state` | `text NOT NULL` |
| `reviewer` | `uuid REFERENCES actor` |
## method_version

| Campo | Tipo e restrições SQL |
|---|---|
| `method_id` | `uuid` |
| `version` | `int` |
| `family_id` | `uuid NOT NULL REFERENCES item_family` |
| `name` | `text NOT NULL` |
| `input_schema` | `jsonb NOT NULL` |
| `formula_ref` | `text NOT NULL` |
| `rounding_rule` | `text NOT NULL` |
| `evidence` | `jsonb NOT NULL` |
| `review_state` | `text NOT NULL` |
| `reviewer` | `uuid REFERENCES actor` |

Restrições: `PRIMARY KEY(method_id,version)`.

## stock_observation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `buyer_id` | `uuid NOT NULL REFERENCES buyer` |
| `municipality_ibge` | `char(7) NOT NULL REFERENCES municipality` |
| `item_id` | `uuid NOT NULL` |
| `item_version` | `int NOT NULL` |
| `quantity` | `numeric(24,8) CHECK(quantity>=0)` |
| `usable_at` | `date NOT NULL` |
| `valid_until` | `date` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |

Restrições: `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## reference_price

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid` |
| `version` | `int NOT NULL` |
| `item_id` | `uuid NOT NULL` |
| `item_version` | `int NOT NULL` |
| `unit_id` | `text NOT NULL REFERENCES unit` |
| `value` | `numeric(24,8) NOT NULL CHECK(value>=0)` |
| `currency` | `char(3) NOT NULL` |
| `phase` | `text NOT NULL` |
| `reference_date` | `date NOT NULL` |
| `region` | `text` |
| `conditions` | `jsonb NOT NULL` |
| `observations` | `jsonb NOT NULL` |
| `method` | `text NOT NULL` |
| `reviewer` | `uuid NOT NULL REFERENCES actor` |
| `valid_until` | `date NOT NULL` |

Restrições: `PRIMARY KEY(id,version)`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## scenario

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid REFERENCES organization` |
| `id` | `uuid` |
| `title` | `text NOT NULL` |
| `current_version` | `int` |
| `creator` | `uuid NOT NULL REFERENCES actor` |

Restrições: `PRIMARY KEY(org_id,id)`.

## scenario_version

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int CHECK(version>0)` |
| `mode` | `char(1) CHECK(mode IN ('A','B'))` |
| `horizon` | `text NOT NULL` |
| `input_hash` | `char(64) NOT NULL` |
| `reason` | `text NOT NULL` |
| `created_at` | `timestamptz NOT NULL` |
| `creator` | `uuid NOT NULL REFERENCES actor` |

Restrições: `PRIMARY KEY(org_id,scenario_id,version)`; `FOREIGN KEY(org_id,scenario_id) REFERENCES scenario`.

## scenario_participant

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int` |
| `ibge` | `char(7) REFERENCES municipality` |
| `buyer_id` | `uuid REFERENCES buyer` |
| `authorization_source` | `uuid REFERENCES source_observation` |

Restrições: `PRIMARY KEY(org_id,scenario_id,version,ibge)`; `FOREIGN KEY(org_id,scenario_id,version) REFERENCES scenario_version`.

## scenario_line

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int` |
| `ibge` | `char(7)` |
| `item_id` | `uuid` |
| `item_version` | `int` |
| `requested_qty` | `numeric(24,8)` |
| `calculated_qty` | `numeric(24,8)` |
| `proposed_qty` | `numeric(24,8)` |
| `approved_qty` | `numeric(24,8)` |
| `method_id` | `uuid` |
| `method_version` | `int` |
| `inputs` | `jsonb NOT NULL` |
| `result` | `jsonb NOT NULL` |
| `status` | `text NOT NULL` |
| `reference_price_id` | `uuid` |
| `reference_price_version` | `int` |
| `line_amount` | `numeric(24,2)` |

Restrições: `PRIMARY KEY(org_id,scenario_id,version,ibge,item_id,item_version)`; `FOREIGN KEY(org_id,scenario_id,version,ibge) REFERENCES scenario_participant`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`; `FOREIGN KEY(method_id,method_version) REFERENCES method_version`; `FOREIGN KEY(reference_price_id,reference_price_version) REFERENCES reference_price(id,version)`.

## allocation_justification

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int` |
| `item_id` | `uuid` |
| `item_version` | `int` |
| `target` | `numeric(24,8) NOT NULL CHECK(target>=0)` |
| `unit_id` | `text NOT NULL REFERENCES unit` |
| `document_id` | `uuid NOT NULL REFERENCES document` |
| `weights_and_limits` | `jsonb NOT NULL` |
| `reviewer` | `uuid NOT NULL REFERENCES actor` |

Restrições: `PRIMARY KEY(org_id,scenario_id,version,item_id,item_version)`; `FOREIGN KEY(org_id,scenario_id,version) REFERENCES scenario_version`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## calculation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `scenario_id` | `uuid NOT NULL` |
| `scenario_version` | `int NOT NULL` |
| `method_snapshot` | `jsonb NOT NULL` |
| `input_snapshot` | `jsonb NOT NULL` |
| `source_snapshot` | `jsonb NOT NULL` |
| `trace` | `jsonb NOT NULL` |
| `result` | `jsonb NOT NULL` |
| `created_at` | `timestamptz NOT NULL` |

Restrições: `FOREIGN KEY(org_id,scenario_id,scenario_version) REFERENCES scenario_version`.

## decision_event

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int` |
| `actor_id` | `uuid NOT NULL REFERENCES actor` |
| `action` | `text NOT NULL` |
| `competence_source` | `uuid REFERENCES source_observation` |
| `reason` | `text NOT NULL` |
| `created_at` | `timestamptz NOT NULL` |

Restrições: `FOREIGN KEY(org_id,scenario_id,version) REFERENCES scenario_version`.

## private_quote_version

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid REFERENCES organization` |
| `quote_id` | `uuid` |
| `version` | `int` |
| `actor_id` | `uuid NOT NULL REFERENCES actor` |
| `item_snapshot` | `jsonb NOT NULL` |
| `quantity` | `numeric(24,8) NOT NULL CHECK(quantity>=0)` |
| `acquisition_unit` | `numeric(24,8) NOT NULL CHECK(acquisition_unit>=0)` |
| `sale_unit` | `numeric(24,8) NOT NULL CHECK(sale_unit>=0)` |
| `variable_unit` | `numeric(24,8) NOT NULL CHECK(variable_unit>=0)` |
| `freight` | `numeric(24,2) NOT NULL CHECK(freight>=0)` |
| `fixed_expenses` | `numeric(24,2) NOT NULL CHECK(fixed_expenses>=0)` |
| `tax_rate` | `numeric(12,10) NOT NULL CHECK(tax_rate>=0 AND tax_rate<1)` |
| `result_snapshot` | `jsonb NOT NULL` |
| `evidence` | `jsonb NOT NULL` |

Restrições: `PRIMARY KEY(org_id,quote_id,version)`.

## coverage_cell

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `municipality_ibge` | `char(7) NOT NULL REFERENCES municipality` |
| `provider_id` | `uuid NOT NULL REFERENCES provider` |
| `buyer_scope` | `jsonb NOT NULL` |
| `window_start` | `date NOT NULL` |
| `window_end` | `date NOT NULL` |
| `object_filter` | `jsonb NOT NULL` |
| `phase` | `text NOT NULL` |
| `state` | `text NOT NULL` |
| `pagination` | `jsonb NOT NULL` |
| `query_hash` | `char(64) NOT NULL` |
| `adapter_version` | `text NOT NULL` |
| `last_success_at` | `timestamptz` |
| `completeness` | `jsonb NOT NULL` |

Restrições: `CHECK(window_end>=window_start)`.

## job

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid REFERENCES organization` |
| `id` | `uuid` |
| `type` | `text NOT NULL` |
| `idempotency_key` | `text NOT NULL` |
| `state` | `text NOT NULL` |
| `attempts` | `int NOT NULL DEFAULT 0 CHECK(attempts>=0)` |
| `checkpoint` | `jsonb` |
| `deadline` | `timestamptz` |
| `access_class` | `text NOT NULL` |
| `resource_version` | `jsonb NOT NULL` |

Restrições: `PRIMARY KEY(org_id,id)`; `UNIQUE(org_id,type,idempotency_key)`.

## export_artifact

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `id` | `uuid` |
| `job_id` | `uuid NOT NULL` |
| `scenario_id` | `uuid` |
| `scenario_version` | `int` |
| `classification` | `text NOT NULL` |
| `object_key` | `text NOT NULL` |
| `sha256` | `char(64) NOT NULL` |
| `expires_at` | `timestamptz NOT NULL` |
| `revoked_at` | `timestamptz` |

Restrições: `PRIMARY KEY(org_id,id)`; `FOREIGN KEY(org_id,job_id) REFERENCES job`; `FOREIGN KEY(org_id,scenario_id,scenario_version) REFERENCES scenario_version`.

## watch

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid REFERENCES organization` |
| `id` | `uuid` |
| `actor_id` | `uuid NOT NULL REFERENCES actor` |
| `query_snapshot` | `jsonb NOT NULL` |
| `enabled` | `boolean NOT NULL` |
| `channels` | `jsonb NOT NULL` |

Restrições: `PRIMARY KEY(org_id,id)`.

## audit_event

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `actor_id` | `uuid NOT NULL REFERENCES actor` |
| `action` | `text NOT NULL` |
| `resource_version` | `jsonb NOT NULL` |
| `redacted_details` | `jsonb NOT NULL` |
| `created_at` | `timestamptz NOT NULL` |
## scenario_item

| Campo | Tipo e restrições SQL |
|---|---|
| `org_id` | `uuid` |
| `scenario_id` | `uuid` |
| `version` | `int` |
| `item_id` | `uuid` |
| `item_version` | `int` |

Restrições: `PRIMARY KEY(org_id,scenario_id,version,item_id,item_version)`; `FOREIGN KEY(org_id,scenario_id,version) REFERENCES scenario_version`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## indicator_observation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid REFERENCES organization` |
| `municipality_ibge` | `char(7) NOT NULL REFERENCES municipality` |
| `indicator_key` | `text NOT NULL` |
| `period` | `text NOT NULL` |
| `universe` | `text NOT NULL` |
| `unit_id` | `text NOT NULL REFERENCES unit` |
| `value` | `numeric(24,8)` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |
| `valid_until` | `date` |
| `access_class` | `text NOT NULL` |
## incoming_delivery

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL REFERENCES organization` |
| `buyer_id` | `uuid NOT NULL REFERENCES buyer` |
| `item_id` | `uuid NOT NULL` |
| `item_version` | `int NOT NULL` |
| `quantity` | `numeric(24,8) CHECK(quantity>=0)` |
| `due_date` | `date NOT NULL` |
| `destination` | `text NOT NULL` |
| `confirmed` | `boolean NOT NULL` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |

Restrições: `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## financial_resource

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid NOT NULL` |
| `scenario_id` | `uuid NOT NULL` |
| `version` | `int NOT NULL` |
| `item_id` | `uuid` |
| `item_version` | `int` |
| `period` | `text NOT NULL` |
| `amount` | `numeric(24,2) CHECK(amount>=0)` |
| `currency` | `char(3) NOT NULL` |
| `source_id` | `uuid NOT NULL REFERENCES source_observation` |
| `reviewer` | `uuid REFERENCES actor` |
| `valid_until` | `date NOT NULL` |

Restrições: `FOREIGN KEY(org_id,scenario_id,version) REFERENCES scenario_version`; `FOREIGN KEY(item_id,item_version) REFERENCES item_version`.

## model_evaluation

| Campo | Tipo e restrições SQL |
|---|---|
| `id` | `uuid PRIMARY KEY` |
| `org_id` | `uuid REFERENCES organization` |
| `method_id` | `uuid NOT NULL` |
| `method_version` | `int NOT NULL` |
| `training_window` | `jsonb NOT NULL` |
| `test_window` | `jsonb NOT NULL` |
| `coverage` | `jsonb NOT NULL` |
| `baseline` | `jsonb NOT NULL` |
| `metrics` | `jsonb NOT NULL` |
| `limitations` | `text NOT NULL` |
| `source_snapshot` | `jsonb NOT NULL` |
| `access_class` | `text NOT NULL` |

Restrições: `FOREIGN KEY(method_id,method_version) REFERENCES method_version`.

## Restrições adicionais e responsabilidades

O SQL inclui FKs compostas para linhas/participantes/itens/artefatos e documentos da organização, política RLS e gatilhos de snapshots imutáveis. Recurso, estoque, recebimentos e avaliação preditiva têm entidades próprias. O serviço valida unidade, origem, acesso público versus privado, relação sem ciclos, herança de classe, competência e atomicidade. Revisão de migração, grants, índices por carga, pool de conexão e testes negativos ainda são de produção. Nenhuma análise estática certifica o banco implantado.
