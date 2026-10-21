# Evidências de validação

## Resultados executados

| Verificação | Resultado atual | Evidência |
|---|---|---|
| Python completo, PostgreSQL isolado | 185 testes e 200 subtestes aprovados; 2 avisos | `evidencias/python-entrega.xml`, `.txt` |
| Documentos/progresso/manifestações após revisão de linguagem | 31 testes aprovados; 1 aviso | `evidencias/python-documentos-humanizacao.xml`, `.txt` |
| Playwright completo | 25 aprovados, 0 falhos, 0 ignorados, 0 flaky | `evidencias/playwright-fechamento.json`, `.txt` |
| Build React/TypeScript/Vite | Aprovado | `evidencias/build-entrega.txt` |
| Migrações 0001–0012 | Banco novo descartável; segunda aplicação idempotente; 6 tabelas com RLS forçada verificadas | `evidencias/migracoes.json` |
| Integridade do núcleo V4 | Oito hashes iguais aos iniciais | `evidencias/preservacao.json` |
| Dados nacionais atuais | Contagens/indexação e hashes dos arquivos conciliados | `evidencias/dados-verificados.json` |
| Dependências Python fixadas | Nenhuma vulnerabilidade conhecida apontada | `evidencias/dependencias-python.json` |
| Dependências frontend de produção | Nenhuma vulnerabilidade conhecida apontada; não inclui auditoria de devDependencies | `evidencias/dependencias-frontend.json` |
| DOCX demonstrativo | Renderizado pelo LibreOffice; 2 páginas inspecionadas visualmente | `documentos-renderizados/docx/` |
| PDF demonstrativo da minuta | 2 páginas inspecionadas visualmente | `documentos-renderizados/minuta-pdf-*.png` |
| PDF de consolidação | 1 página inspecionada visualmente | `documentos-renderizados/consolidacao-pdf-1.png` |

## O que o navegador comprovou

O teste da jornada em 1440 e 390 px pesquisa automóvel no catálogo, seleciona o código, salva progresso incompleto, recarrega, troca período e municípios, identifica ausência de vínculo, informa meta fictícia de 200 unidades, salva estudo sem entradas V4 inferidas, abre o cenário V4 vinculado, recarrega e retorna, prepara/baixa DOCX/PDF, anexa e confere prova fictícia, registra 30 unidades em Ipatinga, exige nova conferência da minuta, exporta os quadros e prepara o dossiê atual. Alfenas continua pendente; o total consolidado completo permanece indisponível.

Cada uma das sete capturas por resolução foi acompanhada de verificação de overflow e análise Axe WCAG 2 A/AA e 2.1 AA. A galeria contém capturas de viewport e versões completas separadas. As regressões também exercitam 320, 768 e 1024 px, 118 participantes/100 itens no V4, diferenças de organização, leitura e escrita por permissão, exportações, comparação, oportunidades, recuperação após erro documental e navegação por teclado.

Isso não substitui avaliação humana com tecnologias assistivas. Não foi medido um percentual de identidade de pixels com artes conceituais nem executado teste de penetração externo.

## Avisos e tentativas anteriores

O Python registra depreciação Starlette/httpx e aviso de chave HMAC curta em um teste negativo deliberado de JWT. O build registra avisos do bundler sobre `use client` na biblioteca de ícones. O renderizador PDF pode registrar fallback de fontes Symbol/ArialUnicode; as imagens finais foram examinadas, sem perda de texto observada nas páginas entregues.

As primeiras tentativas falharam por ambiente inicialmente parado, fixture de teste ausente, expectativa errada sobre permissão de exportação do leitor, CSS ainda não criado, estreitamento TypeScript, datas UTC, semântica/contraste dos indicadores, seletores da Home antiga e mensagem sobreposta em mobile. Esses resultados não foram declarados aprovados. Os resultados finais acima são de novas execuções após correção. Relatórios antigos em `docs/DIRETRIZ_MESTRA_V2` não foram substituídos.

## Segurança do pacote

Confira `evidencias/auditoria-seguranca.json`, o inventário de arquivos e o manifesto SHA-256 do ZIP. A checagem por padrões é complementar aos testes de autorização/RLS e à seleção explícita dos arquivos. Não representa certificação absoluta de ausência de segredos.

O pacote inclui demonstrações identificadas e fatos públicos agregados. Não contém CSVs nacionais integrais, bancos, configurações reais, cookies, tokens, chaves, `.env`, originais recebidos, dependências instaladas ou custos comerciais privados. Nenhum serviço pago ou deploy foi utilizado.
