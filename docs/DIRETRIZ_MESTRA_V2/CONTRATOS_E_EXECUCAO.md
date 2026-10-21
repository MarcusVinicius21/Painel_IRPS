# Contratos e execução local

## Contratos novos

Todos os endpoints exigem a autenticação e o contexto de organização existentes. Escritas exigem CSRF quando a sessão usa cookie. UUIDs e campos são validados; schemas de escrita rejeitam campos extras.

| Rota sob `/api/v1` | Operação |
|---|---|
| `GET /national-catalogue` | `q`, `kind`, `active`, `group`, `classification` (código de classe), `snapshot`, `offset`, `limit` até 50. Retorna página, próximo offset e metadados dos snapshots |
| `GET /national-catalogue/{snapshot}/{code}/links` | Vínculos vigentes e revisados na organização |
| `POST /national-catalogue/links` | Código/snapshot, produto canônico, justificativa, evidência e confirmação explícita |
| `GET /director/products` | Produtos oficiais canônicos revisados disponíveis para a organização |
| `GET /director/history/{product_id}` | Fase, início, fim e até 118 municípios; reutiliza histórico auditável e suas janelas |
| `POST /director/studies` | Definição técnica, snapshot/código opcional, produto vinculado opcional, municípios, período/fase, classificação, meta opcional e conferência técnica |
| `GET /director/studies` | Até 50 estudos recentes da organização |
| `GET /director/studies/{id}` | Estudo preservado e situação da versão atual do cenário |
| `POST /director/studies/{id}/drafts` | Tipo, objeto, revisão do cenário, condições e conferência de coerência; retorna prévia e bloqueios |
| `GET /irp-drafts/{id}` | Minuta, contexto e indicador de desatualização do cenário ou registro documental |
| `POST /irp-drafts/{id}/exports/{docx,pdf}` | Exportação somente sem incoerência e com contexto atual; estado permanece em revisão |
| `GET /director/studies/{id}/register` | Sugestões, manifestações, comunicação e totais conhecidos/parciais |
| `POST /director/studies/{id}/operations` | Evento versionado com `expected_revision`, revisão do cenário, município, tipo, situação, quantidade e comprovantes pertinentes |
| `POST /director/studies/{id}/dossier` | ZIP do contexto e das minutas atuais; sem originais recebidos ou custos privados embutidos |

O endpoint anterior de histórico recebe campos aditivos `temporal_windows` e `annual`. Seus contratos anteriores permanecem disponíveis. O lookup de linhas V4 adicionado na estabilização anterior limita a consulta por cálculo, item/versão e até 118 municípios, sem depender da página visível de vinte linhas.

## Persistência

- `national_catalogue_snapshot` e `national_catalogue_entry`: dados públicos fornecidos, imutáveis; a aplicação tem somente leitura. Importação é uma tarefa local explicitamente configurada com o usuário proprietário do banco de testes.
- `national_product_link`: revisão de associação, por organização e com proveniência.
- `director_study`: contexto imutável, hash, cenário e versão exata.
- `irp_draft`: prévia estruturada, validações, versão e autor.
- `irp_operation`: eventos append-only, revisão otimista, documento/versão/hash, autor e data.
- `item_version.org_id`: itens privados de planejamento são visíveis somente na organização; itens públicos anteriores continuam compartilhados.
- `artifact`, `scenario`, `calculation`, `document`, auditoria e demais estruturas existentes são reaproveitados.

## Executar no ambiente preparado

Na raiz do repositório, em PowerShell:

```powershell
$env:IRPS_LOCAL_CONFIG = (Resolve-Path '.runtime/config-director-qa.json').Path
Push-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
Pop-Location
.\.venv\Scripts\python.exe scripts/importar_catalogo_nacional.py CATMAT 'CAMINHO_LOCAL/catmat.csv'
.\.venv\Scripts\python.exe scripts/importar_catalogo_nacional.py CATSER 'CAMINHO_LOCAL/catser.csv'
.\.venv\Scripts\python.exe scripts/configurar_modelo_irp.py 'CAMINHO_LOCAL/Formulario IRP - 010.docx'
```

Os caminhos de entrada são exemplos; use os anexos preservados. A configuração local ignorada contém os acessos do banco descartável. Não copie esses valores para arquivos versionados. Um ambiente novo deve seguir primeiro o README principal e instalar `backend/requirements.lock`.

API, a partir de `backend`:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 5247 --no-access-log
```

Frontend, a partir de `frontend`, em outro terminal:

```powershell
$env:IRPS_API_PORT = '5247'
$env:IRPS_FRONTEND_PORT = '5248'
npm run dev
```

Abra `http://127.0.0.1:5248/#/inteligencia`. A conta de demonstração é “Equipe de compras A” no emissor local de testes. Isso não representa autenticação institucional pronta para produção.

A base de demonstração é `irps_director_qa`, cópia local separada. A suíte Python usa `config-increment-test.json`; as migrações novas foram também verificadas em um banco novo próprio. Nenhum banco real de produção foi migrado.

## Reprodução dos testes

```powershell
$env:IRPS_LOCAL_CONFIG = (Resolve-Path '.runtime/config-increment-test.json').Path
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q --tb=short
Pop-Location
npm --prefix frontend run build
$env:IRPS_BASE_URL = 'http://127.0.0.1:5248'
Push-Location frontend
npx playwright test
Pop-Location
.\.venv\Scripts\python.exe scripts/auditar_diff_local.py
git diff --check
```

Para a importação e a demonstração reprodutível, volte a selecionar `config-director-qa.json` e execute `scripts/demonstrar_diretriz.py`. O script só aceita emissor local de testes; cria um estudo fictício a partir de um código real do CATMAT, gera minutas e um dossiê, inventaria os fatos existentes e não acessa fontes governamentais pela rede.

`scripts/validar_migracoes_diretriz.py` cria um banco local novo, aplica até 0011 duas vezes e verifica RLS. O banco é preservado. As migrações append-only novas recusam downgrade que apague evidências; o script antigo de downgrade completo não foi utilizado nesta rodada.

## Limites do controle documental

Um documento conferido comprova o que o operador revisou, não a competência jurídica por decisão automática. A pessoa que registra uma confirmação precisa informar os elementos de competência e possuir as permissões necessárias. Produção exige definição institucional dos responsáveis e do rito.

O dossiê contém referências e hashes dos documentos recebidos. Exportar cópias integrais desses originais exige seleção e revisão próprias, para evitar distribuição indevida de documentos internos.
