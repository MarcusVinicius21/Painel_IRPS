# Licinexus no IRPS — resultado da rodada LX01–LX04

**Data:** 24/10/2026. **Estado:** integração parcial operacional, com bloqueios de fonte e dependência. Aplicação local: http://127.0.0.1:5298/#/portfolio. API local: porta 5297. O servidor precisa permanecer ligado para as consultas; não depende de uma conversa interativa no Codex.

## Base preservada e instalação

Pasta real Windows `C:/Users/NEXUS/Downloads/TRAMPOS/IRPs/Painel_IRPS`; branch `feat/cobertura-municipal-12m-2026-10-23`; HEAD inicial e final `5bfd3eeb706b5fbe76e31890c0a6c31f3c4beb7a`. Diff inicial limpo. CI01–CI09 não foram reiniciados, nem a fila antiga executada.

118 alvos, 20 grupos, 7.917 códigos selecionados, 348.679 códigos nacionais, 2.078.067 preços nacionais, um operador e oito módulos V4 preservados. Banco PostgreSQL existente; sem migração nova ou banco adicional operacional.

O [GitHub Licinexus](https://github.com/Licinexus/licinexus-mcp) declara 0.2.2 no código principal; o [NPM](https://www.npmjs.com/package/@licinexusbr/mcp) disponibilizava **0.2.1** como última versão publicada. Foi instalada **0.2.1 fixada**, isoladamente, com lock e licença MIT integral. Scripts de instalação desabilitados, integridade do arquivo conferida. Não foi criada integração global do Codex.

**Ressalva:** dois pacotes acusados no audit, associados ao aviso Zod GHSA-mrhx-c7xc-m3w5. Execução limitada por corpo, estrutura JSON, memória, tempo, hosts e requisições, sem herdar credenciais do IRPS. A vulnerabilidade upstream não foi declarada corrigida; uso em produção exige tratamento adicional.

## Ganho oficial comprovado

Baseline em 24/10/2026 **04:06:36 BRT**; reconciliação final **04:51:36 BRT**, por provedor + identidade oficial, não por soma de linhas/revisões:

| Pergunta | Resultado atribuível ao Licinexus |
|---|---|
| Registros oficiais inéditos | **10 identidades de itens** de uma publicação da Câmara Municipal de Ipatinga |
| Duplicados de identidades já conhecidas | **3 revisitadas**: dois itens e um resultado homologado; não duplicaram compras |
| Versões físicas ligadas aos pedidos | 14; não representam 14 novas compras |
| Municípios adicionais com histórico | **0** |
| Códigos prioritários com novo vínculo técnico confirmado | **0** |
| Contratos, atas, resultados e PCA inéditos | **0 em cada categoria**; houve detalhe de contrato e documentos adicionais como evidência |
| Novos fatos candidatos do portfólio | **2**, teclado e mouse no grupo 17; sem vínculo CATMAT/CATSER aprovado |

Fonte dos dez itens: [PNCP — compra 74/2025 da Câmara de Ipatinga](https://pncp.gov.br/api/pncp/v1/orgaos/19871680000147/compras/2025/74/itens), HTTP 200, hash da resposta e data preservados no PostgreSQL. Não se confundiu Câmara com Prefeitura. Os dez eventos estão discriminados em `LX_NOVOS_EVENTOS.csv`.

O resultado de dois utilitários por R$ 219.000,00 da Prefeitura de Ipatinga já existia: foi atualizado sem ser apresentado como nova aquisição. O contrato 19875020000134-2-000035/2026 de Timóteo também já existia. Publicação, homologação e contrato continuam em fases independentes. Estoque e consumo: **não disponíveis**.

### Comparação com CI09

O relatório CI09 inicial, por volta de 03:18, citava três municípios com candidatos. A última auditoria, às 03:43, já apresentava **quatro**: Água Boa, Ipatinga, Timóteo e Aricanduva. O baseline desta rodada às 04:06 também tinha quatro e o fechamento mantém quatro. A entrada de Aricanduva antecedeu o Licinexus; não é ganho desta integração.

O corte de classificação foi preservado: 11.153 relações; 2.365 diretas, 5.552 pendentes, 525 indiretas e 2.711 excluídas. Os 7.917 códigos selecionados são distintos; relações entre grupos não ampliam essa contagem. Nenhum percentual de cobertura integral dos 118 municípios é afirmado.

## Ferramentas e integração

**As 18 ferramentas foram chamadas individualmente.** A tabela completa, com FUNCIONOU / DADOS / INTEGRADO / PAINEL / BLOQUEIO, está em [LX02_FERRAMENTAS.md](LX02_FERRAMENTAS.md) e no CSV filtrável `LX_FERRAMENTAS.csv`. Foram descobertos quatro prompts e dois recursos sem executar tarefas de IA.

Quatro capacidades foram aprovadas para o fluxo local: itens, resultados, documentos e detalhe de contrato. São consultáveis a partir de identidades oficiais salvas, pela fila durável e worker existente. Itens e resultados usam os importadores PNCP existentes; contratos detalhados e documentos entram como evidências, sem criar outra contratação por mera redescoberta.

Adequadas à atualização automática **limitada**: itens de publicações salvas sem itens, resultados por item conhecido e documentos/detalhes sob demanda. Uma execução por vez, trava compartilhada, checkpoint, retomada de concessão expirada, orçamento de chamadas e pausa em 429/503. Não existe varredura completa garantida nem um segundo coletor livre. CATMAT/CATSER permanecem com atualização manual aos sábados.

Buscas amplas de licitações, contratos, atas, fornecedores, PCA e análises agregadas receberam 503/429. Instrumentos retornaram 404 disfarçado pelo pacote como lista vazia; foram recusados como evidência de ausência. Termos tiveram resposta vazia válida. Detalhe de ata e itens PCA não tiveram sequência descoberta e confirmada: **inconclusivos**, sem histórico importado. CNPJ/órgão tiveram fallback BrasilAPI; cadastro complementar não foi promovido a fonte governamental de compras.

## Uso no painel

Entrar com o operador existente → Portfólio → Material de informática → município Ipatinga → situação Publicado/estimado → Compras dos municípios → órgão `19871680000147` → fonte PNCP_ITENS. Teclado e mouse aparecem com origem; abrir a linha permite pedir complemento de documentos. Filtros de fornecedor e fonte foram ligados ao backend, preservando município, órgão, grupo, código, período e fase. Código oficial exige correspondência aprovada; candidato textual não recebe vínculo automático.

## Código e validação

Novos módulos `licinexus.py` e `licinexus_runtime.py`, guard Node, lock/licença e componente `LicinexusStatus.tsx`. Extensões pequenas em providers, scheduler, sources, histórico, rotas e Portfolio. Testes novos de captura, isolamento, idempotência, retomada e navegador; fixture anterior de relógio tornada determinística sem alterar asserções ou produção. Contratos aditivos detalhados em [LX03_INTEGRACAO.md](LX03_INTEGRACAO.md).

**580 testes Python + 200 subtestes aprovados; build aprovado; cinco testes Playwright aprovados.** Falhas intermediárias, correções e limites estão em [LX04_VALIDACAO.md](LX04_VALIDACAO.md). Regressões cobrem V4, organização, RLS, cenários e funcionalidades anteriores. Sem alteração no núcleo ou referências, sem imagens novas. Segurança: conferência de segredos, arquivos grandes/indevidos e diff local ao fechamento, sem imprimir credenciais.

**Limites remanescentes:** disponibilidade das rotas de consulta; aviso Zod; paginação dos itens não comprovada pelo MCP; ausência de novas atas/PCA/instrumentos; equivalência técnica de teclado/mouse ainda sujeita à revisão. Não se afirma cobertura completa, consumo, estoque, saldo de ata ou pagamento.

Todas as alterações permanecem locais. **Sem commit, push, PR, merge ou deploy.** Checkpoint em `LX_STATUS_GERAL.json`; instruções em `RETOMAR.md`. Logs e corpos de respostas ficam na área privada `.runtime/licinexus`, excluída do versionamento.
