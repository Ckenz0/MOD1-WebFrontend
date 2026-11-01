# Integração com o módulo 1

Este guia reúne os endereços e o contrato para integrar os outros módulos.
Esta entrega usa frontend 0.5.0, Identidade 0.4.0, Projetos 0.5.0 e Backlog 0.4.0.
Os endereços abaixo são os destinos de produção. As evidências finais, o SHA do
frontend implantado e os limites da validação estão nas
[notas da release 0.5.0](https://github.com/Ckenz0/MOD1-WebFrontend/releases/tag/v0.5.0).

| Componente | Endereço HTTPS |
| --- | --- |
| Frontend | https://green-river-02e44e810.2.azurestaticapps.net |
| Identidade | https://mod1-auth.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |
| Projetos | https://mod1-projects.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |
| Backlog | https://mod1-backlog.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |

## Conta e autenticação

Cada pessoa deve criar sua própria conta pelo frontend ou por
`POST /auth/register` na Identidade, enviando JSON com `display_name`, `email`
e `password`. O cadastro responde `202` sem token; depois faça login em
`POST /auth/token`, como formulário `application/x-www-form-urlencoded`, com
`username` igual ao e-mail e `password` literal. Consulte a política pública de
senha em `GET /auth/password-policy`. Contas com MFA seguem o desafio do serviço.

Envie o `access_token` como `Authorization: Bearer <JWT>` para cada API chamada.
Não coloque JWT em URL, configuração pública ou repositório e não use token fixo
compartilhado. Não compartilhe a conta `teste.local`, administrador local ou suas
credenciais; eles não são contas de integração dos grupos.

Para validar assinatura, configure RS256 e os valores confiáveis abaixo:

- Issuer: `https://mod1-auth.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io`.
- Audience: `engenharia-software-api`.
- JWKS: `https://mod1-auth.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io/.well-known/jwks.json`.

Não selecione algoritmo, issuer ou JWKS a partir de campos não verificados do
token. Os consumidores também devem respeitar o estado online da conta/sessão:
assinatura válida sozinha não comprova que uma sessão continua autorizada.

## Projetos, papéis e referências

Use o UUID retornado pela API de Projetos como `project_id` nas referências do
seu módulo e nas chamadas de Backlog. O identificador de projeto não é o ID de
usuário nem o ID de repositório GitHub. Cada API mantém somente seu próprio
schema; integrações usam HTTP e não consultas diretas ao banco de outro serviço.

Papéis declarados no JWT não concedem acesso global aos projetos. Consulte
`GET /projects/{project_id}/access/v2`, com o mesmo Bearer do usuário, para saber
as permissões atuais naquele projeto. Não trate PO, PM ou Desenvolvedor como
autorização universal. O servidor revalida cada operação; `403` não exige apagar
a sessão, e `404` pode representar projeto inacessível àquela conta.

Para acessar um projeto existente, enviem ao gestor o ID retornado por
`GET /auth/me`, peçam um convite com os papéis necessários e aceitem o convite
na interface. Cadastro e login não concedem acesso aos projetos de outras
pessoas. Também é possível criar um projeto próprio pela interface ou por
`POST /projects`; compartilhem seu `project_id` entre os módulos que o integram.

## Exclusão e GitHub Sync

`DELETE /projects/{project_id}` exige o proprietário e se destina a cadastros
vazios. Sucesso retorna `204` sem corpo: não chame `response.json()`. Conteúdo,
vínculos/histórico relevantes ou escritas em andamento retornam `409`; para
trabalho existente, use o ciclo de vida/arquivamento. Falha de dependência não
equivale a projeto vazio. Depois de timeout, consulte o projeto e atualize a
listagem antes de tentar novamente; não suponha sucesso.

Não há cascata entre serviços. O GitHub Sync deve administrar seus próprios
vínculos por `project_id`, conforme o contrato acordado entre os módulos. A
exclusão do cadastro não autoriza apagar repositórios, branches ou PRs do GitHub,
nem limpar referências de outros grupos implicitamente. O contrato completo
fica no repositório de Projetos, em `docs/module2-project-deletion.md`.

## CORS e validação conjunta

Para integrar pelo navegador, enviem ao responsável pela API a origem exata do
frontend: esquema, host e porta, sem caminho. `http://localhost:5173` e
`http://127.0.0.1:5173` são origens diferentes. A origem atual do frontend do
módulo 1 precisa ser preservada ao configurar `CORS_ORIGINS`. Até a preparação
deste guia, nenhuma URL de frontend externo dos outros grupos foi fornecida;
nenhuma liberação adicional de CORS está sendo afirmada.

No teste conjunto, confiram `/health/ready`, cadastro/login individual, acesso
permitido e negado por projeto e tratamento de `204`, `401`, `403`, `404`, `409`
e `503`. APIs suspensas podem precisar de tempo para retomar. Nunca repitam
automaticamente uma gravação cujo resultado ficou incerto.

IA real e o contrato efetivo de eventos com o módulo de revisão de código ainda
estão pendentes. A proposta local não comprova compatibilidade externa. E-mail
usa Resend na Identidade; houve envio/recebimento real de transporte para o
titular, mas o remetente de teste atual não permite afirmar entrega para outras
contas nem fluxo real completo de recuperação/confirmação.

## Registro da entrega

APIs conferidas por CK em 01/11/2026 às 17:02 UTC:

| API | Versão observada | Código implantado |
| --- | --- | --- |
| Identidade | 0.4.0 | [`f4aa7be`](https://github.com/Ckenz0/MOD1-IdentityService/commit/f4aa7be567cb603706933922350d5c97ab12c79f) |
| Projetos | 0.5.0 | [`3b4f942`](https://github.com/briankfreire/MOD1-ProjectsServices/commit/3b4f942982cdfc84ddb41ac1f30a0ee005c07694) |
| Backlog | 0.4.0 | [`8301009`](https://github.com/igorcpds/MOD1-BacklogService/commit/83010094dc794d3077e62a6cfe480d82472d0b86) |

As três responderam readiness 200, expuseram os novos contratos e preservaram
CORS para a origem atual do frontend. A chave pública JWT permaneceu igual à
anterior à atualização. Migrações tiveram backup e preservação dos dados
preexistentes conferidos. Isso não comprova a integração dos outros grupos.

O frontend expõe `/release.json` sem cache com versão e SHA implantados. As
notas da release vinculadas acima registram o workflow de publicação e a
validação final do fluxo entre APIs e pela interface pública, com seus limites.
Os testes de exclusão de projetos foram executados localmente; nenhuma exclusão
de dados de produção foi usada para validar esta entrega.
