# T17 - Relatórios e versões

## Contexto e decisão

**Rota:** `/#/relatorios`. **Funções:** F20. **Público alvo:** Consulta conforme origem; planejamento com preparador/revisor competente.

Obter arquivo da mesma seleção e versão. A faixa de demonstração permanece visível. Identidades municipais vêm do C5; todo valor operacional é sintético.

## Dados e componentes

Versão atual/salva, recorte completo/item, IDs, linhas, Q, preços, totais e faltas. Campos comuns: identificador estável, organização/classe quando restrito, origem, data do evento/consulta, período e estado. Componentes reais: Page, Panel, Field, Notice, Badge, DataTable, Dialog e Stats, conforme a superfície. Números usam pt-BR e unidades explícitas.

**Fonte na demonstração:** `prototipo/src/data/demo.ts`, `cities.json`, estado do cenário e funções tipadas `domain/math.ts`. Custos comerciais ficam fora do estado público do cenário. **Fonte em produção:** contratos F e inventário de integrações; resposta de documentação HTTP não preenche valores da tela.

## Ações e retorno

Salvar; comparar duas versões; baixar PDF/CSV/XLSX dinâmicos. Links navegam; botões alteram estado. A seleção permanece por ID, não pelo índice da linha. Paginação não muda agregados. A alteração de parâmetro/seleção/preço invalida revisão; desfazer restaura o estado anterior. No protótipo, salvamento local não é snapshot transacional de produção.

## Composição desktop

Prévia paginada com resumo reconciliado do arquivo. Trilho lateral e busca/contexto persistentes. Uma ação primária, evidência perto do valor e secundárias sem competir com pendências. Tabelas ordenáveis quando há atributo apropriado; máximo de oito registros por página. Detalhe e origem mantêm a entidade de retorno.

## Composição mobile

Escopo e subtotal antes da prévia; downloads com nome/versão. Navegação inferior com cinco destinos e menu completo. Texto não é reduzido para encaixar cem colunas. Registros em `dl` preservam nome, valor e unidade. Busca, seleção em lote e paginação substituem arraste obrigatório. Em 320 px os formulários usam uma coluna. Ações não dependem de hover.

## Estados e exceções

- Normal: exemplo com recorte, origem e fase.
- Carregando: anúncio e saída para o exemplo, sem número novo inventado.
- Vazio: explica o recorte e oferece retorno; não é ausência nacional de compras.
- Erro: mantém rascunho/último dado e permite tentar novamente.
- Parcial: mantém valores elegíveis e faltas, com subtotal rotulado.
- Sem acesso: omite conteúdo da superfície e orienta o perfil; bloqueio visual não é proteção de servidor.
- Sigilo, retificação, desatualização, conflito e salvo: semântica e estados no documento 07; origem/versão conservadas.

**Exceção específica:** Arquivo inclui selecionados fora da página e linhas pendentes; não contém custo privado.

## Teclado, foco e mensagens

Labels associados; Tab alcança ações; foco de 3 px com afastamento. Diálogo nativo contém foco, Escape cancela e devolve foco ao disparador. Status não depende de cor. O cliente recebe texto humano; diagnóstico fica restrito à documentação técnica. Resultado calculado, proposta e aprovação oficial não recebem o mesmo rótulo.

## Aceite e evidência

Executar ações descritas em 1440 e 390; reflow em 320/768/1024. Conferir um h1, nenhum campo cortado, teclado e mensagens sem jargão. As capturas anteriores não acompanham esta especificação. O plano de QA e o resultado final informam o que foi efetivamente testado; estes critérios não são certificados por aparecerem na especificação.


Capturas selecionadas da implementação atual: [galeria de validação](../../validacao/GALERIA.md). A galeria não cobre todas as telas desta especificação.
