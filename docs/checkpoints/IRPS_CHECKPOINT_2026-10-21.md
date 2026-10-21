# IRPS — checkpoint completo do código local (21/10/2026)

## Origem e preservação

Fonte: checkout real Windows de Painel_IRPS, incluindo todas as alterações acumuladas de backend, frontend, migrações, scripts e testes. Base local: e65375414792d4baef6ec1eaa6d7384c398448ca. O ZIP anterior era incremental e não foi aplicado nem usado como substituto do projeto.

Branch exclusiva: `checkpoint/irps-refinamento-visual-2026-10-21`. Publicação em dois commits: implementação acumulada; depois sete referências originais em `docs/design/referencias-irps/`. Não houve mudança de produto, fórmulas, autenticação, permissões ou migrações nesta tarefa. Nenhuma instalação, formatação ou nova execução de testes que modifique o banco foi feita para publicar.

Os oito arquivos V4 conservam os hashes de docs/validacao/integridade-v4.json. Os 18 arquivos fonte presentes no pacote incremental anterior foram confrontados com os arquivos físicos: todos coincidem; a publicação inclui também o código acumulado que não constava naquele pacote.

## Estado funcional preservado

Catálogo CATMAT/CATSER com paginação, histórico municipal com proveniência e comparabilidade, cenários V4, progresso de estudos, preparação de minutas, manifestações documentadas, consolidação e exportações. As migrações 0009–0012, novas rotas, serviços, componentes e regressões locais estão incluídas. O banco e os catálogos brutos não fazem parte do Git: importar snapshots fornecidos é uma etapa local necessária.

As contas demonstrativas exigem ambiente local de testes. Contas produtivas, integrações, cobertura oficial e modelos jurídicos continuam sujeitos aos limites documentados. Este checkpoint não certifica prontidão para produção nem fidelidade visual integral.

## Validações já executadas antes do checkpoint

Na rodada precedente: 185 testes Python e 200 subtestes aprovados; 32 testes Playwright aprovados; build aprovado; migrações em PostgreSQL descartável até 0012, com reaplicação idempotente e RLS; oito módulos V4 preservados. Estes resultados históricos não foram reexecutados na tarefa de preservação. Metadados compactos: docs/IRPS_REFINAMENTO_PIXEL_PERFECT/RESULTADOS_FINAIS.json. Nesta tarefa foram executadas inspeções Git, diff --check, comparação de hashes, auditoria do conteúdo e verificação remota.

## Segurança da publicação pública

O repositório foi confirmado como público. Nenhuma alteração de visibilidade foi feita. Foram examinados arquivos atuais candidatos e todos os blobs alcançáveis pelo HEAD inicial. Os padrões de chaves/tokens/JWT/URIs autenticadas não identificaram segredo real. A única correspondência foi a URI comentada de .env.example, com APP_ROLE e REPLACE_OUTSIDE_GIT, explicitamente fictícia. A auditoria por padrões não substitui uma avaliação de segurança independente.

Ficam exclusivamente no disco local: .runtime, configurações reais, sessões, bancos, uploads, exportações, documentos institucionais originais/gerados, CSVs brutos CATMAT/CATSER, dependências, dist, ZIPs, capturas locais, mapas de diferenças e galerias. Relatórios textuais de engenharia são preservados; seus links para artefatos locais excluídos podem não abrir no GitHub. Isso não significa ausência dos módulos de código.

O ativo gráfico de marca utilizado pelo frontend é somente uma imagem institucional sem dados pessoais ou credenciais; não inclui corpos de documentos, assinaturas ou formulários. As sete imagens publicadas no segundo commit são conceitos autorizados, com valores ilustrativos, sem representar fatos públicos.

## Auditoria Manus — somente leitura

Usar GitHub Connector e selecionar esta branch ou o SHA do segundo commit. Examinar código, migrações, testes e as sete referências isoladamente. Não editar, commitar, fazer push, alterar PRs ou iniciar implementação durante a auditoria. Consultar README.md e manifest.json da pasta de referências. Os originais devem manter os SHA-256 do manifesto.

As branches main, feat/oportunidades-consormulti (PR #1) e feat/cobertura-historica-catalogo-inteligente (PR #2) devem permanecer inalteradas; não haverá merge ou deploy nesta tarefa.
