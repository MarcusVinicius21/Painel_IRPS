# Execução da cópia para GitHub

Os comandos suportados estão no [README da raiz](../../README.md#instalação-local--windows).
Todos os caminhos são relativos à raiz deste repositório; `irps-app-real/` era o nome da pasta na entrega anterior.

- Instalar: `scripts/preparar_ambiente.ps1`.
- Iniciar: `scripts/iniciar_api.ps1` e `scripts/iniciar_frontend.ps1`.
- Conferir migrações: `python scripts/validar_migracoes.py`, somente no banco descartável `irps_migration_test`.
- Python: `cd backend` e `../.venv/Scripts/python.exe -m pytest -q`.
- Frontend: `cd frontend`, `npm.cmd run build` e, com os serviços ativos, `npm.cmd run qa`.
- Encerrar: Ctrl+C nos terminais e `scripts/parar_postgres.ps1`.

Configuração, chaves locais, banco, resultados brutos e arquivos gerados ficam em `.runtime/`, ignorada.
As portas padrão são 5210/5211/55432. A preparação desta cópia foi testada em portas separadas, descritas em [RESULTADOS](../validacao/RESULTADOS.md).

Os scripts de coleta pública são opcionais. Eles não são necessários para os testes determinísticos e não trazem cobertura histórica completa.
