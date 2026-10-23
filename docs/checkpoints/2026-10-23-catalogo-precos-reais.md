# Checkpoint local de catálogo e preços reais — 23/10/2026

Base preservada: `a83e3205e685370e12ad6c42bd17f57bba20a6ff`. Nova branch exclusiva: `checkpoint/irps-catalogo-precos-reais-2026-10-23`. Sem atualização de main ou dos PRs, sem deploy.

## Código incluído

Login operacional único; catálogo nacional paginado e importação verificável; identidade e histórico PNCP com evidências; preços públicos Compras.gov.br consultados por código CATMAT/CATSER, com cache, erros explícitos e proveniência; importação mensal idempotente; migração aditiva 0015; testes backend e jornadas Chrome. As oito unidades V4 e as sete referências visuais permanecem intactas.

## Instalação operacional

Prepare as dependências e o PostgreSQL local com `scripts/preparar_ambiente.ps1`, como descrito no README. Esse primeiro bootstrap é exclusivo de QA e contém exemplos. Para criar **outro banco**, vazio e com um único operador, execute na raiz:

```powershell
& .\.venv\Scripts\python.exe scripts/preparar_operacional.py --credentials-from .runtime/config-local.json
& .\scripts\iniciar_operacional.ps1
```

O primeiro comando reutiliza somente as credenciais do servidor local e gera uma configuração e uma senha privadas em `.runtime/operacional-local/`. Não imprime nem publica a senha. A aplicação operacional abre em `http://127.0.0.1:5296/`, API em 5295. Não substitua a configuração existente: o preparador a preserva. O banco existente deve receber `alembic upgrade head` com seu `IRPS_LOCAL_CONFIG` explicitamente selecionado; a revisão atual é **0015**. Faça backup antes e nunca use um banco de produção.

Os dados consultados anteriormente não acompanham o clone. Os scripts `baixar_catalogos_oficiais.py`, `importar_catalogo_nacional.py`, `coletar_piloto_catalogo_historico.py` e `importar_precos_mensais.py` disponibilizam ajuda e validações de origem/alvo. A importação mensal exige evidência de backup restaurado e parâmetros explícitos: não é executada pelo simples início da aplicação. O verificador `verificar_operacional.py` foi preservado como ferramenta histórica do piloto 0014; sua asserção fixa de revisão não valida o checkpoint 0015. Não interprete essa ferramenta antiga como verificador genérico da revisão atual.

## Resultados realmente executados na preparação desta entrega

- Python: `python -m pytest backend/tests -q --tb=short`, em PostgreSQL descartável novo: **316 aprovados e 200 subtestes aprovados**, 116,62 s.
- Regressão posterior do histórico/contrato/cenários: **45 aprovados**, 16,38 s.
- Testes específicos de cache/preços e importação mensal: **15 aprovados**.
- Frontend: `npm.cmd run build`, TypeScript e Vite aprovados.
- Playwright real: `qa/urgent-prices-real.spec.ts`, com `IRPS_URGENT_REAL=1`, **1 jornada aprovada**, Chrome com sandbox; sem mocks na consulta operacional. Os demais testes reais têm flags próprias e dependem de preparação local.
- Migração 0015 aplicada e reaplicada em banco descartável; importação repetida sem duplicação; oito tabelas verificadas com RLS forçada no ambiente operacional.
- Falha intermediária preservada: repetir a suíte completa em um banco QA já reutilizado deixou uma fixture de histórico sem normalização suficiente (315 aprovados, 1 falho). A mesma suíte passou integralmente em banco novo. Não foram enfraquecidas as asserções nem alterado o comportamento para acomodar a fixture.

Esses são resultados de execução da rodada que originou este código, não uma promessa de disponibilidade permanente das APIs externas. Logs integrais, XML, capturas e configurações permanecem locais. Os relatórios históricos abaixo podem mencionar esses artefatos locais, que foram deliberadamente excluídos da publicação pública.

## Dados efetivamente observados e limites

No banco operacional local: 345.575 códigos CATMAT e 3.104 CATSER, total 348.679, reconciliados com snapshots oficiais. Isso comprova disponibilidade do catálogo, não histórico de compras para todos os códigos.

O piloto mensal de setembro/2026 importou 139.321 linhas (114.029 de materiais, 25.292 de serviços), com 43.563 códigos existentes no catálogo: **12,49372632%** dos 348.679 códigos possuem preços nesse recorte mensal local. Um código de serviço não encontrado no catálogo foi preservado para revisão, sem remapeamento de namespace. Há 26.019 linhas sem unidade; não geram comparações indevidas. A conciliação CATSER 14729 registrou diferença de uma linha entre API e arquivo mensal, sem causa comprovada; as fontes permanecem separadas.

O histórico PNCP limitado contém 495 fatos de fases diferentes, que não representam 495 compras independentes. Catálogo, preços, publicação, homologação e contrato são apresentados separadamente. Ausência de registro não comprova ausência de compras, necessidade futura ou consumo. Não há alegação de cobertura municipal completa.

## Auditoria antes da publicação

Varredura dos arquivos candidatos, comparação em memória com segredos das configurações locais e inspeção dos 532 blobs alcançáveis no histórico Git. Nenhuma correspondência com os segredos locais nem token de provedor ou chave privada nos candidatos. Uma URI histórica comentada foi classificada como template: usuário, senha e host compostos por placeholders explícitos. O `.env.example` atual mantém URLs vazias.

Bancos, backups, credenciais, sessões, arquivos de configuração privados, ZIPs brutos, capturas e logs operacionais ficam fora do commit. Nenhum candidato acima de 5 MB. A verificação reduz o risco de exposição, sem constituir garantia universal de ausência de segredos.

## Relatórios técnicos preservados

- [Login único e piloto real](../IRPS_PILOTO_REAL_LOGIN_UNICO/RELATORIO.md).
- [Comandos do piloto](../IRPS_PILOTO_REAL_LOGIN_UNICO/COMANDOS.md).
- [Catálogo e histórico](../IRPS_CATALOGO_HISTORICO_REAL/RELATORIO_CATALOGO_HISTORICO_REAL.md).
- [Histórico e preços: correções e limites](../IRPS_URGENTE_HISTORICO_PRECOS/RELATORIO_URGENTE.md).

As restrições de não publicar registradas nesses relatórios eram válidas durante sua execução. A publicação deste checkpoint foi posteriormente autorizada expressamente pelo usuário. Segurança de produção, documentos administrativos, expansão de cobertura e ajustes manuais de quantidade não são aprovados por este commit.
