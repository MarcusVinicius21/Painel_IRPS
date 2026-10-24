# LX03 — Integração incremental ao IRPS

Estado: **parcial operacional**. Quatro capacidades aprovadas foram conectadas; as falhas das demais não foram ocultadas.

## Contratos e execução

- `GET /api/v1/portfolio/licinexus`: últimos vinte pedidos da organização, instalação, versão e limites. Não retorna corpo cadastral, chave ou comando MCP.
- `POST /api/v1/portfolio/licinexus`: `fact_id`, `group` (01–20), `operation` (`items`, `results`, `documents`, `contract`). Autenticação, CSRF e `sources.sync` preservadas. Exige fato oficial atual, órgão municipal e alvo monitorado. Parâmetros adicionais são recusados.
- Pedidos persistem no `job` existente. Identidade de idempotência usa provedor + evento oficial + operação, sem duplicar o mesmo pedido por ter sido aberto por item, resultado, grupo ou publicação. Repetição recente retorna o pedido existente.
- Worker existente executa um complemento por vez sob a trava `irps-public-history-runner:<org>`. Concessão expirada é recuperável; 429/503 provocam pausa do host e até três tentativas. Não se criou segundo coletor livre ou banco auxiliar.
- No ciclo municipal, publicações salvas sem itens podem gerar um pedido. As regras existentes dos vinte grupos são usadas como prioridade textual, jamais vínculo técnico; há ainda prioridades por assunto. Descoberta fica limitada a cem publicações por recorte, um pedido pendente, oito requisições por chamada e memória de 192 MB. Isso não comprova varredura completa dos vinte grupos.

## Integridade

O MCP é intermediário; os fatos continuam `PNCP_ITENS` e `PNCP_RESULTADOS`, com identidades, revisões e importadores existentes. `Capture` entrega a resposta real obtida, URL original/HTTP/hash, sem simular requisição ou marcar uma página inexistente na fila histórica. Caminho, host, resposta e tamanho são conferidos; HTTP 404 convertido em lista vazia pelo upstream não é promovido a consulta oficial bem-sucedida.

Ferramenta de itens não expõe paginação comprovada: estado continua parcial e `expected_pages=null`. O parâmetro interno de tamanho é limite de ingestão, não alegação de página solicitada à fonte. Contrato detalhado e arquivos são evidências adicionais, não novos contratos ou pagamentos. Revisões repetidas não são novas compras. Nenhum vínculo CATMAT/CATSER é criado por descrição.

Contexto BrasilAPI de CNPJ/órgão foi testado, mas não importado como fonte governamental direta. Dados pessoais cadastrais e diagnósticos ficam na área privada de testes. O processo de produção não herda chave CGU, configuração de PostgreSQL ou ambiente completo do Codex. Pacote fixado e licença MIT preservada.

## Piloto operacional comprovado

Comparação por `(provider,event_identity)` contra baseline operacional de **24/10/2026 04:06:36 BRT**; corte de auditoria **04:51:36 BRT**:

- **10 identidades inéditas de itens** de informática: Câmara Municipal de Ipatinga, CNPJ público `19871680000147`, compra `19871680000147-1-000074/2025`. Origem: `https://pncp.gov.br/api/pncp/v1/orgaos/19871680000147/compras/2025/74/itens`.
- **3 identidades já existentes revisitadas**: dois itens de veículos e um resultado homologado de Ipatinga. Foram preservadas revisões; não foram contadas como compras inéditas. A atribuição por documentos vinculados aos pedidos encontrou 14 versões físicas, das quais somente dez identidades inéditas.
- Novo histórico prioritário visível: teclado e mouse da Câmara aparecem como candidatos do grupo 17, sem equivalência nacional aprovada. Os demais oito itens permanecem disponíveis nos fatos/processo, sem forçar enquadramento no portfólio.
- Veículos: dois utilitários homologados por R$ 219.000,00 eram conhecidos; atualização de evidência, não ganho de cobertura ou novo fornecimento.
- **0 municípios adicionais**, **0 vínculos nacionais confirmados novos**, **0 contratos inéditos**, **0 atas**, **0 resultados inéditos**, **0 planejamentos adicionais**. Detalhe de contrato já conhecido e arquivos adicionais foram preservados, sem completar lacunas de fase.

## Interface e filtros

Reutilizada a área municipal do Portfólio Observatório. Novo acompanhamento de consultas, ações por linha, documentos PNCP e estados de ausência/erro. Acrescentados filtros reais de CNPJ fornecedor e fonte aos filtros existentes de município, órgão, grupo, código, período e fase. O filtro de código continua exigindo vínculo comprovado. O contrato é consultado pela operação compatível; não se mostram comandos arbitrários ao usuário.

Nenhum arquivo V4, configuração de login/RLS, catálogo ou preço nacional foi substituído. Sem migração de schema. CATMAT/CATSER continuam manuais aos sábados. Sem push, merge ou deploy.
