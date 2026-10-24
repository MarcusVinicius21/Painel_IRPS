# FCP07 — Comparação por identidade e fornecedores documentados
Status: PARTIAL

GET /portfolio/comparison reutiliza o serviço de histórico local e oferece paginação de grupos técnicos e evidências de fornecedor. Agrupa somente município, comprador, item, versão, descrição, unidade, moeda, fonte e fase idênticos. Não soma códigos do grupo comercial, órgãos, versões ou fases. Totais gerais de quantidade/valor permanecem null. Cada linha informa quantidade observada quando comparável, valor documentado conhecido, parcialidade, mediana dos preços unitários documentados comparáveis, IDs de fatos/fontes e meses observados.

Recorrência percentual, consumo mensal e previsão permanecem null, pois não há cobertura apropriada. Unidade ausente, conflito de embalagem e embalagem não expressa na unidade impedem soma de quantidades. O teste inicial identificou que o normalizador anterior não rejeitava kg versus descrição de caixa com resmas; foi acrescentada a restrição conservadora no agregado, mantendo a asserção de exclusão. Não se converte peso em embalagens sem regra aprovada.

Fornecedor PJ somente do resultado/contrato documentado, com papel, CNPJ, processo, comprador, URL, fonte e consulta. Não deduz vínculo por CNAE ou similaridade nem afirma relação comercial com CONSORMULTI. Candidatos de grupo continuam marcados para revisão; a comparação de identidade municipal não aprova vínculo CATMAT ou proposta de licitação.

Prova READ ONLY no operacional: grupo veículos/Ipatinga/homologado retorna um agregado da identidade do item e uma evidência de adjudicatário; grupo informática/Timóteo/publicado retorna dois agregados da Câmara e zero fornecedores (publicação não comprova adjudicatário). Evidência privada comparison-proof.json. Quantidade/valor observados permanecem separados de preços nacionais. Os exemplos PNCP não são previsões ou necessidade V4.

Testes: pytest test_portfolio_insights.py test_portfolio_history.py test_municipal_indicators.py: **7 aprovados**, 1,72 s, após correção da incompatibilidade embalagem/unidade; sem enfraquecer asserções. Cobrem versões/fases/moedas/cidades distintas, dados ausentes e fornecedor com evidência. Diff e hashes V4 preservados. Sem migração, alteração de cálculos, screenshots ou publicação remota.

Pendentes: navegação visual em FCP08; revisão técnica/comercial, cobertura temporal insuficiente para recorrência comprovada, fontes financeiras e associações de código não documentadas. Próxima FCP08.
