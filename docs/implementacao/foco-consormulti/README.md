# Portfólio CONSORMULTI — execução local

Aplicação verificada: **http://127.0.0.1:5298/#/portfolio**. API correspondente: http://127.0.0.1:5297/health . Mesmo operador e senha operacional já configurada; nenhuma senha consta nesta documentação. Instâncias anteriores em 5295/5296 foram preservadas e não são a referência para validar as novas rotas.

## Abrir e iniciar

Na raiz Windows real do Painel_IRPS, com PostgreSQL e configuração operacional existentes:

```powershell
.\scripts\iniciar_foco_consormulti.ps1
```

O script reutiliza as portas quando já estão disponíveis, confere o contrato da API existente, deriva configuração privada de loopback e não inicia coletores. Não instala dependências ou cria contas. Se uma porta da API contiver outra versão, o script recusa encerrá-la; escolha portas distintas explicitamente. O teste desta rodada reutilizou as instâncias já iniciadas pelo terminal.

Para operação em terminais controlados, use a configuração privada derivada, sem copiar seus valores:

```powershell
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/irps-fcp/operational-preview-config.json).Path
.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 5297 --app-dir backend --no-access-log
```

Em outro terminal:

```powershell
$env:IRPS_API_PORT='5297'
$env:IRPS_FRONTEND_PORT='5298'
npm.cmd --prefix frontend run dev
```

Para parar/reiniciar uma instância aberta no terminal, use Ctrl+C **somente nesse terminal** e execute novamente seu comando. Não encerre PostgreSQL, coletores ou processos antigos para liberar portas. Instâncias iniciadas pelo script ficam ocultas; identifique seus processos antes de encerrá-las manualmente. A rodada não alterou configuração de início automático do Windows.

## Jornada comprovada

1. Entrar com o operador existente: aparecem vinte grupos.
2. Compra de veículos → Ipatinga → Homologado → Aplicar e salvar filtros → Compras dos municípios. Conferir utilitário, fornecedor e resultado PNCP.
3. Material de informática → Timóteo → Publicado/estimado → Aplicar filtros. Conferir os registros da **Câmara**, com CNPJ próprio, sem chamá-los de compras da prefeitura.
4. Café → código **463562** → Abrir ficha → Consultar preços nacionais. Os arquivos de doze meses continuam separados do histórico municipal.
5. Fontes e cobertura mostra consultas parciais e fontes bloqueadas. Ausência de vínculo com o código não significa ausência de compras.
6. Ficha selecionada pode abrir o planejamento existente com código e snapshot. Não cria IRP, necessidade V4, aprovação ou manifestação automaticamente.

## Testes e auditoria

```powershell
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/irps-fcp/final-qa-config.json).Path
.venv/Scripts/python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend run build
$env:IRPS_BASE_URL='http://127.0.0.1:5298'
$env:IRPS_FCP_OPERATIONAL='1'
Set-Location frontend
npx.cmd playwright test fcp-portfolio.spec.ts --reporter=list
```

O arquivo final-qa-config.json aponta ao QA descartável, **nunca ao banco operacional**. Não execute seed/testes Python sobre a configuração do operador. Os testes de navegador operacionais consultam fatos reais e salvam somente preferências, sem gerar compras ou documentos de demonstração.

Para um lote de coleta PNCP, após conferir backup e inexistência de outro worker:

```powershell
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/operacional-local/config.json).Path
.venv/Scripts/python.exe scripts/executar_campanha_municipal.py --execute --ticks 1 --refresh-every 1
```

Sem `--execute`, o comando mostra uma prévia. Não há serviço de coleta contínua novo ativo. Os checkpoints permanecem no PostgreSQL e no diretório privado; a fila antiga M/D/X está pausada por decisão do usuário, sem exclusão.

Relatórios: FCP01.md a FCP09.md, FCP02_MATRIZ.md, FCP04_FONTES.md e FCP_RELATORIO_FINAL.md nesta pasta. Evidências privadas em .runtime/irps-fcp, sem capturas. Nunca versionar configurações privadas, dump ou arquivos brutos de consulta.
