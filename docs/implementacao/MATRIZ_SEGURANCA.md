> Evidência histórica da rodada 01. Os números abaixo descrevem aquela execução. Para a nova verificação de publicação, consulte [RESULTADOS](../validacao/RESULTADOS.md). Evidências brutas não foram redistribuídas; falhas anteriores permanecem relatadas em LOG_TESTES.md.

# Controles testados e limites

Nenhum teste isolado comprova segurança integral. Esta matriz descreve o que foi implementado e exercitado localmente.

| Área | Implementação e prova | Produção |
|---|---|---|
| Sessão | RS256 e `kid`; JWK pública; issuer/audience/exp/nbf/iat/sub/jti/organização obrigatórios; oito testes de tokens inválidos | Definir IdP HTTPS e validar fluxo real, rotação e provisionamento |
| Papéis | Membership ativo no banco; sessão revogada/expirada é negada; papéis não vêm do navegador | Provisionamento e administração de acesso próprios |
| Organização | Transação define contexto local; recurso e ação conferidos; app sem superusuário/bypass; RLS forçada | Repetir auditoria com infraestrutura produtiva |
| Custos privados | Empresa A/B separadas em listagem, ID, ferramenta, documentos e exportação; suporte técnico sem custo privado | Políticas comerciais e retenção aprovadas |
| Cache | Organização, ator, papel, tipo de organização e revisão de fontes no identificador; acesso revalidado antes da leitura | Quotas/cache distribuídos e política de revogação centralizada |
| Jobs | Organização/ator persistidos; idempotência; revalidação de membership/permissão no worker e na consulta de resultado | Worker distribuído, agendamento e retomada supervisionada |
| Cookies | HttpOnly na sessão; SameSite Strict; CSRF nas mutações com cookie; Secure falso exclusivamente em loopback HTTP | HTTPS, cookie Secure e infraestrutura de identidade |
| CORS/origem | Origem permitida explícita; origem externa negada; headers e métodos restritos | Domínios definitivos autorizados |
| Frequência | Limite por ator/organização/minuto; teste de 429; fontes com pausa persistente | Limite distribuído e ensaio de carga |
| Injeção | SQL parametrizado; schemas fechados; filtros incompatíveis recusados; nenhuma ferramenta livre | Revisão independente e testes ampliados de abuso |
| Documentos | Limites de tamanho/ZIP/XML/células/páginas; macros/externos recusados; instrução embutida não executa; original imutável | Antivírus, isolamento do parser e análise operacional |
| Arquivos exportados | Autorização no download e digest; CSV neutraliza prefixos interpretáveis; XLSX mantém decimal como texto | Armazenamento privado, expiração e política de retenção |
| Auditoria | Metadados mínimos, sem texto integral de perguntas/documentos, tokens ou custos no evento | Retenção, alertas e monitoramento independente |
| Provedores de IA | Chamadas pagas recusadas; nenhuma chave de OpenAI/Google carregada | Consentimento, teto, dados permitidos e reconciliação de custo |

## Evidência de acesso

Os 50 casos da nova suíte incluem oito cenários de token inválido, revogação após cache, RLS sem contexto, contas A/B, custos privados/artefatos, jobs por ator, rate limit/IdP não configurado, leitores de documentos e filtros de ferramentas. Não são 50 testes exclusivos de segurança; a suíte também cobre cálculos, exports e fontes.

PostgreSQL: usuário da API sem `rolsuper` e `rolbypassrls`; conexão sem organização vê zero cenários. `SET LOCAL` termina na transação, impedindo herança de organização pela próxima requisição do pool. Matrículas não podem ser administradas pelo usuário SQL da API.

Fontes e dados oficiais têm leitura pública autenticada entre organizações. Essa exceção é exclusiva da classificação inserida pelo conector do servidor. A API não aceita um pedido do cliente para transformar cotação ou documento privado em fato oficial.

## Segredos e preservação

Não foram lidos `.env`, tokens ou credenciais do Radar/Google/OpenAI. Foram criadas apenas senhas de banco e chave do emissor **fictícias para teste**, dentro de `.runtime`, ignorada e excluída do ZIP. Nenhuma chave foi colocada em código ou arquivo versionável. A configuração exige um caminho explícito, e o modo sem configuração falha fechado.

2.210 arquivos protegidos, oito arquivos V4 e 192 arquivos de código do Radar conferidos sem diferenças. Os arquivos de segredos inventariados anteriormente só são referidos como metadados; não foram relidos.

## Gate de produção

Continua fechado. O modo de teste permite escolher contas fictícias sem senha humana: serve para validar assinatura, acesso e isolamento em loopback. Não é autenticação produtiva. Ausência de dados oficiais e ausência de antivírus/isolamento impedem tratar o ambiente como sistema pronto para receber documentos privados reais.

Auditorias de dependências não encontraram vulnerabilidades conhecidas nos snapshots finais pip/npm. Isso não substitui revisão de código, análise de arquitetura, pentest, atualização contínua ou cobertura de componentes nativos como PostgreSQL.
