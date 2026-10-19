> Registro da rodada local original. O envio inicial ao GitHub foi autorizado posteriormente. Consulte README.md para os caminhos atuais.

# Continuidade da implementação

Este código é uma nova implementação local autorizada, sobre o design Observatório existente. Não modificar o V4, Radar, skills ou versões anteriores. Não ativar cobrança, OAuth ou implantação nesta entrega.

1. Começar pelos testes e `docs/INDEX.md`.
2. A API é a autoridade: nenhuma permissão, quantidade ou total nasce do seletor do navegador.
3. Valores da API usam representações decimais textuais. `Intl` apenas apresenta números na UI.
4. Nenhum estágio de compra equivale a outro. Cabeçalhos e itens PNCP não podem ser somados juntos.
5. Não reutilizar as credenciais locais de teste para produção. O proprietário do schema não é o usuário da API.
6. Alterações de cenário exigem `If-Match`; versões são inseridas, nunca sobrescritas.
7. Novas cidades/itens não recebem parâmetros fictícios. Somente a rota `scenarios/synthetic`, restrita ao emissor de teste, preenche exemplos explícitos.
8. Alterar versão do item requer novos parâmetros/preços. Relatórios antigos usam a versão preservada.
9. A IA organiza consultas; o V4 calcula. Acrescentar ferramenta exige schema fechado, autorização e testes negativos.
10. Antes de produção: identidade externa, política de aprovação/anuência, cobertura/conciliação de dados, limites distribuídos, workers, backups/restauração, análise de arquivos isolada, gestão de segredos e revisão independente de segurança.

Manus governa composição e fluxo; Humanização governa os textos; Frontend Design preserva a direção Observatório; Web Design Guidelines orienta teclado, contraste e estados. Nenhuma dessas skills foi alterada.
