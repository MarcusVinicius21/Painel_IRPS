# Cobertura CATMAT e CATSER

Conferência local em 20/10/2026. Universo: códigos distintos dos arquivos `catmat.csv` e `catser.csv` fornecidos pelo usuário, conciliados com os snapshots de mesmo SHA-256 no banco local de validação. Não certifica a atualidade nem a totalidade do catálogo nacional corrente.

| Catálogo | Códigos no arquivo | Códigos disponíveis para consulta | Cobertura de consulta | Códigos com histórico oficial vinculado e revisado | Cobertura para análise de compras por código |
|---|---:|---:|---:|---:|---:|
| CATMAT | 345.575 | 345.575 | 100% | 0 | 0% |
| CATSER | 3.104 | 3.104 | 100% | 0 | 0% |
| Total | 348.679 | 348.679 | 100% | 0 | 0% |

**Resultado:** todos os códigos dos arquivos estão no banco para pesquisa. Ainda não há cobertura comprovada de análise histórica de compras associada a esses códigos na organização local avaliada. Os fatos oficiais já armazenados não foram descartados; falta estabelecer seus vínculos técnicos revisados com o catálogo. Isso não significa ausência de compras desses produtos pelos municípios.

## Método e limites

- Consulta: interseção dos códigos do CSV com os códigos do snapshot correspondente, dividida pelos códigos distintos do CSV. Comparação por conjunto encontrou zero códigos faltantes e zero extras em ambos os catálogos.
- Análise: códigos com vínculo revisado para produto canônico oficial vigente e pelo menos um fato oficial atual correspondente ao par exato de item e versão, com referência de fonte, divididos pelo mesmo universo. Nenhum vínculo oficial revisado foi encontrado na organização avaliada (`compras-a`).
- Materiais e serviços são universos separados: códigos numéricos iguais entre CATMAT e CATSER não são deduplicados entre si.
- Inclui ativos e inativos. Ativos: 250.034 materiais e 3.022 serviços; inativos: 95.541 materiais e 82 serviços. Esses estados não indicam existência de compras.
- O indicador de análise mede disponibilidade mínima de histórico vinculado; não comprova cobertura temporal completa, preços comparáveis, recorrência, consumo nem necessidade futura V4.
- Dados sintéticos, estudos de demonstração e vínculos em bancos de testes não entram no numerador de análise oficial.

Evidência com contagens, hashes dos CSVs e instante da medição: [cobertura-catalogos.json](evidencias/cobertura-catalogos.json).

Esta atualização acrescenta somente documentação e evidência local. Não altera o aplicativo, o núcleo V4, fontes ou credenciais. Não houve commit, push ou deploy.
