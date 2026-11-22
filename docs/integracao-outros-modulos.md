# Integração com o módulo 1

Este guia reúne os endereços e o contrato para integrar os outros módulos.
O código implantado até 22/11/2026 usa frontend 0.8.0, Identidade 0.5.0,
Projetos 0.7.0 e Backlog 0.6.0. As referências de 15/11 abaixo preservam o
registro histórico. Os endereços abaixo são os destinos de produção, sujeitos
ao bloqueio operacional descrito a seguir. As evidências e seus limites estão
em [verification.md](verification.md); `/release.json` identifica o SHA do
frontend efetivamente implantado.

A versão 0.8.0 usa a [curadoria da API de Projetos 0.7.0](module5-curation.md).
O navegador acessa as duas rotas de curadoria pela origem de Projetos, com o
Bearer atual e `project:read`. A integração externa é configurada nesse backend.

| Componente | Endereço HTTPS |
| --- | --- |
| Frontend | https://green-river-02e44e810.2.azurestaticapps.net |
| Identidade | https://mod1-auth.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |
| Projetos | https://mod1-projects.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |
| Backlog | https://mod1-backlog.whitemeadow-deba1090.brazilsouth.azurecontainerapps.io |

## Disponibilidade e banco de dados — 22/11/2026

O PostgreSQL no Neon está recusando as conexões das três APIs por cota excedida.
Isso impede o aceite funcional em produção, incluindo login e operações que
dependem do banco, mesmo com o código implantado. As novas releases de Projetos
0.7.0 e Frontend 0.8.0 permanecem em rascunho até a validação operacional.

A troca de provedor do PostgreSQL está em avaliação e ainda não foi executada.
Ela deve preservar os endereços, rotas, formatos de requisição e resposta,
Bearer RS256, issuer, audience, JWKS e origens CORS das APIs. Os módulos que
integram por HTTP devem continuar usando os mesmos endpoints; a conexão com
o banco é configuração privada dos backends. Cada API continua restrita ao
próprio schema, e o frontend continua sem acesso direto ao banco.

Essa compatibilidade também depende de preservar os dados e seus UUIDs.
Uma restauração de backup antigo não recupera automaticamente contas, projetos
ou itens criados depois dele: referências desses registros nos outros módulos
podem retornar `404`. Antes de qualquer troca, é necessário definir quais dados
serão mantidos e validar autenticação, permissões e referências entre módulos.
Sessões podem exigir novo login após uma restauração. Nenhum endpoint, banco
ou dado foi alterado por esta atualização de documentação.

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
módulo 1 precisa ser preservada ao configurar `CORS_ORIGINS`.

As três APIs já permitem estas quatro origens, verificadas por preflight em
15/11/2026:

- `https://green-river-02e44e810.2.azurestaticapps.net`
- `https://mackai-conversas.calmfield-d7c6c49f.brazilsouth.azurecontainerapps.io`
- `https://ai-platform-github-service-eduardo-frapb8fbbcd0bfdm.brazilsouth-01.azurewebsites.net`
- `http://localhost:5173`

Isso não confirma CORS recíproco nas APIs dos outros grupos. Outros frontends
devem informar sua origem exata. O envio de notificações ao Módulo 6 ocorre
entre backends e não depende de CORS; a chave de integração fica no servidor.

No teste conjunto, confiram `/health/ready`, cadastro/login individual, acesso
permitido e negado por projeto e tratamento de `204`, `401`, `403`, `404`, `409`
e `503`. APIs suspensas podem precisar de tempo para retomar. Nunca repitam
automaticamente uma gravação cujo resultado ficou incerto.

Gemini real e Resend estão configurados nas APIs. Os links reais de confirmação
e recuperação foram validados em ambiente isolado, com entrega reportada pelo
Resend. O Módulo 4 está integrado por análise síncrona via Backlog; a proposta
legada de eventos permanece desabilitada. [Contrato atual](module4-reviews.md).

## Registro da entrega

APIs conferidas na publicação de 15/11/2026:

| API | Versão observada | Código implantado |
| --- | --- | --- |
| Identidade | 0.5.0 | [`e4a2e70`](https://github.com/Ckenz0/MOD1-IdentityService/commit/e4a2e70130d2bf80b5425e24b06d69d00b107275) |
| Projetos | 0.6.0 | [`ebdacfe`](https://github.com/briankfreire/MOD1-ProjectsServices/commit/ebdacfe3b3abaa687933e89da2c1b7ba6c5088d0) |
| Backlog | 0.5.0 | [`35898bd`](https://github.com/igorcpds/MOD1-BacklogService/commit/35898bd2a0287ef5efeb202d54601fd031ceabaf) |

As três responderam readiness 200, expuseram os novos contratos e preservaram
CORS para a origem atual do frontend. A chave pública JWT permaneceu igual à
anterior à atualização. Migrações tiveram backup e preservação dos dados
preexistentes conferidos. Isso não comprova a integração dos outros grupos.

O frontend expõe `/release.json` sem cache com versão e SHA implantados. As
evidências de validação registram o fluxo entre APIs e pela interface pública,
com seus limites. Esta tabela registra a publicação verificada, não cada commit
posterior de testes/documentação.
Os testes de exclusão de projetos foram executados localmente; nenhuma exclusão
de dados de produção foi usada para validar esta entrega.

## Code Review pelo Módulo 1

Use as rotas de revisões do Backlog com o mesmo Bearer do usuário. A senha
Basic do Módulo 4 nunca é repassada ao frontend ou aos consumidores.
`GET /projects/{project_id}/items/{item_id}/code-reviews` lista o histórico local
autorizado; `POST` no mesmo caminho solicita análise de PR ou arquivos Python,
com `request_id` e `expected_version`. Não espelhe o histórico global do M4.
Resultados incertos devem ser consultados antes de qualquer nova análise;
não repita POST automaticamente. [Campos e limites](module4-reviews.md).
