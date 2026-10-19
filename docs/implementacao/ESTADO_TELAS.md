> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Observatório conectado

Todas as telas abaixo usam o serviço local ou a identidade autenticada. Não há troca de papel por seletor no navegador, cálculo financeiro local ou armazenamento de cenário em `localStorage` no frontend ativo. Os componentes e o visual Observatório foram reaproveitados.

| Tela/rota | O que funciona com API/banco | Limitação visível |
|---|---|---|
| Entrada | Contas fictícias, sessão assinada e membership | Conta real depende de IdP |
| `inicio` | Planejamento salvo, publicações oficiais gravadas e atalhos | Cobertura parcial e exemplos identificados |
| `pesquisa` | CATMAT/CATSER preservados, itens e versões | Catálogo não comprova compra/unidade pronta |
| `resultados` | Texto, cidade, fase, origem e paginação | Sem inferir “não comprou” |
| `produto` | Registros da mesma identidade/versão e unidade | Equivalência entre descrições não é automática |
| `municipio` | Registros ligados ao código IBGE | Nem todos os órgãos/períodos foram coletados |
| `processo` | Registro exato por ID, fonte/data e consulta de itens PNCP | Publicação não comprova execução |
| `pagamentos` | Conciliação por cidade, item, versão e obrigação | Pagamentos oficiais ainda não coletados; exemplos explícitos |
| `comparar` | Consultas em paralelo, mesma descrição/unidade/fase | Cidades sem dados permanecem sem informação |
| `necessidades` | Mediana histórica V4 quando existem três anos compatíveis | Demonstração histórica; previsão real não validada |
| `licitacao` | Cenários salvos, criação interna sem valores ou exemplo explícito, cálculo persistido | Não é licitação oficialmente aprovada |
| `participantes` | Seleção/pesquisa, 3/10/20/118 e salvamento | Novas cidades não ganham parâmetros inventados |
| `itens` | Seleção de itens/versões e unidades | Troca de versão invalida parâmetros/preços |
| `quantidades` | Linhas do banco, paginação e revisão de parâmetros | Faltas mantêm quantidade/total pendentes |
| `distribuicao` | Meta justificada, pesos/fontes/pisos/tetos, confirmação e V4 | Não há peso automático por população |
| `precos` | Referência com unidade, versão, endereço e data | Completude não equivale a pesquisa aprovada |
| `revisao` | Pendências e registro de revisão interna | Não autoriza despesa ou ato oficial |
| `relatorios` | Cálculo/versão escolhidos, PDF/CSV/XLSX e recuperação de rascunho | Custos privados ficam fora do documento de planejamento |
| `memoria` | Fórmula, parâmetros, avisos e preço do cálculo preservado | Conferência administrativa continua necessária |
| `negocio` | Custo, venda, despesas, tributos, lucro/margem e versões privadas | Hipóteses preenchidas pelo usuário; sem conclusão tributária |
| `documentos` | Vários arquivos, leitura local, original, localização e conferência | Não aplica extração automaticamente; sem OCR/antivírus |
| `fontes` | Consultas reais, jobs, origem/data e cobertura | Recortes pequenos e fontes adicionais pendentes |
| `alertas` | Consulta guardada por ator; remoção confirmada | Não envia notificações automáticas |
| `administracao` | Meu acesso e minhas atividades | Não é administração completa de usuários |
| Assistente contextual | Perguntas e fontes por ferramentas offline | Sem modelo pago ou interpretação universal de linguagem |

## Desktop e mobile

Navegação lateral desktop e navegação inferior mobile existentes foram preservadas. Tabelas viram registros verticais no mobile. Rodaram fluxos reais em 320/390/768/1024/1440 e inspeção das 23 rotas autenticadas em 390/1440. Login e assistente também foram testados. As imagens da galeria são capturas do navegador, não composições inventadas.

## Estados e linguagem

Carregamento: “Consultando os registros salvos…”. Ausência: “Não encontramos registros neste recorte. Isso não comprova ausência de compras.”. Conflito: “Outra pessoa alterou este cenário. Abra a versão atual.”. Falta de estoque/recebimento impede cálculo. Falha de fonte conserva o histórico. Perfil sem custo privado recebe uma explicação de acesso, sem buscar as cotações.

Manus manteve contexto → decisão → evidência → ação → feedback. Humanização foi aplicada aos rótulos, avisos e respostas. Web Design Guidelines orientou labels explícitos, teclado, contraste e a correção de sobreposição. Frontend Design preservou tipografia, teal, composição e hierarquia Observatório.

## Não confundir com frontend definitivo de produção

O código da UI é funcional e conectado, mas ainda precisa de validação em campo, autenticação produtiva e dados oficiais suficientes. Não há simulação silenciosa quando a API falha: o erro fica visível. O banco local contém apenas exemplos explicitamente criados e a pequena coleta pública documentada.
