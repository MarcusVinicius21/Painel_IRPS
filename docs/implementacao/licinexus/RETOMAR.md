# Retomada segura LX01–LX04

Ler `LX_STATUS_GERAL.json`, os relatórios e o diff local antes de editar. Base Git conhecida: `5bfd3ee`, branch `feat/cobertura-municipal-12m-2026-10-23`. O incremento permanece local, sem commit. Não reinstalar nem repetir o piloto: o pacote 0.2.1 já está em `.runtime/licinexus/service` e os pedidos/evidências estão no PostgreSQL.

Não retomar CI01–CI09 ou a fila M/D/X/63. As capacidades com HTTP 503/429 e as sequências de ata/PCA sem identidade confirmada estão registradas como bloqueios, não como ausência de compras. O próximo trabalho deve partir de uma pendência específica, sem reimportar o catálogo ou preços.

Ambiente local: PostgreSQL existente em 55433, API 5297 e frontend 5298. Usar a configuração privada já existente; nunca imprimi-la. Launcher existente `scripts/iniciar_foco_consormulti.ps1` habilita o worker na configuração derivada privada. Um restart do backend retoma jobs persistidos, respeitando concessões e pausa por host. Não reinicializar o banco.

Instalação reprodutível em outra máquina: `integrations/licinexus/README.md`, manifesto e lockfile. Auditoria Zod continua uma limitação; não expor servidor MCP publicamente. Nenhuma chamada de IA paga, chave nova ou deploy foi autorizada.
