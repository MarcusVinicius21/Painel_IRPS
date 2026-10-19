> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Dependências da entrega

Python 3.12 em `.venv`; Node 24; PostgreSQL 18.6 portátil. Versões Python em `requirements.lock`, JavaScript em `package-lock.json`. Os inventários de licenças estão em `evidencias/licencas-python-instaladas.json` e `licencas-node-lock.json`. O lock novo não contém links para dependências do laboratório anterior.

O projeto usa FastAPI, SQLAlchemy/Alembic/psycopg, PyJWT/cryptography, Pydantic, httpx, leitores PDF/XML/XLSX e ReportLab. A interface usa React, Vite, TypeScript e Lucide. Playwright/axe e pip-audit são ferramentas locais. Não há SDK de IA chamando serviços pagos.

Manrope acompanha licença OFL em `frontend/public/fontes/manrope-OFL.txt`. PostgreSQL é obtido de distribuição indicada pelo site oficial, sem instalar serviço. Os binários e as dependências instaladas não são redistribuídos no ZIP. As condições de redistribuição dos componentes devem ser revisadas antes da distribuição comercial.

Os snapshots finais pip/npm não apontaram vulnerabilidades conhecidas; isso não cobre toda a segurança do aplicativo, do sistema operacional ou dos binários PostgreSQL. A auditoria inicial do pip foi preservada e sua atualização local está fixada no instalador.
