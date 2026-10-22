# IRPS — Observatório de compras públicas

Aplicação local para pesquisar compras, comparar municípios e **montar licitações** com quantidades por município e item. Inclui simulação comercial privada, documentos revisáveis e um assistente offline.

O frontend Observatório usa React e TypeScript. O backend FastAPI grava no PostgreSQL e executa o núcleo matemático V4 original. As fórmulas do V4 permanecem intactas; a interface apresenta os resultados do servidor.

**Estado: implementação local de testes.** As contas e os cenários iniciais são fictícios e aparecem identificados. O acesso com contas de teste valida assinatura e permissões, mas não substitui uma identidade de produção. Não use documentos ou informações comerciais reais neste ambiente.

## O que funciona

- Cenários versionados, seleção de participantes e itens, necessidades individuais e distribuição global justificada.
- Quantidades, preços de referência, valores totais, memória de cálculo e exportações CSV/XLSX/PDF.
- Até 118 participantes iniciais e cenários testados com 100 itens: 11.800 linhas persistidas.
- Autorização no servidor, isolamento entre organizações com RLS e simulações comerciais privadas.
- Importação limitada e revisável de PDF textual, DOCX, XLSX e CSV, preservando o arquivo original.
- Consultas públicas delimitadas de PNCP e IBGE; catálogo CATMAT/CATSER separado das compras.
- Assistente offline com ferramentas validadas. Chamadas pagas a IA permanecem desativadas.
- Observatório responsivo conectado às APIs, incluindo estados de erro e informações ausentes.
- Área **Oportunidades**: coleta PNCP paginada e retomável, filtros históricos, cobertura explícita, equivalências revisadas, prioridade condicionada a dados e revisão humana, rascunho de licitação e acompanhamentos locais.
- **Catálogo inteligente e cobertura**: normalização auditável, produtos equivalentes revisados, inventário por município/órgão/fonte/fase, publicações e atualizações PNCP, consulta pontual de preços Compras.gov.br e execução limitada por agendador local.

Os conectores não representam cobertura histórica completa. Quantidade contratada não comprova consumo; valor contratado não significa valor pago. A instalação limpa inclui dados sintéticos, não uma cópia do banco utilizado anteriormente.

## Instalação local — Windows

Requisitos: **Python 3.12**, **Node.js 24 com npm**, PowerShell e Google Chrome para os testes de navegador. Os scripts fornecidos preparam PostgreSQL 18.6 portátil, sem serviço global. A instalação automatizada foi validada no Windows; outras plataformas exigem adaptação do bootstrap PostgreSQL.

```powershell
git clone git@github.com:MarcusVinicius21/Painel_IRPS.git
Set-Location Painel_IRPS
# Estado integrado I01–I17 desta entrega:
git switch checkpoint/irps-integrado-i17-04-2026-10-22
& .\scripts\preparar_ambiente.ps1 -PythonExe 'python'
```

O script cria `.venv`, instala os locks Python/npm, obtém os binários oficiais PostgreSQL e prepara migrações e exemplos. O download PostgreSQL tem cerca de 385 MB. O digest fixado registra o binário validado na entrega, sem alegar checksum separado do fornecedor. Nenhum token, chave externa ou faturamento é necessário.

As senhas aleatórias e as chaves do emissor local são geradas somente em `.runtime/`, ignorada pelo Git. **Não copie configurações reais para `.env.example`**. A aplicação lê apenas o caminho explícito `IRPS_LOCAL_CONFIG`, dentro de `.runtime`; não carrega `.env` automaticamente.

## Executar

Em dois terminais, na raiz do repositório:

```powershell
& .\scripts\iniciar_api.ps1
```

```powershell
& .\scripts\iniciar_frontend.ps1
```

- Observatório: <http://127.0.0.1:5210/>
- API/OpenAPI: <http://127.0.0.1:5211/docs>
- PostgreSQL: `127.0.0.1:55432`, bancos `irps_local` e `irps_migration_test`.

Escolha uma conta fictícia para começar. As equipes A/B e empresas A/B permitem conferir o isolamento. As consultas oficiais são acionadas em **Fontes e cobertura**; não exigem credenciais.

Em **Catálogo e cobertura**, confira as páginas realmente coletadas, reanalise os itens e revise sugestões antes de agrupá-las. Para repetir o piloto público limitado ou avançar coletas já autorizadas no ambiente local:

```powershell
& .\.venv\Scripts\python.exe .\scripts\piloto_cobertura.py --pages 24
& .\.venv\Scripts\python.exe .\scripts\avancar_coletas.py --collections 5 --pages-each 1
```

Veja [o relatório técnico deste incremento](docs/implementacao/COBERTURA_HISTORICA_CATALOGO.md) e [a evidência do piloto MG](docs/validacao/PILOTO_COBERTURA_CATALOGO.md). O piloto não comprova toda a história de um município.

Para reiniciar o banco e encerrar os serviços:

```powershell
& .\.venv\Scripts\python.exe .\scripts\iniciar_postgres.py
# Ctrl+C nos terminais de API e frontend; depois:
& .\scripts\parar_postgres.ps1
```

Se as portas estiverem ocupadas, configure `IRPS_PG_PORT`, `IRPS_API_PORT` e `IRPS_FRONTEND_PORT` **antes da preparação** e mantenha esses valores nos terminais. A API aceita `-Port`; o Playwright também aceita `IRPS_BASE_URL`. Não aponte o validador de migrações para bancos reais.

## Testar

```powershell
# Exclusivamente no PostgreSQL local; cria um banco novo descartável para upgrade/reaplicação:
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/config-test.json).Path
& .\.venv\Scripts\python.exe .\scripts\validar_migracoes_diretriz.py
Push-Location backend
& ..\.venv\Scripts\python.exe -m pytest -q --junitxml=../.runtime/evidencias/pytest.xml
Pop-Location
Push-Location frontend
npm.cmd run build
# API, frontend e PostgreSQL devem estar em execução:
npm.cmd run qa
npm.cmd audit --omit=dev
Pop-Location
& .\.venv\Scripts\python.exe -m pip_audit
```

Resultados brutos, downloads dos testes e capturas ficam em `.runtime/evidencias/`. Somente evidências revisadas são incluídas em `docs/validacao/`. O teste 118 × 100 e as verificações de navegador podem levar alguns minutos. Veja [resultados da preparação para GitHub](docs/validacao/RESULTADOS.md) e [falhas anteriores preservadas](docs/implementacao/LOG_TESTES.md).

## Organização

```text
backend/app/          API, permissões, cenários, documentos, fontes e assistente
backend/irps_core/    Oito módulos originais V4, sem alteração de fórmulas
backend/migrations/  Schema PostgreSQL até a revisão Alembic 0014
backend/tests/       Regressões V4 e testes de integração/segurança
backend/seed_data/   Cadastro municipal conciliado e catálogo fictício
frontend/src/        Observatório conectado ao backend
frontend/qa/         Testes Playwright existentes
scripts/             Preparação, execução e validações locais
dados/               Lista histórica exigida pelos testes V4
docs/especificacao/  Escopo, telas, regras, arquitetura e fluxogramas de referência
docs/implementacao/  Documentação do recorte efetivamente implementado
docs/validacao/      Resultados revisados, integridade V4 e capturas selecionadas
```

Comece pelo [índice técnico](docs/INDEX.md), [arquitetura executável](docs/implementacao/ARQUITETURA_IMPLEMENTADA.md), [Oportunidades CONSORMULTI](docs/implementacao/OPORTUNIDADES_CONSORMULTI.md), [modelo de dados](docs/implementacao/BANCO_IMPLEMENTADO.mmd) e [OpenAPI](docs/implementacao/OPENAPI_IMPLEMENTADO.json). As especificações descrevem também funcionalidades futuras; o estado implementado prevalece em `docs/implementacao/`.

## Segurança e limites

Nenhuma credencial, banco local, sessão, documento privado, skill privada ou exportação volumosa deve entrar no Git. Consulte a [política de segurança](SECURITY.md) e o [relatório de auditoria](docs/validacao/SEGURANCA_PUBLICACAO.md).

Antes de produção: identidade externa HTTPS, gestão de segredos, proteção dos parsers, workers e limites distribuídos, backups/restauração, cobertura de dados e revisão independente. Este repositório não configura implantação nem ativa serviços pagos.

As licenças das dependências e da fonte Manrope estão documentadas [aqui](docs/implementacao/DEPENDENCIAS_E_LICENCAS.md). Este repositório é público; os avisos de licença existentes devem ser preservados.

## Diretriz Mestra V2 — incremento local
A área **Inteligência e planejamento** reúne catálogo nacional, histórico por município, meta preliminar, estudo versionado e minutas IRP revisáveis. Consulte [a entrega local](docs/DIRETRIZ_MESTRA_V2/README.md) para contratos, execução, testes e limites. Os 348.679 códigos importados não representam compras nem cobertura municipal. O checkpoint integrado I01–I17 inclui o código acumulado; não constitui aceite visual integral ou liberação de produção.

## Checkpoint integrado I01–I17 — 22/10/2026

A branch `checkpoint/irps-integrado-i17-04-2026-10-22` preserva o estado funcional acumulado para auditoria posterior com dados públicos reais. Inclui os módulos de histórico filtrado, resumos verificáveis, estudos multiitem, revisão de minutas, evidências municipais, inventário e prévia de PDF, além das migrações **0013 e0014** e dos respectivos testes.

As sete referências originais permanecem em [docs/design/referencias-irps](docs/design/referencias-irps/README.md). O núcleo V4 continua idêntico. A fidelidade visual ainda é parcial, e nova gravação manual de quantidade municipal permanece dependente de autorização institucional. Não foi iniciada nova coleta nem alterada regra de negócio nesta publicação.

Leia [o relatório público do checkpoint](docs/implementacao/CHECKPOINT_I01_I17_2026-10-22.md). Ele separa testes executados nesta publicação de resultados anteriores. Evidências brutas, configurações, bancos e grandes ZIPs ficam somente no workspace local.

A execução do frontend após instalação não depende das fixtures de QA. Já os testes visuais históricos usam estudos preparados em `.runtime`; esses dados e configurações privadas não são distribuídos. Prepare-os em ambiente isolado com os helpers guardados em `backend/tests/`, sem apontar para produção nem enfraquecer asserções. Uma instalação limpa não reproduz automaticamente o banco e os IDs de estudos do ambiente de desenvolvimento.
