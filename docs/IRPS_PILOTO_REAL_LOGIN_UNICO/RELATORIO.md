# IRPS — piloto real com acesso operacional único

Data: 22/10/2026. Aplicação: **http://127.0.0.1:5296/**. API: http://127.0.0.1:5295.

O Chrome foi aberto com Playwright, autenticado no operador único e no estudo municipal real. Não houve commit, push, merge, PR, deploy ou chamada paga de IA.

## Resultado por etapa

| Etapa | Comprovação | Limite real |
|---|---|---|
| Acesso | Um operador, uma organização e uma vinculação; todos os módulos acessíveis | Autenticação local protegida; não é OIDC produtivo |
| Banco | Banco PostgreSQL novo, migração 0014, RLS preservada | Nenhum banco anterior foi apagado, copiado ou recriado |
| IBGE | Ipatinga/MG 3131307 e Timóteo/MG 3168705 consultados | Identidade municipal; não inclui indicadores demográficos |
| PNCP | Cinco publicações e 21 linhas de itens oficiais preservadas | Coleta pontual, parcial, primeira página; não representa 26 compras |
| Histórico | Item, versão, situação, período, município e fonte rastreáveis | Histórico observado não é consumo, necessidade futura ou anuência |
| V4 A | Execução com entradas ausentes e quantidades indisponíveis | Sem estoque, recebimentos e parâmetros validados, não há necessidade calculável |
| V4 B | Execução bloqueada sem meta e distribuição aprovadas | Nenhuma meta global foi inventada ou distribuída |
| Preparação de IRP | Minuta interna gerada, com pendências e sem numeração oficial | Não é documento aprovado, assinado ou publicado |
| Manifestações | Dois municípios do estudo, sem respostas formais registradas | Comunicação pendente; silêncio não significa recusa |
| Consolidação | Total confirmado e consolidado indisponíveis | Nenhuma quantidade histórica ou sugerida entrou como confirmação |
| Documentos | Downloads DOCX e PDF executados e verificados | Minutas para revisão, sem aprovação jurídica |
| Simulação comercial | Acesso permitido ao mesmo operador; campos iniciais vazios | Hipóteses comerciais continuam privadas e separadas dos preços públicos |

## Estado inicial e preservação

Pasta real: `C:/Users/NEXUS/Downloads/TRAMPOS/IRPs/Painel_IRPS`.

Branch e HEAD iniciais e finais: `checkpoint/irps-integrado-i17-04-2026-10-22`, `a83e3205e685370e12ad6c42bd17f57bba20a6ff`. A árvore inicial estava limpa. O remote continua `MarcusVinicius21/Painel_IRPS`. Não foram encontradas instruções AGENTS.md na árvore pesquisada do projeto. Nenhum patch histórico foi reaplicado.

Os oito arquivos Python originais V4 tiveram seus hashes comparados com `docs/validacao/integridade-v4.json`: oito idênticos. As sete referências visuais originais não aparecem no diff. Fórmulas, modos A/B, arredondamentos e regras de consolidação não foram alterados.

Os serviços anteriores foram preservados. A versão atual foi iniciada em portas separadas, sem encerrar processos cuja identidade não pôde ser confirmada com segurança.

## Acesso único e segurança

As configurações locais disponíveis não continham issuer HTTPS e JWKS HTTPS utilizáveis para OIDC. Foi implementado `operational_local`, exclusivamente em loopback, com:

- Senha forte gerada localmente, protegida no servidor por Argon2id: 64 MiB, três iterações e paralelismo quatro.
- Configuração, senha inicial e chave de assinatura fora do Git, em pasta privada com ACL Windows restrita ao usuário e SYSTEM.
- JWT RS256 com emissor, audiência, validade, identidade e organização verificados; sessões persistidas e revogáveis.
- Cookies próprios do operador, `HttpOnly` para a sessão, `SameSite=Strict`, CSRF nas alterações, origem permitida e expiração de uma hora.
- Cinco falhas de senha em 15 minutos bloqueiam novas tentativas nesse intervalo. O controle e as falhas ficam persistidos na auditoria, sem gravar senhas.
- Rejeição de conexões não loopback e identidade diferente do operador configurado.
- Rotas de contas de teste e de login fictício indisponíveis no modo operacional.
- Permissões de todos os módulos atribuídas pelo contexto operacional validado, mantendo o escopo de organização, RLS e auditoria. Não foram criados novos usuários ou empresas.
- Cookie Secure desativado somente para HTTP em loopback. Este modo não deve ser publicado nem usado como autenticação de produção.

A interface operacional não apresenta seletor de organização nem contas fictícias. A navegação, documentos e simulação comercial usam a mesma identidade. Contas múltiplas e exemplos permanecem restritos ao modo explícito de QA. Cargas sintéticas são recusadas no ambiente operacional; documentos fictícios também são recusados.

## Banco e dados oficiais

O banco operacional novo é `irps_operacional_local_ab7af83a1b`. Foram aplicadas as migrações até 0014 sem executar seed. A verificação encontrou:

- Uma organização CONSORMULTI, um ator e uma vinculação.
- Zero fatos, itens, cenários e documentos classificados como sintéticos.
- Dois cadastros municipais comprovados por respostas do IBGE.
- Cinco publicações PNCP e 21 itens publicados, com observações oficiais e hashes preservados.
- Zero entradas de catálogo nacional importadas neste banco operacional. Os bancos anteriores e seus catálogos permanecem preservados.

Não foi copiado o catálogo de demonstração. A origem oficial corrente dos CSVs locais não foi certificada nesta rodada; portanto, não foi afirmada cobertura nacional CATMAT/CATSER nem importado um arquivo apenas porque possuía a contagem esperada. A seleção de produtos reais funciona pela identidade exata dos itens consultados no PNCP, independentemente dessa pendência.

Uma identidade técnica de item único preserva sua versão e sua fonte. Ela não aprova equivalência com outro item. Descrições semelhantes não foram agrupadas automaticamente. A grafia `1,00 UNIDADE` pode ser identificada como uma unidade sem converter embalagens; o texto original permanece preservado.

## Consulta real e exemplo municipal

IBGE: [Ipatinga](https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3131307) e [Timóteo](https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3168705).

PNCP: recorte de publicação de **16 a 22/10/2026**, código territorial 3131307, modalidades explicitamente consultadas 4, 6, 8 e 9, página 1 e tamanho 10. As modalidades 6 e 8 retornaram registros; 4 e 9 retornaram vazias neste recorte. Isso não comprova ausência de outras compras ou cobertura de outras modalidades.

O recorte territorial incluiu registros do MUNICÍPIO DE IPATINGA, CNPJ **19.876.424/0001-42**, e registros da POLÍCIA MILITAR DO ESTADO DE MINAS GERAIS em unidades localizadas em Ipatinga. Estes últimos não foram chamados de compras da prefeitura. A interface orienta a conferir o comprador original.

O teste final usou um item do **Município de Ipatinga**, compra PNCP de 2026, sequencial 142:

> ANESTÉSICO CLORIDRATO DE LIDOCAÍNA 2% COM EPINEFRINA 1: 100.000, VASOCONSTRITOR, CAIXA COM 50 TUBETES DE VIDRO DE 1,8ML.

**675 caixas e R$ 86.400,00 publicados como estimativa**, em um registro identificado, sem somar outra linha com descrição semelhante. [Resposta oficial de itens](https://pncp.gov.br/api/pncp/v1/orgaos/19876424000142/compras/2026/142/itens?pagina=1&tamanhoPagina=10).

O histórico municipal mostrou o registro em Ipatinga. Timóteo aparece com quantidade indisponível: seu cadastro foi verificado, mas não houve coleta PNCP suficiente para inferir zero compras. A janela histórica exibida não amplia a cobertura efetivamente coletada.

Foram consultados resultados de dois itens de outro processo, com respostas vazias preservadas. A tentativa adicional de consultar resultados do item municipal selecionado falhou por conexão, sem causa determinada. Não se afirmou inexistência de homologação. Contratos, pagamentos, entregas e consumo não tiveram abrangência comprovada por este piloto.

O arquivo `consultas-oficiais.json` registra 13 tentativas: 11 bem-sucedidas e duas falhas. Há ainda duas falhas iniciais do IBGE registradas separadamente, e duas chamadas de diagnóstico HTTP sem importação. Não houve coleta massiva, evasão de limite, autenticação externa ou substituição por fixtures.

## Jornada efetivamente executada

No mesmo contexto autenticado do Chrome:

1. Entrar com senha do operador e abrir Início.
2. Abrir Inteligência e selecionar um item oficial já consultado.
3. Conferir o histórico individual de Ipatinga e Timóteo, com fonte, fase e unidade.
4. Conferir a especificação reproduzida da fonte e criar estudo interno sem meta inventada.
5. Executar o V4 A: quantidades indisponíveis por ausência de entradas municipais. Executar B em cenário interno separado, sem meta aprovada: distribuição bloqueada.
6. Preparar prévia de procedimento a partir do estudo salvo; preservar as pendências administrativas.
7. Gerar e baixar DOCX e PDF da minuta; conferir arquivos não vazios.
8. Abrir Manifestações. Uma tentativa de confirmação sem comprovante foi rejeitada com HTTP 422.
9. Abrir Consolidação: nenhum participante confirmado, total indisponível e duas pendências municipais.
10. Conferir a apresentação também em mobile de 390 px.

Não foi gravada quantidade manual sugerida por município, nem alterado o V4 com volumes históricos. Estudos e cenários internos criados pelas execuções dos testes foram preservados, identificados como internos; eles não são novas compras públicas.

## Validações

| Execução | Resultado |
|---|---|
| `python -m pytest backend/tests -q --tb=short` com configuração QA descartável | **295 testes e 200 subtestes aprovados**, 119,82 s |
| Testes focados de autenticação e identidade observada | **11 aprovados** |
| `npm run build` no frontend | **Aprovado** |
| `IRPS_OPERATIONAL_REAL=1 ... npx playwright test qa/operational-real.spec.ts --reporter=list` | **2 aprovados**; Chrome real, desktop e mobile |
| Alembic `upgrade head`, repetido em banco QA novo | **0014**, segunda execução idempotente |
| Verificação PostgreSQL operacional | Um operador, zero sintéticos, seis tabelas verificadas com RLS forçada |
| Hashes V4 | **8/8 idênticos** |
| `git diff --check` | **Aprovado** |
| Verificação de segredos nos arquivos de código alterados | Nenhum achado nos padrões examinados; arquivos privados ignorados |

Os testes completos incluem as regressões existentes de cálculo, autorização, isolamento, histórico, cenários e documentos. Não se afirma teste de produção ou auditoria externa de segurança.

Ocorreram falhas intermediárias na preparação de fixtures: SecretStr não convertido no teste e emissor de teste não exclusivo; depois, CNPJ aleatório de fixture com 15 dígitos. As fixtures foram corrigidas, sem enfraquecer asserções nem flexibilizar as validações de produção. Houve também um erro inicial de JSX corrigido antes do build final. No navegador, corrigiu-se o marcador de operação que herdava ocultação visual do antigo banner. A revisão final também corrigiu o resumo que chamava uma execução V4 pendente de “Cálculo disponível”: agora distingue dados insuficientes e cálculo parcial. Um erro de consulta de metadados Alembic pelo papel da aplicação foi resolvido usando leitura pelo proprietário, sem ampliar permissões do aplicativo.

Avisos remanescentes: depreciação Starlette/httpx; chave curta em teste deliberado de rejeição JWT HMAC; diretiva do lucide-react e tamanho do bundle no build. Eles não foram ocultados dos registros dos testes.

## Arquivos e contratos

- `backend/app/operational.py`: autenticação de operador local e validação de loopback.
- `config.py`, `security.py`, `main.py`, `documents.py`: configuração privada, contexto autorizado, cookies separados, rotas de acesso e bloqueio de dados sintéticos.
- `catalogue.py`, `director_routes.py`: identidade determinística de item/versão e lista limitada de itens oficiais disponíveis.
- `GET /api/v1/auth/mode`, `POST /api/v1/auth/operator-login`: seleção explícita do modo e entrada protegida, sem devolver senha ou token no corpo.
- `GET /api/v1/director/observed-items?q=...&limit=...`: até 50 registros oficiais atuais, com fonte e versão.
- `POST /api/v1/director/observed-items/{fact_id}/identity`: identidade única e idempotente; não cria equivalência entre itens.
- `Workspace`, `App`, `api`, `Director`, `Planning`, `Opportunities`, `Research`, `ObservedItems`: acesso único, opções QA restritas, seleção de fatos oficiais e filtros iniciais compatíveis com os dados disponíveis.
- Requisitos Argon2, testes e scripts de preparação, início, coleta limitada e verificação.

Não houve alteração de schema ou nova migração. Consulte `ALTERACOES_LOCAIS.patch`, `GIT_STATUS.txt` e `STATUS.json` para o diff e a lista física completa.

## Como abrir novamente

A janela Chrome está aberta e autenticada. Endereço: **http://127.0.0.1:5296/**.

Se os serviços forem encerrados, execute na pasta real do projeto:

```powershell
./scripts/iniciar_operacional.ps1
```

A senha inicial está exclusivamente no arquivo local privado `.runtime/operacional-local/acesso-privado.json`. Abra-o somente neste computador se precisar entrar novamente. Nenhuma senha foi incluída neste relatório, no diff ou na galeria. A configuração de execução fica em `.runtime/operacional-local/config.json`.

Para preparar outro banco local novo, sem copiar dados:

```powershell
.venv/Scripts/python.exe scripts/preparar_operacional.py --credentials-from .runtime/sequence-05-06/config-browser.json
```

O script preserva uma configuração operacional já existente; não recria seu banco. O arquivo indicado fornece somente credenciais locais de conexão, nunca dados ou sementes de teste.

Para verificar novamente o ambiente atual:

```powershell
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/operacional-local/config.json).Path
.venv/Scripts/python.exe scripts/verificar_operacional.py
```

Não execute a suíte backend completa com esta configuração operacional: suas fixtures exigem um banco QA separado. Os comandos efetivamente usados nesta rodada e seus resultados estão em `testes/`.

## Pendências reais

1. Estoque, recebimentos, base atendida, taxas e respectivas fontes validadas para o V4.
2. Quantidade global, critérios, pesos, pisos e tetos aprovados para eventual uso do modo B.
3. Autoridade competente, rito, prazo, canal e condições de entrega; revisão jurídica da minuta e numeração oficial.
4. Comunicações comprovadas e manifestações municipais autênticas, com documentos e conferência. Nenhuma foi simulada.
5. Coleta histórica mais ampla e reconciliada; retomada da consulta de resultados que falhou. Ausência de resposta não é ausência de compra.
6. Certificação da origem do catálogo nacional antes de importá-lo no banco operacional.
7. Configuração de autenticação e infraestrutura de produção em etapa própria. O modo local atual não é autorização de publicação.

Essas pendências não impedem consultar os registros oficiais, abrir o histórico, manter estudos internos e gerar minutas de revisão. Impedem declarar necessidade municipal comprovada, confirmação de participantes ou procedimento oficialmente concluído.

## Evidências físicas

- `dados-oficiais.json`, `consultas-oficiais.json`, `falha-inicial.json`.
- `jornada-real.json`, `modulos-acessiveis.json`, `verificacao-banco.json`.
- `seguranca-e-integridade.json`, `STATUS.json`, `ALTERACOES_LOCAIS.patch`, `GIT_STATUS.txt`.
- `testes/` com os resultados realmente executados.
- `capturas/` e `GALERIA.html`, com desktop 1672 × 941 e mobile 390 px.

O trabalho permanece local e não commitado. Nenhuma mudança foi enviada ao GitHub.
