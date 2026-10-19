# Resultados — Inteligência de Oportunidades

## Testes executados

| Verificação | Resultado | Evidência |
|---|---|---|
| API de oportunidades | 21 aprovados | `backend/tests/test_opportunities.py` |
| Regressão Python completa, incluindo V4 e segurança | 136 casos coletados, 336 entradas JUnit com 200 subverificações, zero falhas; 35,727 s | `.runtime/evidencias/pytest-oportunidades-final.xml` |
| Jornada Playwright | 2 aprovados | [metadados](oportunidades/jornada-playwright.json) |
| Playwright completo | 13 aprovados; sem falha, salto ou instabilidade | `.runtime/evidencias/playwright-oportunidades-final.json` |
| Acessibilidade | Zero violações axe WCAG A/AA nas duas jornadas | Registro Playwright |
| Responsividade | 1440×1050 e 390×844 sem rolagem horizontal indevida | [galeria](#capturas-reais) |
| Build React/TypeScript | Aprovado | `npm.cmd run build` |
| Migrações PostgreSQL | 38 tabelas → zero → 38; 34 com RLS forçada | `scripts/validar_migracoes.py` |
| Segredos no índice e histórico | Zero achados em 444 entradas; oito módulos V4 íntegros | `scripts/auditar_publicacao.py --history` |
| Gitleaks no índice | Zero vazamentos encontrados | `gitleaks git --staged` |
| Auditoria de dependências | npm produção e pip: zero vulnerabilidades conhecidas nos pacotes instalados | `.runtime/evidencias/` |

A jornada usou um exemplo fictício controlado, marcado pela interface. Ela
selecionou o conjunto, abriu Papel A4, salvou revisão com evidências fictícias
de teste e criou um rascunho. O arquivo de métricas registra sete cliques,
onze controles alterados (um filtro e dez da revisão humana), quatro telas
percorridas e 10,1 segundos no navegador automatizado. Os controles da
revisão pedem oito textos de evidência e duas decisões de viabilidade;
não foram automatizados porque representam responsabilidade humana.

O primeiro comando Playwright desta retomada usou a porta padrão 5210, que
estava sem serviço, e falhou por conexão recusada. A execução válida informou
`IRPS_BASE_URL=http://127.0.0.1:5220` e aprovou os 13 testes. O build emitiu
dois avisos da dependência `lucide-react` sobre `use client`, sem falha de
compilação. O teste Python manteve aviso de depreciação da integração de teste
HTTP; não houve falha funcional final.

## Capturas reais

### Desktop — lista

![Lista de oportunidades em 1440 px](oportunidades/telas/1440-oportunidades.png)

### Desktop — análise detalhada

![Detalhe da oportunidade em 1440 px](oportunidades/telas/1440-oportunidade-detalhe.png)

### Mobile — lista

![Lista de oportunidades em 390 px](oportunidades/telas/390-oportunidades.png)

## Fonte pública limitada

Em 19/10/2026, uma coleta local consultou o PNCP para o período 13–19/10/2026,
IBGE 3131307 e modalidade 6. Duas páginas retornaram três registros e o limite
configurado encerrou em `limited`; não há alegação de cobertura do município.
Uma coleta separada de contratos, com CNPJ obtido da própria resposta anterior,
retornou um contrato em uma página. O corpo de respostas públicas não foi
incluído no Git; URL, consulta, digest e momento permanecem no banco local.

Detalhes, limites e rotas estão em [OPORTUNIDADES_CONSORMULTI](../implementacao/OPORTUNIDADES_CONSORMULTI.md).
