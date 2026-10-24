# LX04 — Validação local

## Resultados executados em 24/10/2026

| Verificação | Comando / escopo | Resultado |
|---|---|---|
| Python completo, PostgreSQL isolado | `.venv/Scripts/python.exe -m pytest backend/tests -q` | **580 aprovados; 200 subtestes aprovados; 2 avisos**, 161,22 s |
| Foco integração e preços | testes Licinexus e runtime de preços | **18 aprovados**, 2,84 s |
| Extensões de captura, fila e retomada | testes adicionais Licinexus | **7 aprovados**, 2,11 s |
| Build | `npm run build`, em frontend | **Aprovado**, TypeScript e Vite; aviso de diretiva de dependência preservado no log |
| Navegador operacional | Playwright: `ci-monitoring.spec.ts`, `fcp-portfolio.spec.ts`, `licinexus.spec.ts` | **5 aprovados**, 32,7 s; login real, filtros, preços, evidências, nova consulta e responsividade |
| MCP real | initialize, tools/list, prompts/list, resources/list e 18 tools/call | **18 ferramentas testadas**, quatro prompts e dois recursos descobertos; falhas HTTP discriminadas na matriz |
| Mutação dirigida | inversão temporária da validação de caminho da captura | Teste recusou a mutação; código restaurado e testes focados aprovados |
| Schema | inspeção de alterações | Nenhuma migração necessária ou executada nesta rodada |

Logs completos e XML ficam em `.runtime/licinexus/`, fora do versionamento. O arquivo de segurança registra nova varredura ao fechamento. Testes de autorização, organização, RLS, cenários e V4 integram a suíte Python; não se substituiu a base operacional por fixtures.

## Falhas encontradas e corrigidas

- Importação ESM do guard no Windows exigiu URI de arquivo; corrigida sem alterar o pacote externo.
- O caso inicial usava sequência de compra 1642; o caso oficial existente é 164. O erro e a nova tentativa constam da evidência privada.
- Teste de navegador encontrava duas representações responsivas do mesmo item. A verificação foi delimitada à tabela, preservando as verificações de mouse, teclado, fornecedor e fila.
- Testes novos precisaram de pausa expirada determinística e parâmetros SQL com tipos separados. Não se ampliaram permissões para acomodar fixtures.
- A primeira regressão final teve **579 aprovados e uma falha**: a fixture anterior de preços esperava recibos diferentes, mas duas chamadas receberam o mesmo instante no relógio do Windows. Apenas a fixture ganhou relógio determinístico com microssegundos diferentes. Foram mantidas as asserções de recibos diferentes, fingerprint original igual e comportamento do cache. Nenhuma lógica de preços em produção foi alterada. A suíte completa posterior passou.

Os dois avisos finais são de depreciação httpx/Starlette e chave HMAC curta no teste de rejeição de JWT inválido; não representam inspeção ou exposição da chave operacional. Não foram removidos para maquiar o resultado.

## Revisão de interface e preservação

Humanização e revisão React Best Practices aplicadas ao componente de acompanhamento: carregamento/erro independentes, cleanup do temporizador, proteção contra atualização após desmontagem, lista limitada a vinte consultas e paginação de cinco linhas. Foram reutilizados componentes existentes; nenhuma biblioteca visual ou redesign introduzido. Não se mediu ganho de desempenho nem se declara fidelidade pixel-perfect.

Playwright verificou larguras de 390 e 1672 px sem transbordamento horizontal. Não foram geradas imagens nesta rodada. A evidência é textual e automatizada.

Os oito hashes V4, as sete referências, doze arquivos privados de skills/configuração de referência, licença MIT e ausência de artefatos de runtime no diff são conferidos pelo fechamento. O worker usa a fila e trava existentes. Nenhuma fórmula, autenticação ou regra de confirmação municipal foi reescrita.

## Limites de segurança

O pacote fixado é 0.2.1; a versão 0.2.2 consta do GitHub, mas não estava publicada no NPM. O audit acusa dois pacotes com gravidade alta vinculados ao mesmo aviso Zod GHSA-mrhx-c7xc-m3w5. Limites de corpo, profundidade, nós, memória, tempo, hosts e requisições reduzem exposição; **não corrigem a vulnerabilidade upstream**. O uso é local e controlado; aprovação para produção não foi concedida. Não há endpoint MCP público.

As respostas HTTP 503/429, 404 e vazias não foram transformadas em cobertura comprovada. Não há estoque, consumo ou saldo documental de ata demonstrado. Nenhuma ata ou PCA foi integrado sem evidência.

## Fechamento

API reiniciada para carregar o código final; API `/health/ready` e frontend retornaram HTTP 200. A varredura dos **27 arquivos** alterados/novos encontrou zero correspondências de credenciais e nenhum arquivo grande ou de runtime indevido. Doze arquivos privados de referência, oito módulos V4, referências visuais e licença preservados. `git diff --check` aprovado; somente avisos de normalização CRLF/LF. HEAD permanece na base CI09, com oito arquivos rastreados modificados e os novos arquivos listados no relatório. Nenhum commit, push, PR, merge ou deploy.
