# Validação do incremento de cobertura e catálogo

Execução local em 20/10/2026. Banco PostgreSQL de testes isolado do banco do piloto. Não houve deploy, merge ou chamada paga de IA.

| Verificação | Resultado | Evidência/limite |
| --- | --- | --- |
| Migrações Alembic | 40 tabelas no upgrade; 0 no downgrade; 40 no novo upgrade; 36 tabelas com RLS forçado | `scripts/validar_migracoes.py`, banco descartável `irps_migration_test` |
| Python completo, incluindo núcleo V4, autenticação, isolamento, fontes, catálogo e oportunidades | 149 testes e 200 subtestes aprovados | `pytest -q`; dois avisos de dependências/teste, sem falha |
| Regressões novas | 9 testes aprovados | Variação de nome, embalagem, unidade, reprocessamento idempotente, sobreposição, versionamento, fases, contagem por página, 404 ambíguo, HTTP 204 vazio, preço sem dados pessoais |
| Frontend | Build TypeScript/Vite aprovado | Avisos não bloqueantes de diretivas da dependência `lucide-react` |
| Playwright Chrome | 15 testes aprovados, larguras 320, 390, 768, 1024 e 1440 px | Jornadas, rotas, recuperação, responsividade, teclado e axe sem violações nas páginas verificadas |
| Piloto público PNCP | 100 requisições dentro do orçamento; limite atingido sem erro | [Recorte e URLs](PILOTO_COBERTURA_CATALOGO.md) |
| Catálogo no piloto local | 926 normalizações salvas: 10 incompletas, 916 com descrição/unidade textual; 4 grupos sugeridos, nenhum aprovado automaticamente | Inclui dados fictícios de teste e fatos oficiais. Código oficial de catálogo frequentemente ausente nos itens consultados. |

As capturas abaixo são do aplicativo conectado à API e ao PostgreSQL locais. Dados sintéticos continuam marcados; dados oficiais são identificados por fonte e recorte.

- [Catálogo e cobertura — desktop, primeira dobra](telas/1440-catalogo-primeira-dobra.png)
- [Catálogo e cobertura — desktop, página completa](telas/1440-catalogo-cobertura.png)
- [Catálogo e cobertura — mobile, primeira dobra](telas/390-catalogo-primeira-dobra.png)
- [Catálogo e cobertura — mobile, vista principal](telas/390-catalogo-cobertura.png)
- [Catálogo e cobertura — mobile, painel de fontes](telas/390-catalogo-painel-cobertura.png)

No primeiro Playwright completo, 14/15 passaram e um teste antigo de rotas apresentou navegação concorrente (`Execution context was destroyed`). O teste foi ajustado para navegar por hash dentro do mesmo documento, que é o comportamento real da aplicação; a suíte completa foi repetida e passou. Na primeira execução Python deste incremento, 144 testes passaram e um teste legado exigia exatamente 100 itens sintéticos, incompatível com a inclusão controlada de novos itens no teste de catálogo. A expectativa foi corrigida para preservar os 100 itens sem impedir extensões, e a suíte completa passou.

Não foi comprovada cobertura completa de publicações de todas as modalidades, resultados homologados, atas, contratos, entregas, liquidações, pagamentos ou consumo. A identidade jurídica de consórcio/órgão frente ao município localizado pelo código IBGE exige conferência. Os testes de browser e dados oficiais são locais; autenticação produtiva, retenção, observabilidade e conectores municipais seguem pendentes.
