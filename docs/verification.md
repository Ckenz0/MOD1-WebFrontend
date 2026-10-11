# Verificação do frontend

Execução em 10/10/2026, Windows, Python 3.12 e Microsoft Edge com Playwright.
Plano: `docs/superpowers/plans/2026-10-10-auth-frontend.md`.

## Extensão: cadastro público e acesso protegido

Verificada localmente em 10/10/2026, após a entrega inicial abaixo:

- **34 testes aprovados, zero falhas e zero skips**, em 32,177 s, usando o mesmo comando de suíte abaixo com `AUTH_BACKEND_PATH`.
- Sete testes novos de interface: validação de login, limites e confirmação de senha, preservação/limpeza de senha literal, primeira submissão em celular, domínio de e-mail, acesso sem sessão e distinção entre falha de rede e bloqueio.
- Quarto teste de API real: cadastro pelo navegador, login imediato e consulta protegida antes de entrar, após login e após sair. Essa suíte usa banco/chave/contas sintéticos isolados com SQLite.
- Demonstração separada no **Neon PostgreSQL**: uma conta sintética nova criada pelo navegador recebeu 202; login e acesso autenticado receberam 200; consultas sem sessão, antes do login e após logout, receberam 401. Cadastro repetido preservou a senha anterior.
- Capturas reais em 1440 × 1100 e 390 × 844; temas claro/escuro, nenhum overflow horizontal e zero erros de JavaScript.
- Revisão independente sem achados críticos ou importantes. A diferença de validação de nome/e-mail foi corrigida com regressões. O deslocamento de botão causado pela validação no blur em celular também foi reproduzido e corrigido: ao focar submit, a validação aguarda a submissão para não deslocar o alvo do clique.

| Estado | Captura real |
| --- | --- |
| Cadastro / desktop claro | [Captura](screenshots/registration-desktop-light.png) |
| Cadastro / celular escuro | [Captura](screenshots/registration-mobile-dark.png) |
| Campos inválidos / celular escuro | [Captura](screenshots/validation-mobile-dark.png) |
| Acesso permitido / desktop claro | [Captura](screenshots/access-allowed-desktop-light.png) |
| Acesso bloqueado após sair / celular escuro | [Captura](screenshots/access-blocked-mobile-dark.png) |

O cadastro atual permite login imediato e não verifica posse do e-mail. Administração e desativação continuam na CLI. As alterações desta extensão estão na worktree; os dados e a revisão da entrega inicial abaixo são históricos.

## Resultado reproduzível da entrega inicial

```powershell
$env:AUTH_BACKEND_PATH = 'C:\Users\cauek\.codex\worktrees\2ecd\MOD1-EngenhariaSoftware'
uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
git diff --check
```

Resultado final: **26 testes aprovados, zero falhas, zero skips**, em 25,153 s.
`git diff --check` passou. A integração usa a implementação `feat/auth-mvp`
do backend, com SQLite, chave RSA e conta sintéticos temporários.

| Área | Evidência | Limite |
| --- | --- | --- |
| Cliente HTTP e sessão | 6 testes: formulário literal, Bearer, validação de respostas, erros seguros, timeout/cancelamento, expiração e ausência de persistência | Respostas controladas no navegador |
| Interface | 17 testes: identidade confirmada, senha, teclado, envio único, saída, resposta atrasada, expiração, atualização, 401, rede, tema, recarga, texto não confiável, contraste de seleção e inicialização segura | Microsoft Edge; não substitui auditoria com leitor de tela |
| API real | 3 testes: login/JWT/identidade/atualização/saída, CORS bloqueado e conta desativada | HTTP real com SQLite; não valida PostgreSQL |
| Identidade visual | Tokens do guia do módulo 6, fontes locais licenciadas, claro/escuro e oito capturas | Sem logotipo oficial disponível; identificação textual e ícone geométrico |
| CLI, JWKS, saúde, hashing e regras JWT | Cobertos pela suíte própria do backend; verificação anterior: 93 aprovados e 6 pulados | Não expostos como telas; essa suíte não foi reexecutada nesta entrega |
| PostgreSQL, Docker e deploy | Pendentes | Não comprovados pelos testes do frontend |

## Inspeção visual

Login e perfil inspecionados em **1440 × 1000** e **390 × 844**, nos dois temas.
As oito combinações carregaram Inter local, mantiveram textos de pelo menos 12 px
e não tiveram overflow horizontal. Foco visível, labels, regiões de alerta/status,
texto longo e navegação por teclado foram conferidos. A seleção de texto no tema
escuro tinha contraste de 1,23:1; o teste reproduziu a falha e passou após manter
o primeiro plano branco sobre o azul primário. O alvo do botão de senha mede 44 px.

Capturas com conta sintética, após concluir a animação de entrada:

| Tamanho | Claro | Escuro |
| --- | --- | --- |
| Desktop / login | [Captura](screenshots/desktop-light-login.png) | [Captura](screenshots/desktop-dark-login.png) |
| Desktop / perfil | [Captura](screenshots/desktop-light-profile.png) | [Captura](screenshots/desktop-dark-profile.png) |
| Celular / login | [Captura](screenshots/mobile-light-login.png) | [Captura](screenshots/mobile-dark-login.png) |
| Celular / perfil | [Captura](screenshots/mobile-light-profile.png) | [Captura](screenshots/mobile-dark-profile.png) |

## Escopo da demonstração inicial

O frontend permite verificar o fluxo público de autenticação implementado.
Administração de contas continua na CLI. Sair limpa a sessão local e não revoga o
JWT no servidor; recarregar exige novo login. Sem cadastro, recuperação de senha,
refresh token ou telas de projetos, equipes e backlog. O portal final será
integrado ao módulo 6.

## Revisão independente

Revisão da branch `862ebd3..f822233` concluída: nenhum achado crítico ou menor;
um achado importante corrigido. Quando o JavaScript estava desabilitado ou o
módulo falhava ao carregar, o formulário nativo podia enviar credenciais pela URL.

Os controles agora permanecem desativados até todos os handlers serem instalados.
O fallback usa POST e os campos desativados não enviam credenciais. Os dois testes
de regressão falharam antes da correção e passaram depois; também exercitam o envio
nativo forçado com valores sintéticos. A suíte completa passou com 26 testes,
incluindo o envio normal pelo teclado. Sem nova rodada de revisão: o achado foi
verificado por regressão e pela suíte, conforme o método de execução aprovado.

PostgreSQL/Docker/deploy e revogação no servidor foram considerados na revisão:
permanecem, respectivamente, pendentes de validação e fora do contrato de logout local.

Entrega publicada na branch `feat/auth-ui`, com [PR #1 em rascunho](https://github.com/Ckenz0/MOD1-Frontend/pull/1)
para revisão. A worktree local foi preservada para execução e ajustes.

## Projetos do Brian — 11/10/2026

Ampliação do frontend com **Meus projetos**, criação validada, listagem paginada,
consulta de detalhe, retorno à conta e saída. Usa a API independente na porta 8001,
JWKS de identidade e persistência Neon no schema `projects`.

O fluxo com duas APIs reais passou: cadastrar A, entrar pelo navegador, criar um
projeto, reiniciar projetos, reencontrar os dados e verificar lista vazia/404 para B.
Smoke separado no Neon comprovou 201 na criação, 404 para outra conta, 401 sem
autenticação e 200 para o mesmo projeto após reinício da API.

Capturas de uma inspeção conjunta, usando apenas dados sintéticos:

- [Desktop claro](screenshots/projects-desktop-light.png)
- [Celular escuro](screenshots/projects-mobile-dark.png)
- [Validação no celular](screenshots/projects-validation-mobile.png)

Os testes também cobrem nome/descrição em Unicode, HTML mostrado como texto,
submissão única, erro recuperável, teclado e descarte de respostas antigas após
logout/troca de sessão. Layout 390/1440 sem overflow horizontal.

Resultado: **47 testes passaram**, sem skips quando `AUTH_BACKEND_PATH` e
`PROJECTS_BACKEND_PATH` estão configurados. Backend de projetos: **73 passaram,
1 teste PostgreSQL local opt-in pendente**; lint, tipos e wheel/sdist passaram.
Revisão independente final concluída. Os dois achados importantes sobre JWKS
foram corrigidos com testes de regressão; uma auditoria adicional garantiu que
wheel/sdist excluem configurações privadas. Após as correções e outro reinício,
o mesmo projeto persistido no Neon retornou 200.
