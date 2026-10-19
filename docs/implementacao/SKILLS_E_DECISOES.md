> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Skills aplicadas nesta execução

As skills foram carregadas pela leitura dos arquivos e referências locais disponíveis na sessão. Não foram reinstaladas nem editadas. “Aplicada” aqui descreve o uso das regras no trabalho; não é alegação de chamada automática a um plugin ou servidor MCP.

| Skill | Aplicação observável |
|---|---|
| Manus / `governed-frontend-ui` | React/TypeScript/Vite e CSS existentes; shell, contexto, seleção, evidência e feedback; `plan.md`, TODO verificável, handoff, build e fluxos reais |
| `config-humanization-irps` | Textos de acesso, pendência, preço, consumo, documentos e assistente; dados ausentes não viram zero; revisão de títulos/ações e estados |
| `frontend-design` | Preservação da direção Observatório, Manrope, cores e composição; nenhuma nova proposta visual |
| `web-design-guidelines` | Labels explícitos, navegação semântica, foco, teclado, contraste, tamanhos e correção de mensagem sobrepondo o assistente |
| React best practices | Pedidos independentes em paralelo, limpeza de efeitos, identidade no servidor, paginação e separação de componentes por domínio |
| Playwright | Browser Chrome real, cinco larguras, onze roteiros e capturas; axe e arquivos baixados |

A versão consultada das [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) foi obtida nesta sessão. A preferência de título em inglês dessas guidelines não substitui o português brasileiro humano exigido pela skill IRPS.

## Decisões de implementação

- O backend e a persistência foram explicitamente autorizados pelo usuário nesta rodada. A governança da Manus foi aplicada sem transformar uma skill de frontend em fonte de autorização de dados.
- O núcleo V4 foi copiado por arquivo e comparado por digest; as regras matemáticas não foram redesenhadas.
- A matriz de permissões matemática anterior não substitui autenticação. A aplicação usa vínculo real no banco, sessão verificada e RLS.
- O usuário proibiu commit/push/deploy. Nenhum checkpoint Git foi criado; o workspace também não era repositório Git.
- O frontend herdado com papel fictício e cálculos locais foi retirado da fonte ativa da nova aplicação. Os originais permanecem nas entregas anteriores.
- Foram geradas somente credenciais sintéticas de teste, fora do código. Plugins e skills privados não são redistribuídos no ZIP.
- A rede foi usada apenas para documentação/registros de pacotes e consultas públicas oficiais. Serviços pagos, Google OAuth, Radar e dados privados reais não foram conectados.

`evidencias/preservacao-final.json` registra os hashes dos quatro SKILL.md principais e o resultado de preservação. Nenhuma regra privada foi sobrescrita para facilitar a implementação.
