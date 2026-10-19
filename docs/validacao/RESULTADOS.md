# Validação da cópia para GitHub — 19/10/2026

Todos os testes abaixo foram executados sobre o código da raiz deste repositório, em uma instalação nova. O ambiente da entrega anterior não foi reutilizado para gravar testes.

| Verificação | Resultado | Evidência revisada |
|---|---|---|
| Instalação Python | Nova `.venv`, lock instalado; `pip check` aprovado | Lock e scripts na raiz |
| Instalação frontend | `npm ci --include=dev --ignore-scripts` aprovado | `frontend/package-lock.json` |
| Python | **115 casos aprovados**, 200 subverificações internas; 29,24 s | [Console](pytest.txt), [JUnit](pytest.xml) |
| Build TypeScript/Vite | Aprovado | [Saída integral revisada](build.txt) |
| Playwright/Chrome | **11 aprovados**, zero falhas, saltos ou retries; 88,06 s | [Console](playwright.txt), [JSON](playwright.json) |
| Responsividade | 320, 390, 768, 1024 e 1440 px | [Galeria](GALERIA.md) |
| Navegação | 22 rotas autenticadas em 390/1440 px, sem coleta oficial prévia | Suíte `frontend/qa/routes.spec.ts` |
| Migrações PostgreSQL 18.6 | 30 tabelas → zero → 30; 26 com RLS forçada | [Resultado](migracoes.json) |
| Auditoria npm | Zero vulnerabilidades conhecidas, incluindo desenvolvimento | [Resultado](npm-audit.json) |
| Auditoria Python | Zero vulnerabilidades conhecidas no ambiente instalado | [Resultado](pip-audit.json) |
| Núcleo V4 | Oito módulos com bytes idênticos ao original e ao índice Git | [SHA-256](integridade-v4.json) |
| Segredos e privacidade | Revisão dos arquivos selecionados e verificações antes do envio | [Relatório](SEGURANCA_PUBLICACAO.md) |
| Links documentais locais | 181 conferidos; nenhuma referência ausente após ajustes | [Resultado](links-locais.json) |

Os 115 casos correspondem aos 65 históricos e 50 da integração. O XML registra também as subverificações e pode apresentar 315 entradas. Não são 315 casos independentes. Os 21 testes do pacote instrutivo, aprovados na rodada anterior, não foram repetidos nem somados nesta publicação.

## Ambiente e limites do teste

A cópia foi testada em portas separadas: frontend 5220, API 5221 e PostgreSQL 55433. Os bancos são novos, gerados apenas para esta verificação. Os scripts mantêm 5210/5211/55432 como padrão e aceitam portas explícitas.

Nenhum banco, documento privado, sessão, chave ou configuração anterior foi copiado. As consultas oficiais aparecem vazias na instalação limpa. Os testes exercitam contratos de fonte com respostas controladas; não houve nova coleta PNCP/IBGE neste envio. A pequena coleta real anterior continua documentada na [matriz histórica](../implementacao/MATRIZ_FONTES.md) e em [três amostras públicas revisadas](amostras-publicas-historicas.json).

Playwright criou dados fictícios, verificou cálculos persistidos, CSV baixado, assistente offline, custos privados, documentos, isolamento A/B, teclado, axe, recuperação de 503 e navegação. Sem fatos oficiais carregados, a rota de detalhe de uma compra pública não entra no roteiro de 22 rotas desta cópia. Na execução anterior havia 23 rotas; não atribuimos essa cobertura à instalação nova.

## Ajustes necessários para versionar na raiz

- Código mantido em `backend/`, `frontend/`, `dados/` e `scripts/`, sem a pasta envoltória antiga.
- Resultados brutos encaminhados a `.runtime/evidencias/`, impedindo escrita nas entregas anteriores.
- URLs e portas locais configuráveis, para testar sem interferir no ambiente aberto.
- Bootstrap usa construtores de conexão, em lugar de interpolar a senha em literais de URI. Credenciais continuam somente no runtime ignorado.
- Roteiro de consulta oficial cobre também a base vazia; não depende de uma coleta externa para passar.
- README e índice adaptados; referências históricas identificadas. Scripts internos de empacotamento/baseline, dependentes de caminhos pessoais, não foram redistribuídos.

Não houve alteração das fórmulas V4 nem redesenho do Observatório.

## Falhas e avisos preservados antes do envio

1. As falhas da rodada original e suas correções continuam descritas em [LOG_TESTES](../implementacao/LOG_TESTES.md). Os relatórios brutos originais permanecem no workspace anterior.
2. A primeira invocação desta auditoria Python usou `--disable-pip` sem `-r` e terminou com código 2. O comando foi corrigido para auditar os pacotes instalados; a execução válida retornou zero vulnerabilidades. O README contém o comando corrigido.
3. O scanner complementar identificou três construções dinâmicas de URI no bootstrap, sem senha literal. A revisão confirmou interpolação de valores gerados no runtime. O código passou a usar construtores de conexão; não foi criada exceção para ocultar esses apontamentos.
4. `git diff --cached --check` retornou 2 para espaços/finais de linha herdados, incluindo CSV histórico, licença Manrope e linhas vazias finais. São avisos de formatação; os arquivos de referência foram preservados. Não é falha nos testes funcionais ou detecção de segredo.
5. O build mantém dois avisos `use client` da biblioteca de ícones. Pytest mantém a depreciação TestClient/httpx e o aviso da chave propositalmente inadequada do teste de rejeição HS256. Playwright registra `NO_COLOR`/`FORCE_COLOR`. Esses avisos estão nas saídas revisadas.
6. A primeira conferência dos links identificou 51 referências sem destino na seleção inicial de documentos. Três referências técnicas foram incluídas; as ligações para a galeria antiga foram substituídas pelo acesso à seleção atual, sem importar imagens antigas. A conferência final passou.

Nenhuma falha funcional permaneceu nas execuções finais listadas. Os controles testados não substituem auditoria independente ou prontidão para produção.
