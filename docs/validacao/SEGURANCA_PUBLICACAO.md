# Auditoria do envio inicial ao GitHub

Data: 19/10/2026. Destino autorizado: `MarcusVinicius21/Painel_IRPS`, branch `main`.

## Escopo e seleção

A publicação utiliza uma cópia independente da implementação local. O repositório remoto foi conferido pelo conector GitHub: privado, tamanho zero, branch principal `main` e permissão de escrita disponível. O SSH confirmou a identidade `MarcusVinicius21` sem criar token ou expor uma chave.

Incluídos: código executável, locks, migrações, testes, scripts portáveis, catálogo fictício, cadastro municipal público, documentação técnica textual, fluxogramas Mermaid/SVG, evidências de testes revisadas e dez capturas sobre dados sintéticos.

Excluídos: `.runtime`, `.venv`, `node_modules`, binários PostgreSQL/Gitleaks, bancos/dumps, `.env` reais, uploads, exports CSV volumosos, arquivos ZIP, traces/HAR, cookies, sessões, chaves, credenciais, PDFs privados, histórico de outros projetos e arquivos das skills privadas. O Radar não integra esta cópia.

## Verificações antes de enviar

- **Gitleaks 8.30.1**, regras padrão, ocultação integral de valores, sem comentários de exclusão: varredura dos fontes/documentos selecionados e do índice Git. Resultado sem achados.
- Binário Gitleaks obtido da [release oficial](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1), SHA-256 comparado ao manifesto dessa release: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`. A comparação com o manifesto da mesma origem não é uma validação independente de assinatura.
- Scanner complementar em `scripts/auditar_publicacao.py`: caminhos proibidos, chaves privadas, tokens usuais, JWT literal, URI com senha e integridade V4. A análise não imprime o valor suspeito.
- `.gitignore` conferido com `git check-ignore` para configurações reais, runtime, ambientes, caches, bancos, backups e estado de autenticação. `.env.example` contém somente placeholders explícitos.
- JSONs, XML, TXT, documentação e logs escolhidos foram inspecionados. Caminhos pessoais e hostname foram removidos das cópias publicáveis; não foram alterados resultados, falhas ou mensagens dos testes.
- Dez PNGs foram abertos e revisados: somente contas/cenários fictícios e municípios públicos. Não contêm comentários textuais ocultos nem EXIF, conforme [manifesto de capturas](capturas-metadados.json).
- As três amostras oficiais históricas contêm somente campos públicos e URLs de origem. IDs internos de recursos, atores e jobs foram omitidos. CNPJ do órgão é identificação pública; não é credencial.
- Oito módulos V4 preservados byte a byte. Os originais e as skills não receberam alterações. O índice inclui a proteção de bytes em `.gitattributes`.
- Auditorias de dependências Python e npm: zero vulnerabilidades conhecidas nos snapshots desta execução. Não equivale a ausência absoluta de vulnerabilidades.

## Histórico Git e conclusão do gate

Este repositório foi inicializado do zero na cópia limpa; nenhum diretório `.git` foi importado do workspace ou de outro projeto. O commit inicial deverá ser verificado antes do push com Gitleaks no histórico completo e com `python scripts/auditar_publicacao.py --history`.

Os resultados dessas últimas verificações e o SHA efetivamente publicado são registrados no recibo local da publicação, fora do repositório. Isso evita alterar o próprio commit após sua auditoria. Somente o commit conferido será enviado, sem force push.

O envio foi autorizado pelo usuário; não configura implantação nem torna o aplicativo público. A visibilidade privada será conferida novamente após o push. Não houve leitura de credenciais do Radar, uso de chave de IA, ativação de serviço pago ou alteração de configuração Git global. A identidade de autoria usa o endereço GitHub `noreply` correspondente ao proprietário verificado.

Limitação: varreduras automatizadas e revisão manual reduzem o risco, sem prometer detecção de todos os segredos ou falhas possíveis. Avisos e limitações estão descritos em [RESULTADOS](RESULTADOS.md) e na [política de segurança](../../SECURITY.md).
