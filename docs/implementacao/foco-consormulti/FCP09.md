# FCP09 — Aceite, regressões e limites finais
Status: PARTIAL

Executadas as nove tarefas em sequência, com um commit local por tarefa e fila M/D/X preservada/pausada. O relatório consolidado e as instruções estão em FCP_RELATORIO_FINAL.md e README.md. Não houve push, PR, merge, deploy ou imagens.

## Testes realmente executados

- Banco **novo** irps_fcp_final_9f06fea069, migração até 0016 e seed restrito ao modo local_test: suíte Python completa **551 testes e 200 subtestes aprovados**, 150,81 segundos. JUnit privado com zero falhas, erros ou skips. Inclui segurança, autorização, cenários, documentos/IRP, isolamento, histórico e V4. Avisos: depreciação Starlette/httpx e chave HMAC curta de uma fixture deliberadamente inválida do teste JWT; não representam uso dessa chave no operacional.
- Após completar filtros ativo/inativo/subgrupo e filtragem de fornecedores antes da paginação: **8 testes direcionados aprovados**, 2,35 s, preservando asserções de permissão, isolamento e identidade. Essas correções finais são registradas neste commit FCP09.
- Build TypeScript/React/Vite aprovado. Avisos preexistentes de diretiva lucide e bundle >500 kB; não foram ocultados. Build repetido após os textos finais.
- Playwright real Chrome headless no operacional: **3 aprovados**, 18,0 s na última execução. Login único, dados oficiais de Ipatinga/Timóteo, fornecedor documentado, preço nacional CATMAT 463562, ativo/subgrupo, filtros salvos, ausência de vínculo e falha de complemento sem bloquear a leitura.
- Responsividade em 320/390/1536 px, foco e axe no conteúdo novo: **zero violações**, sem screenshots. Isso não certifica todos os módulos antigos nem fidelidade pixel-perfect.
- Migração nova/segunda execução/downgrade vazio QA/reupgrade e RLS/FORCE RLS de quatro tabelas aprovados em FCP03. Backup integral efetivamente restaurado, hash e contagens preservadas em FCP05.
- Auditoria dos arquivos rastreados: **558 arquivos textuais examinados, zero possíveis segredos detectados e nenhum arquivo rastreado >5 MB**. Guarda byte a byte dos oito V4 e sete referências preservada. Novo script examinado pelo parser PowerShell e executado reutilizando os serviços existentes sem duplicá-los. Stage final seletivo e diff --check aprovados.

## Funcionamento real e desempenho

API 5297/OpenAPI contém as rotas novas; interface 5298 operacional. HTTP autenticado: grupos 20 em 0,030 s; código café 463562 em 0,014 s; histórico homologado de veículos em 0,072 s; matriz 264 células em 1,930 s; fontes em 0,016 s. Medidas locais com banco já aquecido, não benchmark de grande escala. Saúde dos serviços antigos e novos: 200; nenhum processo anterior foi encerrado.

Verificação final READ ONLY: 348.679 códigos, 2.078.067 preços, 24 snapshots, 1.755 versões físicas de fatos, um ator/organização/vínculo e dois municípios. O aumento de 113 versões físicas em relação ao baseline não é contagem de compras. Nenhum preço nacional foi reimportado. Resumo nacional: 125.493 códigos materiais e 2.286 serviços com preços, total 127.779, ou **36,6466%** do catálogo. Não é cobertura municipal.

Correções de aceite finais: controles de ativo/inativo e subgrupo já disponíveis na API passaram a constar na UI e nas preferências; fornecedor é filtrado antes da paginação; última consulta é exibida na cobertura. Rótulo de instrumento PNCP não afirma execução financeira. UUID de snapshot deixou de ser metadado cru na ficha, sem perder sua referência no contrato. Não se alterou V4, regra de quantidade manual ou manifestações.

## O que impede aceite integral

Os vínculos municipais encontrados são majoritariamente candidatos por descrição, não todos revisados tecnicamente ou associados a CATMAT/CATSER. Não há confirmação comercial registrada. Grupo 09 exige decisão terminológica. Cobertura das doze competências é parcial; atas/documentos sem fatos estruturados não aparecem como quantitativos. TCE/portais financeiros permanecem bloqueados ou em revisão. Não se promete série de consumo, recorrência comprovada ou previsão. O coletor é retomável por lote; não foi ativado como serviço contínuo.

Não se declara “100% funcionando” em substituição a esses critérios. O aceite funcional e as lacunas estão separados no checklist do relatório final. Evidências contêm somente testes e informações públicas locais; configurações, backups e sessões não entram na entrega versionada.
