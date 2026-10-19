> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Testes executados e evidências

## Contagens separadas

| Verificação | Resultado | Evidência |
|---|---|---|
| Casos Python da aplicação | 115 aprovados: 65 regressões históricas + 50 casos da integração atual | `evidencias/pytest-final.txt`, XML correspondente |
| Verificações internas do V4 | 200 aprovadas dentro dos casos históricos | Saída pytest; não somar como 200 novos casos independentes |
| Referência do pacote instrutivo | 21 aprovados | `pytest-referencia.xml`; não substitui os testes reais |
| Playwright | 11 roteiros aprovados | `playwright.json`, `playwright-final.txt` |
| Larguras no fluxo completo | 320, 390, 768, 1024 e 1440 px | Imagens por largura, CSV baixado e resultado API |
| Rotas autenticadas | 23 rotas verificadas em 390 e 1440 px | `rotas-390.json`, `rotas-1440.json` |
| Migrações | Upgrade → downgrade → upgrade no PostgreSQL real | `migracoes.json`: 30 tabelas, zero após reversão, 30 após reaplicação |
| RLS e papel SQL | App sem superusuário/bypass; sem contexto vê zero cenários | Teste negativo e `navegador-api-banco.json` |
| TypeScript/Vite | Compilação e build aprovados | `build.txt` |
| Dependências Python/npm | Nenhuma vulnerabilidade conhecida nos snapshots finais | `pip-audit.json`, `npm-audit.json` |

O XML pytest contém também as subverificações e pode exibir 315 entradas. A contagem de **casos** no console é 115. As quantidades acima não são somadas para gerar um número promocional único.

Não foi criada uma suíte unitária TypeScript que repita o V4: a matemática fica no servidor. A UI é verificada por typecheck e Playwright com serviços reais.

## Comandos

```text
python scripts/validar_migracoes.py
cd backend
python -m pytest -q --junitxml=../../.runtime/evidencias/pytest-final.xml
cd ../frontend
npm.cmd run build
npm.cmd run qa
```

Foram usados o ambiente `.venv` e configurações explícitas do projeto; veja os comandos PowerShell completos em `COMO_EXECUTAR_LOCAL.md`. Referência instrutiva: `python -m pytest IRPS_RODADA_IMPLEMENTACAO_MAXIMA_01/reference/tests -q`, com o pacote no `PYTHONPATH`.

## O que os testes realmente exercitam

- Token com assinatura errada, expiração, nbf futuro, issuer/audience errados, algoritmo/kid indevidos e claim ausente.
- Sessão ausente, CSRF, origem externa, logout, membership revogado e cache anterior.
- RLS com duas organizações; custos privados, documentos, ferramentas, exportações e jobs por ator/organização.
- Modo A: 3/10/20/118 participantes; Modo B: confirmação e limites com três participantes; retirada sem inflar remanescentes; entrada sem inventar insumos; limites inviáveis; confirmação invalidada.
- Unidade e versão incompatíveis no preço; referência ausente; estoque/recebimentos desconhecidos.
- 118 × 100: 11.800 linhas gravadas, paginação e CSV/XLSX/PDF reabertos com conferência do conjunto.
- Contratos com respostas públicas de teste, revisões novas e repetição de versão antiga sem reativação indevida.
- Leitores de quatro formatos; fórmula sem cache preservada; original idêntico; revisão concorrente; reprocessamento por nova versão sem alterar original.
- ZIP com caminho indevido, macros, vínculos externos, proporção excessiva, formato falso, tamanho excessivo e instruções embutidas.
- 429/503 sem apagar histórico; Retry-After; catálogo sem criar compra; reserva de orçamento concorrente e gasto incerto.
- Interface conectada: sessão, criação, cálculo, quantidade, download, assistente, lucro privado, leitura/revisão e troca de conta.

## L01–L07

| Limite anterior | Correção comprovada |
|---|---|
| L01 obrigação de A usada para B | Cidade/item/versão/obrigação são resolvidos no banco e no acesso; B não recebe O-A |
| L02 papel higiênico tratado como A4 | Pedido fica em esclarecimento; não há substituição |
| L03 filtro extra ignorado | Schema e consulta recusam campos desconhecidos ou incompatíveis |
| L04 XLSX sem cache vira vazio/zero | Leitura preserva fórmula, aba/célula e proposta ausente, exigindo conferência |
| L05 recebimento desconhecido vira zero | Adapter impede cálculo até informar o recebimento |
| L06 pontuação corrompida | Resposta humana não passa por substituição global de caracteres |
| L07 regra antiga também confundia papel | O roteador novo usa resolução explícita e é o único ativo |

## Acessibilidade, console e rede

axe avaliou a montagem nas cinco larguras, fontes em 390 px e simulação comercial em 1440 px. Os critérios avaliados não apresentaram violações. Os seis arquivos `axe-*.json` registram montagem/fontes; o teste comercial inclui a asserção axe no próprio roteiro. Não é auditoria integral WCAG.

Foco ao fechar o assistente, navegação por teclado, labels explícitos, navegação mobile e ausência de overflow foram verificados. As rotas adicionais passaram por revisão de títulos/ações sem jargões vetados, mantendo descrições oficiais intactas.

Os arquivos `browser-*.json` registram diagnósticos sem conteúdo privado. O 401 inicial ao consultar uma sessão inexistente é esperado. Chrome sinaliza `ERR_ABORTED` ao transformar a navegação do arquivo em download; o arquivo foi salvo e validado em cada largura. Não houve exceção JavaScript ou erro HTTP inesperado nos roteiros aprovados. Isso não significa ausência absoluta de qualquer mensagem no console.

## Falhas preservadas e corrigidas

1. Migração inicial: `%I` de PL/pgSQL foi interpretado pelo driver como parâmetro; execução DDL foi corrigida.
2. Dependências herdadas: lock continha vínculos locais; a instalação nova foi feita pelo registro, com lock independente.
3. Primeiro pytest: faltava o CSV histórico exigido pelo teste do V4; copiado sem alteração, separado do cadastro conciliado usado pela aplicação.
4. Seletores de teste: tabela mobile e labels de select exigiram nomes/escopo explícitos.
5. Em 1024 px, a mensagem encobria o assistente; posição foi corrigida.
6. Após restringir UPDATE em originais, o bloqueio de revisão documental exigia esse privilégio. Foi substituído por advisory lock transacional, mantendo a imutabilidade.
7. Repetição de revisão histórica PNCP provocava conflito de unicidade. A ingestão agora ignora conteúdo já conhecido, sem reativar versão antiga.
8. Teste de troca de empresa aguardava a navegação antes da confirmação da nova identidade. O roteiro foi corrigido e verifica também a recusa 404 do custo de A para B.
9. CSV passou a propor campos por cabeçalho. Nova leitura preserva original e abre outra revisão quando muda o parser.

Os resultados anteriores estão em `pytest-inicial`, `pytest-endurecimento-inicial`, `pytest-retificacao-inicial`, `playwright-terceira-execucao`, `playwright-quarta-execucao` e `antes-csv-paginacao-*`. Execuções iniciais de navegador interrompidas após falha não são contabilizadas como aprovadas.

## Avisos que permanecem

O build registra duas diretivas `use client` da biblioteca de ícones; a aplicação Vite permanece cliente e passou nos fluxos. O TestClient registra depreciação da compatibilidade httpx e um aviso da chave deliberadamente inadequada no teste de algoritmo rejeitado. Nenhum aviso foi ocultado para declarar sucesso. A instalação inicial do pip continha avisos de vulnerabilidade; o pip isolado foi atualizado, com auditoria inicial preservada e versão fixada no instalador.

## Esforço do usuário

Veja `MATRIZ_INTERACOES.md`. Medidas são amostras de automação local, não entrevistas nem benchmark humano. São registradas separadamente: cliques DOM, campos alterados, rotas percorridas e tempo. Ações `selectOption` não simulam cada clique de abertura de uma lista; esse limite é declarado no indicador.

A recuperação de interface também foi exercitada com uma resposta 503 controlada. Ao restaurar a consulta, os IDs dos documentos continuaram iguais. O caso adicional é registrado em `recuperacao-interface.json`; a recusa 503 é proposital e fica fora dos fluxos normais.
