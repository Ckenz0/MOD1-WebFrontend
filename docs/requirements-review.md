# Conferência dos requisitos — MVP P6 — 11/10/2026

## Referências e alcance

- Documento fornecido pelo aluno: `Projeto de Engenharia de Software com Microsserviços 2026-2.pdf`, páginas 2, 4 e 5.
- Slide da P6 fornecido: demonstração do MVP, link para a versão específica do código e demonstração na apresentação parcial.
- Orientação informada pelo aluno: nesta etapa o MVP pode executar localmente e representar uma parte do projeto, mostrando valor ao usuário.
- Recorte aprovado de projetos: `docs/superpowers/specs/2026-10-11-projects-mvp-design.md` no repositório de Brian.
- Identidade visual: `Guia_Visual_Modulo6.pdf`, v1.0, e `DESIGN.md` deste frontend.

A conferência abrange requisitos funcionais e dependências. O recorte aprovado é
cadastro → login → criação/consulta de projeto persistente, com acesso restrito ao
responsável. Ele não representa a conclusão do módulo 1 inteiro. Publicação das
branches, abertura de PRs e solicitação de revisão ficam com Caue, conforme pedido.

## Requisitos do recorte aprovado

| Requisito | Situação | Evidência |
| --- | --- | --- |
| Criar conta e entrar imediatamente | Atendido | API `/auth/register`, `/auth/token` e integração real do navegador |
| Validar nome, e-mail, senha e confirmação | Atendido | Backend, mensagens junto aos campos, foco no primeiro erro; confirmação apenas no frontend |
| Preservar conta existente em cadastro repetido | Atendido | Testes de duplicidade, senha original e conta inativa |
| Armazenar senha com hash e assinar JWT | Atendido | Argon2, RS256 e JWKS somente público |
| Consultar identidade e demonstrar permitir/bloquear acesso | Atendido | `/auth/me`, antes/depois de login e logout |
| Criar, listar e consultar os próprios projetos | Atendido | POST/GET `/projects`, paginação, detalhe |
| Definir responsável no servidor | Atendido | `owner_id` vem do `sub` validado; campos extras recusados |
| Impedir consulta a projeto de outra conta | Atendido | Filtros de responsável; UUID conhecido e inexistente retornam 404 |
| Persistir após reinício | Atendido | Integração isolada com APIs reais e smoke separado no Neon |
| Separar serviços e dados | Atendido | Identidade 8000 / schema `mod1_identity`; projetos 8001 / schema `projects`; sem FK/join entre módulos |
| Falhas recuperáveis e envio único | Atendido | Rede/503, clique duplicado, timeout e descarte de resposta antiga após logout |
| Interface conforme guia do módulo 6 | Atendido no recorte | Tokens, Inter, ações azul-marinho, temas, teclado e layout 390/1440; capturas em `screenshots/` |
| Mostrar valor ao usuário | Demonstrável | Registrar objetivo/escopo do projeto, reencontrar dados e proteger o conteúdo de outras contas |

Tokens ficam em memória no navegador. Logout não revoga JWT no servidor. Cadastro
não confirma posse do e-mail e não oferece recuperação de senha. Uma conta
desativada perde login e `/auth/me`; consumidores podem aceitar JWT emitido até
expirar. Esses limites acompanham a entrega, sem prometer funcionalidades ausentes.

## Requisitos do módulo completo

| Parte prevista no documento da disciplina | Situação nesta etapa |
| --- | --- |
| Autenticação/controle de acesso | Identidade e isolamento por responsável implementados |
| Cadastro e gerenciamento de projetos | Criar/listar/consultar implementados; editar/excluir ficam para evolução |
| Gestão de equipes | Ainda não implementada; responsabilidade do serviço de projetos |
| RBAC por projeto (PO, PM/Scrum Master, desenvolvedor/aluno) | Ainda não implementado; proprietário único não equivale a RBAC |
| Backlog/User Stories/tarefas | Ainda não implementado; próximo recorte do Igor após publicar projetos |
| IA para composição de equipes/permissões, aplicação sugerida no PDF | Ainda não implementada |
| Portal central do módulo 6 e integração com outros grupos | Frontend atual demonstra o MVP; integração com o portal definitivo permanece futura |

Deploy e CI/CD pertencem às próximas entregas do cronograma (P7/P8); Docker e
Azure não foram validados em execução nesta conferência. Esta avaliação comprova
o recorte local aprovado, sem substituir a avaliação do professor.

## Dependências e testes

| Repositório | Fonte das dependências | Resultado da conferência |
| --- | --- | --- |
| MOD1-EngenhariaSoftware | `pyproject.toml` + `uv.lock`, Python >= 3.12 | Lock atualizado, ambiente compatível, Ruff/formatação/mypy passaram |
| projeto_eng_soft | `pyproject.toml` + `uv.lock`, Python >= 3.12 | Lock atualizado, ambiente compatível, Ruff/mypy passaram |
| MOD1-Frontend | `tests/requirements.txt`, Python 3.12 para testes | Playwright/pyee/greenlet fixados e compatíveis; HTML/CSS/JS sem pacotes de produto |

Não é necessário duplicar as dependências dos backends em `requirements.txt`;
`pyproject.toml` define o pacote e `uv.lock` registra a resolução reproduzível.
PyJWT usa o extra `crypto`, pwdlib usa `argon2`, e psycopg usa `binary`. Bibliotecas
dos backends não são enviadas ao frontend. Para os testes integrados, ambas as APIs
precisam estar instaladas em suas `.venv` e os dois paths precisam ser configurados.

Resultados finais desta conferência:

- Autenticação: **108 passaram, 5 PostgreSQL local opt-in ignorados**.
- Projetos: **73 passaram, 1 PostgreSQL local opt-in ignorado**.
- Frontend: **48 passaram**, com ambas as APIs reais configuradas.
- Neon: evidência real anterior e consulta direta confirmaram persistência; os testes descartáveis não usam Neon.
- Wheel/sdist de projetos excluem arquivos privados; seleção atual do sdist e artefatos existentes da autenticação também foram conferidos.

A primeira execução do frontend mostrou uma falha de limpeza depois de um fluxo
bem-sucedido: `users.db` ainda estava ocupado no Windows. Foi acrescentada espera
limitada a 5 segundos, depois de encerrar os processos próprios, e uma regressão
com arquivo realmente aberto. Teste e suíte passaram após a correção.

Na autenticação, duas regressões comprovaram que `host`/`hostaddr` na query da URL
de teste passavam pela proteção de host. A fixture agora recusa esses parâmetros
antes de inicializar o banco. Nenhuma conexão remota foi usada nessa regressão.

## Antes de publicar e entregar

- **Autenticação ainda tem alterações sem commit** na worktree `feat/auth-mvp`.
  O último commit nela é `c4eeb15`, anterior à implementação atual. Publicar somente
  a branch nesse estado não envia os arquivos do novo serviço. Commitar o recorte
  revisado, excluindo arquivos ignorados, antes de disponibilizá-lo ao revisor.
- Projetos está em `feat/projects-mvp`, commit `9317975`; o frontend está em
  `feat/auth-ui`, com os commits de projetos e a correção de teste desta conferência.
  Confirmar que a publicação usa essas branches/worktrees.
- Incluir `Co-authored-by: Brian Freire <briankfreire@outlook.com>` nos novos commits,
  conforme a coautoria solicitada. Não reescrever commits anteriores.
- Manter `.env`, DSNs, senhas, JWTs, chaves e `.local/` fora dos commits. Isso já está
  coberto pelos arquivos de ignore e pela conferência de distribuição.
- Depois da publicação, usar links para os commits específicos do MVP, e não apenas
  a página inicial do repositório. Os links ficam pendentes da publicação do aluno.
- Capturas e roteiro estão em `docs/verification.md`; selecionar/gravar a demonstração
  a enviar e apresentar o fluxo. Um PR ou uma captura isolada não substitui todos os
  entregáveis do slide da P6.

O próximo backlog deverá usar o JWT de identidade e confirmar acesso ao projeto
pela API de projetos; não consultar diretamente schemas dos demais serviços. O
desenho desse recorte será discutido quando a entrega de projetos estiver publicada.
