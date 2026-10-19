# Estados, acessibilidade e esforço

## Modelo de estados do produto

| Estado | Texto proposto / significado | Recuperação e preservação |
|---|---|---|
| Carregando | “Preparando o exemplo…” / execução em curso | Manter termo/contexto; cancelar tarefa não apaga documento |
| Vazio do recorte | “Nenhum registro neste recorte” | Ajustar filtro; não dizer que o município não comprou |
| Não consultado | “Este período ainda não foi consultado” | Exibir cobertura e permitir novo recorte |
| Falha | “Não foi possível consultar esta fonte agora” | Último dado datado; tentar novamente; não converter em zero |
| Parcial | “Há linhas que precisam de confirmação” | Subtotal e faltas; relatório parcial explícito |
| Sem permissão | “Este perfil não pode abrir estes dados” | Não retornar payload em produção; validar acesso/organização |
| Sigiloso | “Preço não divulgado” | Não estimar como gratuito; separar quantidade e valor |
| Retificado | “Esta versão substitui a anterior” | História preservada; não somar original e substituto |
| Desatualizado | “Confira a data antes de usar” | Oferecer atualização como nova observação, sem alterar aprovação |
| Conflito | “Outra versão foi salva. Compare antes de continuar” | Manter edição local; comparar/reaplicar com versão esperada |
| Salvo | “Rascunho salvo neste navegador” | Em demo, storage local; produção exige confirmação do serviço |
| Sem estoque | “Falta confirmar o estoque disponível” | Quantidade permanece ausente; zero exige informação explícita |
| Meta inviável | “A meta não cabe na soma dos pisos e tetos” | Revisar meta/limites; nenhuma distribuição silenciosa |

O protótipo oferece estados normais, parciais, carregando, vazio, falha e sem acesso em todas as rotas pelo seletor de estados. Sigilo/ausência, retificação e salvo aparecem também nas tarefas. Conflito concorrente, sessão expirada e revogação produtiva estão especificados; sem servidor, não há alegação de ensaio real dessas funções. Revisão demonstrativa não emite ato administrativo.

## Acessibilidade funcional

HTML semântico, um h1, títulos em ordem, links para navegação e botões para ação. Labels associados, names compreensíveis, unidades no contexto. Teclado: Tab/Shift+Tab, Enter quando pertinente, Escape cancela diálogo, foco retorna ao disparador. Campo de arquivo nativo é alternativa ao arrastar. Contornos funcionais e foco têm contraste próprio; cor nunca é único indício.

Proibir bloqueio de zoom. Reflow em 320 é verificação geométrica, não ensaio humano de zoom 400%. Mobile usa registro com rótulo/valor; tabela desktop tem cabeçalhos, legenda, região rolável focalizável e paginação. Cada região recebe nome distinguível. Ações fixas não podem encobrir o foco; conferir teclado virtual e aparelho físico antes de produção.

Objetivo de produção: WCAG2.2AA, sujeito a auditoria completa. Axe sem violações cobre somente regras automatizáveis. Leitor de tela humano, dispositivos reais, outros motores, percepção visual e primeira utilização continuam a exigir ensaios próprios; são complementos, não bloqueios à entrega atual do design.

## Zero Friction e automação

Prioridade: encontrar dados, preencher o que estiver comprovado e pedir somente decisões. Importação em lote, grupos municipais, busca por nome/UF/IBGE, catálogo aberto, parâmetros reutilizados e relatório da seleção reduzem repetição. Autoridade revisa quantitativo, contradição, hipótese frágil e emissão oficial.

Metas preferenciais: iniciar busca, abrir município e retomar cenário em 1-2 ativações. Operação complexa pode exigir mais quando preserva clareza e decisão. Aplicar 118 não exige 118 toques. Alterar referência ou venda recalcula no contexto. Filtrar/paginar não altera conjunto. Remover tem desfazer; cancelar não aplica.

O QA mede eventos confiáveis, campos distintos, mudanças de URL e duração automatizada em tarefas curtas. Preparação é excluída e declarada. Não converter duração Playwright em tempo humano; não anunciar taxa geral de automação. IFO-A proposto: cliques + teclas de ação sem duplicidade + seleção nativa + 2×campos + 2×telas + 4×repetições obrigatórias + teto(segundos automáticos/30). Guardar os eventos e o estado inicial. Comparação entre alternativas exige mesma tarefa/dados e ensaio humano complementar.

## Operação assistida futura

Coleta, normalização, extração e preenchimento em segundo plano dependem dos conectores e da autorização. LLM pode sugerir classificação e texto com referência; não inventa Q, preço ou aprovação. Não há assistente externo configurado no protótipo. Cache e fonte indisponível conservam último sucesso; atualização propõe revisão. Nenhuma notificação externa ou envio documental foi feito nesta entrega.
