# Comandos executados

Todos partiram da pasta real do repositório, salvo `npm/npx` executados em `frontend`.

```powershell
.venv/Scripts/python.exe scripts/preparar_operacional.py --credentials-from .runtime/sequence-05-06/config-browser.json
./scripts/iniciar_operacional.ps1
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/sequence-05-06/config-browser.json).Path
.venv/Scripts/python.exe .runtime/piloto-real-login-unico/migrar-qa.py --evidence-dir .runtime/piloto-real-login-unico
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/piloto-real-login-unico/config-migration.json).Path
.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short --junitxml=.runtime/piloto-real-login-unico/python-final.xml
.venv/Scripts/python.exe -m pytest backend/tests/test_observed_identity.py backend/tests/test_operational_login.py -q --tb=short
npm.cmd --prefix frontend run build
$env:IRPS_OPERATIONAL_REAL='1'
$env:IRPS_BASE_URL='http://127.0.0.1:5296'
# Dentro de frontend:
npx.cmd playwright test qa/operational-real.spec.ts --reporter=list
# De volta à raiz:
$env:IRPS_LOCAL_CONFIG=(Resolve-Path .runtime/operacional-local/config.json).Path
.venv/Scripts/python.exe scripts/verificar_operacional.py
git diff --check
```

O coletor oficial `scripts/piloto_fontes_reais.py` foi executado no modo operacional, sem transporte mock. As consultas adicionais limitadas estão registradas em consultas-oficiais.json. O Chrome visível foi aberto pelo script Playwright local em .runtime/piloto-real-login-unico/abrir-chrome-municipal.mjs. As falhas intermediárias estão descritas no relatório; não houve enfraquecimento de asserções.
