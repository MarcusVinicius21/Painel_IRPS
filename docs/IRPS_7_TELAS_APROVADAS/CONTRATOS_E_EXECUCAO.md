# Contratos e execução local

## Reaproveitamento e extensão

As rotas existentes foram preservadas. Não há outra aplicação React nem uma segunda implementação das fórmulas. `Executive` usa os serviços de leitura; `Director` compõe a jornada; `IRPRegister` usa o registro institucional existente; `WorkflowPlanning` seleciona o cenário correto antes de abrir `Planning`.

| Contrato | Finalidade e limites |
|---|---|
| `GET /api/v1/director/dashboard/{catalogue,history,operations}` | Consultas independentes. Histórico somente oficial e atual, agrupado por fase; operações somente da organização autenticada. |
| `GET /api/v1/national-catalogue` | Busca/paginação já existentes; máximo 50 por página. Código é texto, associado ao snapshot. |
| `GET /api/v1/national-catalogue/{snapshot}/{code}` | Recupera a seleção exata após navegação/reabertura. Não implica compra. |
| `GET/POST /api/v1/director/progress` | Lista snapshots mais recentes ou salva um rascunho incompleto. Escrita exige `scenario.write`. |
| `GET /api/v1/director/progress/{id}` | Recupera rascunho da organização. Não cria nem restaura aprovação técnica. |
| `POST /api/v1/director/studies` | Contrato validado anterior; meta não é entrada V4; exige unidade e conferência técnica. |
| `GET /api/v1/director/studies/{id}` | Inclui referência interna derivada da identidade/ano e verifica a versão atual do cenário. |
| `GET /api/v1/director/studies/{id}/drafts` | Até 50 versões documentais, com modelo, data e validação; não retorna documentos de outra organização. |
| `GET /api/v1/irp-drafts/{id}/preview` | Seções do mesmo gerador DOCX/PDF, com estado de desatualização. |
| `GET /api/v1/director/studies/{id}/register` | Resumo vigente, sugestões/confirmados conhecidos separados, recusas válidas, estado municipal e últimas 500 operações para exibição. O resumo usa os registros vigentes completos. |
| `POST /api/v1/director/studies/{id}/operations` | Reutilizado: versão esperada, cenário, prova e competências; conflito retorna 409, validação retorna 422, falta de permissão retorna 403. |
| `POST /api/v1/director/studies/{id}/consolidation/{xlsx,pdf}` | Gera quadro interno sem preencher pendências com zero. Exige exportação e leitura documental. |
| `POST /api/v1/director/studies/{id}/dossier` | Inclui relatórios atuais de consolidação e minutas vigentes; exclui minutas bloqueadas/desatualizadas e originais recebidos. |

O rascunho de progresso recebe campos estritos: item/snapshot opcionais, municípios, período, fase, etapa e formulário parcial. Campos de aprovação não são aceitos. Cada sucessor referencia o snapshot anterior; uma segunda gravação sobre o mesmo antecessor retorna conflito, preservando ambas as evidências já existentes. Nenhuma quantidade desse armazenamento é consumida pelo cálculo.

## Navegação

- `#/inicio`: dashboard.
- `#/inteligencia?etapa=selecao`: catálogo e seleção.
- `#/inteligencia?etapa=historico`: filtros e evidências.
- `#/inteligencia?etapa=planejamento`: matriz e planejamento.
- `#/inteligencia?estudo=ID&etapa=preparacao`: preparação e versões.
- `#/inteligencia?estudo=ID&etapa=manifestacoes`: recebimento e conferência.
- `#/inteligencia?estudo=ID&etapa=consolidacao`: quadro e exportações.

`rascunho=ID` reabre progresso incompleto. `codigo` e `catalogo` permitem recuperar a seleção de consulta, mas não substituem o salvamento de progresso. Os parâmetros V4 usam `estudo=ID`, mantido nas abas e no link de retorno. Valores importantes ficam no backend; estado temporário não salvo é identificado como edição.

## Ambiente local já preparado

PostgreSQL em loopback, porta 55433. API em 5247; frontend em 5248. As configurações reais ficam em `.runtime`, ignorada pelo Git e excluída do ZIP. Nenhum segredo está reproduzido aqui. O ZIP de revisão é complementar ao repositório e ao diff local, não uma instalação autônoma.

Para reabrir o ambiente existente, a partir da raiz do repositório:

```powershell
$env:IRPS_LOCAL_CONFIG = (Resolve-Path .runtime/config-director-qa.json).Path
$env:IRPS_API_PORT = '5247'
$env:IRPS_FRONTEND_PORT = '5248'
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --app-dir backend --factory --host 127.0.0.1 --port 5247
```

Em outro terminal:

```powershell
$env:IRPS_API_PORT = '5247'
$env:IRPS_FRONTEND_PORT = '5248'
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5248
```

Use o cluster local existente. Não execute `initdb`, limpeza ou recriação sobre os dados atuais. Se as portas estiverem ocupadas, confira os processos; não encerre serviços de outros projetos. Configurações de outra máquina devem ser geradas localmente a partir de exemplos fictícios, nunca copiadas do ambiente atual.

O acesso de teste “Equipe de compras A” é fictício e restrito ao modo local autorizado. Ele não representa autenticação de produção nem uma conta municipal.

## Testes reproduzíveis

```powershell
$env:IRPS_LOCAL_CONFIG = (Resolve-Path .runtime/config-increment-test.json).Path
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe scripts/validar_migracoes_diretriz.py --evidence-dir .runtime/sete-telas
npm --prefix frontend run build
```

Em `frontend`, com API e frontend locais operacionais:

```powershell
$env:IRPS_FRONTEND_PORT = '5248'
npx playwright test
```

As regressões de backend usam banco isolado; o verificador de migrações cria outro banco descartável sem destruir o existente. Playwright usa o ambiente local de QA e cria somente cenários/documentos sintéticos identificados, além de ler o catálogo e fatos oficiais existentes. Não execute esses testes contra produção.
