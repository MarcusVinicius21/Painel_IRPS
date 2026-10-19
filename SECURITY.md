# Segurança do IRPS

Esta implementação foi validada em ambiente local de testes. Não recebe dados privados reais nem configura implantação automática.

- Não versionar `.env`, `.runtime`, senhas, chaves privadas, tokens, cookies, arquivos de sessão ou bancos.
- A configuração local é explícita e gerada com valores aleatórios novos por instalação. O proprietário do schema não é a conta SQL da API.
- Contas fictícias e emissor local servem somente para loopback. Produção exige identidade externa HTTPS e remoção do acesso por contas de teste.
- Isolamento por organização, RLS, autorização por ação, CSRF e revogação são exercitados nos testes. Isso não equivale a certificação de segurança.
- Documentos reais exigem isolamento dos parsers, antivírus, política de retenção e gestão de acesso antes de qualquer uso.
- Serviços externos de IA permanecem bloqueados. Não inserir chaves para contornar essa proteção.

Se encontrar uma vulnerabilidade, comunique ao mantenedor por um canal privado já estabelecido. Informe o caminho, o comportamento e uma reprodução sintética. Não inclua credenciais ou dados de clientes, nem abra uma discussão pública com esses conteúdos.

Auditoria do envio inicial: [SEGURANCA_PUBLICACAO.md](docs/validacao/SEGURANCA_PUBLICACAO.md). Não há garantia absoluta de ausência de falhas; mantenha as verificações antes de cada envio futuro.
