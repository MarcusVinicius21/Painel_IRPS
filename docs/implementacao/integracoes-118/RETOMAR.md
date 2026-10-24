# Retomada — integrações e 118 alvos

## Estado atualizado após CI09

CI03–CI09 foram executadas nesta continuação. O texto abaixo é o checkpoint histórico de CI02 e **não deve ser reexecutado**. Backup atual foi restaurado e conferido; 118 alvos estão ativados; migração atual é 0018. Skills confirmadas na sessão, sem reinstalação. Usar `CI_STATUS_GERAL.json` e `CI_RELATORIO_FINAL.md` como estado atual.

CGU autenticada e chave privada DPAPI; não solicitar nem imprimir o segredo. Portal MCP somente POC isolada por alertas de dependências. Licitei mantém amostra após reinício, mas busca ainda sem retorno e adoção AGPL pendente. Cobertura municipal permanece parcial; agenda do backend segue enquanto o servidor estiver ligado.

Retomada: confirmar Git, serviços e testes posteriores; não repetir CI01–CI08, não refazer FCP nem reabrir M/D/X. Prosseguir apenas nas lacunas específicas aprovadas em novo pedido. Não presumir cobertura integral ou vínculos de catálogo revisados. Não fazer push, PR, merge ou deploy.

Para abrir o ambiente existente: `powershell -File scripts/iniciar_foco_consormulti.ps1`, com PostgreSQL previamente em execução. A configuração privada derivada habilita o worker; nenhuma senha consta neste documento. Não reinicializar o banco.

## Checkpoint histórico de CI02

Este checkpoint pertence à ordem de 24/10/2026. Não retomar M/D/X, repetir FCP nem reinstalar as sete skills.

Abra o mesmo projeto e esta conversa no próximo turno. Caso as skills não apareçam no catálogo, feche normalmente o aplicativo Codex, abra-o novamente e retome esta conversa. Não pare o PostgreSQL; uma reinicialização do Codex não é uma reinicialização do banco.

Mensagem de continuação:

> Continue a ordem INTEGRAÇÕES 118 pelo checkpoint em docs/implementacao/integracoes-118/CI_STATUS_GERAL.json e RETOMAR.md. Confirme as sete skills instaladas, leia as pertinentes e comprove o carregamento de CI02. Conclua o backup atual restaurado pendente de CI01; a recuperação do PostgreSQL e a reconferência SQL já passaram, mas confira disponibilidade e mudanças posteriores. Depois execute CI03–CI09 sequencialmente, sem refazer FCP, sem retomar M/D/X e sem push, PR, merge ou deploy. Preserve o banco existente e os oito V4. Faça somente os commits locais por etapa testada previstos na ordem original.

## Antes de qualquer mutação operacional

1. Confirmar branch, HEAD e diff; preservar trabalho posterior a este checkpoint.
2. `pg_isready` em loopback 55433 e log de recuperação. Se ainda em recuperação, aguardar e diagnosticar; nunca excluir PID ou recriar cluster para contornar.
3. Reconferir migração 0016, RLS/FORCE RLS, único operador, 20 grupos, 348.679 códigos, 24 snapshots e 2.078.067 preços. Usar configuração privada existente sem imprimir valores.
4. Gerar backup **atual**, restaurar em banco descartável novo e conferir contagens antes da importação dos municípios.
5. Validar lista de 118 contra IBGE oficial, conservar aliases/origem; não presumir filiação. As quatro diferenças nominais estão em CI01.md.

## Ordem restante

CI03: 118 alvos idempotentes, filiação distinta de monitoramento, sem seed. CI04: processos isolados e smoke tests dos repositórios, com gates AGPL/licença/chave. CI05: registro único de provedores e proveniência. CI06: coleta incremental auditável. CI07: agenda persistente sem coletor duplicado e catálogo exclusivamente manual. CI08: interface existente. CI09: testes operacionais, matriz e entrega.

O pacote original permanece em Downloads: `IRPS_ORDEM_CODEX_INTEGRACOES_118_2026-10-24.md` e ZIP correspondente. Ambos os Markdown anexados têm SHA256 `801c883d470d9ffcfb267e7ed8eb38c6a26cd57935b2ed251a2aea846b1ebb24`. O ZIP contém a mesma ordem, LEIA_ME e manifesto, integralmente lidos; não contém código de produto para reaplicar.

Instalação dev não significa integração de dados concluída. Nenhuma das CI03–CI09 foi executada neste checkpoint.
