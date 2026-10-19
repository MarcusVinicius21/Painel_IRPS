> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Próximas implementações e decisões reais

As pendências abaixo não impediram a aplicação local. Não há solicitação de autorização pendente nesta entrega.

## Decisões humanas, quando chegar a etapa correspondente

1. **Identidade produtiva e organizações:** definir o provedor de acesso, responsáveis pelo provisionamento e papéis administrativos. As contas atuais são fictícias.
2. **Competência administrativa:** definir responsáveis, anuência municipal, comprovação de recursos e atos oficiais. A revisão atual é interna e não autoriza despesa.
3. **IA externa, somente se aprovada:** escolher serviços, projeto/conta, teto e classes de dados permitidas. As credenciais deverão ser provisionadas fora do código. OpenAI/Google seguem desligados para o IRPS.
4. **Cobertura e curadoria:** priorizar períodos/órgãos e responsáveis por equivalências de descrição, embalagem, unidade e versão. A amostra atual não sustenta cobertura nem previsão comercial dos 118 municípios.
5. **Infraestrutura produtiva:** escolher ambiente e política de dados/retencão. Implantação, serviços globais e faturamento continuam fora da autorização desta rodada.

## Implementação técnica priorizada

| Prioridade | Próximo trabalho | Resultado necessário |
|---|---|---|
| 1 | IdP real e provisionamento, HTTPS e gestão de segredos | Entrada de pessoas reais com organizações verificadas |
| 1 | Coletor público centralizado, resultados/contratos PNCP e conciliação de itens | Histórico reproduzível por fase e unidade, sem duplicação |
| 1 | Fontes de execução financeira e evidência física | Distinguir empenho/liquidação/pagamento/entrega/consumo com documentos |
| 1 | Processo de revisão, anuência e recursos | Responsáveis e trilha administrativa suficientes para atos oficiais |
| 2 | Workers, retomada agendada, limites distribuídos e testes de carga | Operação confiável fora de um único computador |
| 2 | Isolamento de leitores, antivírus, OCR autorizado e grandes arquivos | Documentos reais processados com segurança e revisão |
| 2 | Backups/restauração, retenção, monitoramento e revisão de segurança | Evidência operacional e plano de recuperação |
| 2 | Respostas API mais tipadas e contrato cliente gerado | Reduzir tipos dinâmicos na camada de apresentação |
| 3 | Responses/Google, se aprovados | Expansão de linguagem/extração com orçamento, privacidade e avaliações |
| 3 | Avaliação preditiva e usabilidade em campo | Acurácia e esforço medidos em situações reais |

Não é preciso redesenhar o Observatório ou reescrever o V4 para executar essa sequência. Não reutilizar credenciais nem prompts de notícias do Radar. Reaproveitar padrões de tratamento de erro, reserva e medição estudados anteriormente, respeitando o domínio do IRPS.
