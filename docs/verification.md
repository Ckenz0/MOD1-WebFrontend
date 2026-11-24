# Validação do frontend

## M?dulo 3 ? valida??o de 24/11/2026

- Dez testes focados de interface/cliente bin?rio: v?nculo manual, somente leitura
  para leitores, filtros, vers?es, download expl?cito, navega??o com resposta
  antiga, falha do provedor, retirada de conte?do ap?s recusa e a??es no celular.
- A su?te local executou 207 testes, com 16 opt-ins ignorados nessa configura??o;
  dois casos novos de erro foram inclu?dos posteriormente nos dez testes focados.
- Aceite adicional com duas APIs M1 reais, SQLite tempor?rio e M3 por HTTP loopback:
  login, v?nculo persistido, vers?es, download de bytes e acesso recusado ? segunda
  conta. O provedor recebeu somente GET sem token M1. N?o houve chamada externa
  de escrita, e-mail ou notifica??o de teste.
- Desktop claro 1366px e celular escuro 390px, sem overflow da p?gina. A??es de
  arquivos permanecem acess?veis no celular sem rolagem lateral.
- Valida??o do cliente backend com o M3 real: GET de cat?logo/arquivos/vers?es e
  download aprovados. N?o foi atribu?do v?nculo a um projeto M1 de produ??o.
- Resumos/classifica??es aguardam contrato GET para descobrir a an?lise. Esses
  testes n?o representam an?lise IA, teste PostgreSQL ou deploy Azure.
  [Uso e limites](module3-artifacts.md).


## Aceite controlado do Módulo 5 — 18/11/2026

O frontend 0.8.0 foi exercitado com as APIs temporárias de Identidade,
Projetos 0.7.0 e Backlog e um provedor Módulo 5 em loopback. O navegador
verificou que abrir o projeto não consulta o provedor, abrir **Curadoria**
carrega o feed e cada clique explícito em **Buscar artigos** envia uma pesquisa.
O provedor recebeu `GET /feed` sem Bearer e `POST /consultas` com o Bearer da
sessão e somente `pergunta` no corpo. O teste confirmou lista de resultados,
retorno vazio, `503` com aviso de resultado incerto, ausência de reenvio
automático e igualdade do registro do projeto antes e depois.

Os cenários de interface cobrem projeto arquivado, permissão de leitura,
pré-preenchimento a partir de treinamento, limites da pergunta, links e texto
seguros, integração desativada, fontes indisponíveis, truncamento, timeout,
duplo envio, descarte de respostas antigas e encerramento por `401`.
Abrir Curadoria durante a leitura de Contexto libera a navegação e mantém
o carregamento restrito ao feed. O teste também confirma que uma resposta
antiga de Contexto não libera os controles de uma requisição mais nova. As
capturas em 1366 px no tema claro e 390 px no escuro foram inspecionadas
visualmente. Nenhuma largura apresentou rolagem horizontal na seção.

A suíte completa do frontend com os três backends executou **198 testes em
316,452 s, com 196 aprovações e 2 opt-ins ignorados**. Os opt-ins usam
Resend e Gemini reais. A verificação da Curadoria usou exclusivamente
serviços locais e contas descartáveis.

Na API de Projetos, o CI do commit `ef233ea` aprovou 408 testes e ignorou
11 opt-ins após a correção do prazo de DNS. O alcance dessa suíte inclui
autorização e contrato das duas rotas, revalidação após comunicação externa
e limites do adaptador. Veja [contrato e reprodução](module5-curation.md).

## Aceite do Módulo 4 — 16/11/2026

A regra aprovada foi implementada e validada: uma análise válida inicia somente
itens a fazer; trabalho em andamento/concluído permanece como está e conclusão
é manual. Os registros são restritos ao projeto/item, persistidos antes do POST
e recuperáveis após reinício. Repetir o UUID com conteúdo igual não chama o
provedor; conteúdo diferente conflita. Falhas, versão ou acesso alterados não
concluem itens nem provocam retry automático. O ingresso legado de eventos
permanece desabilitado e separado da API síncrona real do Módulo 4.

- Backlog: **491 testes aprovados**, incluindo migração aditiva e concorrência
  em PostgreSQL descartável local. Ruff, formato e mypy passaram.
- Frontend: **187 testes executados, 185 aprovados e 2 opt-ins ignorados**,
  usando as três APIs temporárias. Os ignorados são Resend/Gemini reais, já
  validados na entrega anterior e não repetidos por esta alteração.
- O aceite controlado de navegador exercitou sucesso, Basic dedicado, texto
  seguro, replay, reinício e resposta incerta sem alteração do item. A revisão
  independente encontrou e acompanhou as correções de recuperação após 409,
  avisos entre páginas e indisponibilidade JWKS; não restaram achados materiais.
- Uma rodada de aceite com o serviço M4 real passou: análise estática de código
  fictício, **HTTP201**, um POST nessa rodada, transição `todo→in_progress`,
  persistência após reinício e replay sem segundo POST. IA não foi solicitada;
  não se infere que testes do código foram executados. O resultado informou
  `testes_executados=false`. Não houve comentário em PR nem criação/alteração de
  entidade de negócio de produção por esse teste.
- O segredo Basic é exclusivo da API do Backlog. O patch de publicação preserva
  CORS, JWT, Gemini e M6 e não repassa essa senha ao worker de notificações.
  A tabela própria foi preparada de forma aditiva, após backup validado,
  com SELECT/INSERT/UPDATE para runtime e sem acesso a outros schemas.

O histórico global do provedor não é disponibilizado aos usuários do módulo.
Respostas e Markdown são exibidos como texto; novo envio após resultado
desconhecido exige ação explícita e indicação de possível duplicidade.

Contrato, interface e comandos: [module4-reviews.md](module4-reviews.md).

## Histórico — validação de 15/11/2026

O frontend 0.6.1 corrige permissões e navegação e fecha os testes de aceite de
e-mail/IA. A [matriz](backlog-status.md) registra 99 US implementadas, US-096
bloqueada por contrato externo e US-101 duplicada. Consulte também o
[registro de fechamento](final-delivery.md).

## Suíte final local

**172 testes executados em 244,447 s: 170 aprovados e 2 ignorados por opt-in.**
Os dois ignorados são os testes reais Resend/Gemini, executados separadamente
com sucesso e com autorização para chamadas externas. Os três caminhos de
backend estavam configurados para checkouts com os pacotes instalados. As APIs
do harness usam SQLite, RSA e contas temporários em portas loopback.

```powershell
# Defina AUTH_BACKEND_PATH, PROJECTS_BACKEND_PATH e BACKLOG_BACKEND_PATH.
$env:MAIL_PROVIDER = 'auto'
$env:AI_PROVIDER = 'structured-http'
$env:AI_SIMULATED = 'false'
$env:MODULE6_ENABLED = 'false'
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

Execute a suíte normal sem variáveis privadas `RESEND_*` ou opt-ins externos.
As regressões finais incluem 9 testes de permissões e 2 de navegação,
reproduzidos antes das correções. A revisão independente reexecutou esses
11 testes e não deixou achados críticos/importantes. As fronteiras entre
apresentação, aplicação, domínio e clientes HTTP continuam verificadas.

## Provedores reais

- **Resend:** um cenário de navegador aprovado, duas mensagens reais com
  entrega reportada pelo provedor. Links retornados pelo Resend confirmaram
  e-mail/reset; replay recusado, fragmento removido, senha anterior recusada,
  sessões anteriores invalidadas nas três APIs e MFA preservado. Nenhuma conta
  de produção foi alterada. [Reprodução e limites](email-acceptance.md).
- **Gemini:** um cenário de navegador aprovado, sete chamadas HTTP 200 ao host
  oficial, propostas persistidas e preservadas após reiniciar as três APIs.
  Papéis e backlog tiveram aprovação explícita/idempotente; revogação expirou
  diante de contexto alterado, sem revogar acesso. Equipes retornou vazio válido,
  sem alegação de aprovação real de equipe nessa rodada. Perfil sem consentimento
  e credenciais foram excluídos do corpo. [Resultados por tipo](local-ai-testing.md).

## Publicação e integrações

Na publicação de 15/11 foram conferidos Identidade 0.5.0, Projetos 0.6.0,
Backlog 0.5.0 e a primeira publicação frontend 0.6.0. O patch final 0.6.1 está
descrito no changelog. `/release.json` registra versão/SHA efetivamente publicados;
o arquivo VERSION sozinho não comprova deploy.

Os quatro deploys da publicação foram aprovados. Saúde pública, 10 verificações
de login/JWT/acesso/logout entre APIs e navegador de produção passaram. A chave
JWT/JWKS permaneceu igual. Foram aprovados 36 preflights CORS e bloqueadas
3 origens negativas. Após logout, as três APIs recusaram o Bearer anterior.
Não houve erro JavaScript ou overflow observado em desktop/mobile nessa rodada.

Os workers de Backlog/Projetos para o Módulo 6 foram verificados prontos. Um aviso
real com escopo de projeto foi aceito com HTTP 200. Isso não comprova a
apresentação na Central nem cria eventos de negócio artificiais em produção.
CORS do Módulo 1 para Módulos 2/7 foi liberado; liberação recíproca é externa.

Inspeção dos arquivos candidatos não encontrou credenciais reais ou arquivos
locais protegidos rastreados. Links Markdown locais e `git diff --check` passaram.
Produto e evidências publicadas não dependem de planos privados.

As seções abaixo são históricas: seus estados de IA/e-mail, versões e limites
descrevem a data registrada, e não substituem o aceite final acima.

## Histórico — preparação da versão 0.5.0 — 01/11/2026

A suíte completa executou **152 testes aprovados, sem skips, em 181,392 s**,
usando `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Os três
caminhos de backend estavam configurados para os checkouts da entrega. O
processo de testes recebeu `MAIL_PROVIDER=auto` e nenhuma variável `RESEND_*`.
As fixtures inicializaram APIs reais locais com SQLite, RSA e contas temporários;
não usaram banco de produção ou transporte real de e-mail.

Essa execução inclui os fluxos de MFA/confirmação/reset locais, revogação nos
consumidores, planejamento/papéis/quadro e as regressões do refinamento premium
para filtros móveis e contraste de foco. A revisão visual independente das
36 capturas e das correções está em [premium-frontend.md](premium-frontend.md).

O artefato de deploy foi reproduzido em diretório temporário copiando somente
`public/` e gerando a configuração das três APIs HTTPS: **37 arquivos**, com
`config.js` sem cache e sem arquivos privados ou padrões de segredos encontrados
na inspeção. Links locais de README e nove documentos foram conferidos sem
destinos ausentes; `git diff --check` passou. Arquivos locais de agentes,
Superpowers e `.local/` não estão rastreados.

O transporte Resend teve envio/recebimento real confirmado separadamente para o
titular. O remetente de teste atual limita os destinatários a essa conta. Essa
evidência de transporte não substitui teste externo ponta a ponta de reset ou
confirmação. IA real e contrato efetivo do módulo de revisão seguem pendentes.
Os testes e a preparação descritos aqui não comprovam push, tag, merge,
disponibilidade de produção ou deploy da versão 0.5.0.

## Histórico — validação adicional de 31/10/2026, funcionalidades locais

Na branch local `feat/remaining-user-stories`, a suíte completa com
`AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH`
apontando para os worktrees locais executou **150 testes, todos passaram, sem
skips**, em 180,595 s. Comando: `python -m unittest discover -s tests -v`.

O Edge headless exercitou APIs reais em portas loopback, bancos SQLite
temporários e chaves próprias. Os fluxos novos incluem metadados/orçamento/
datas, papel personalizado, história orientada/MoSCoW/estimativa, arrastar para
ordenar e atualizar status, MFA com recuperação, confirmação de e-mail e reset.
Reset revoga a credencial anterior também em Projetos e Backlog. Parar a API de
Identidade durante uma edição retorna indisponibilidade, preserva os campos e
permite repetir a gravação após o reinício.

Testes controlados também verificam caixa de notificações, equipe/convite,
sessões e revogação, limites de inatividade/validade absoluta, renovação única,
cancelamento da primeira tela durante rotação e logout durante resposta tardia.
Retornar do fluxo de token público limpa também a identidade anterior, impedindo
que uma verificação de expiração remova o formulário de recuperação em seguida.
Recomendação simulada mostra janela de observação e exige decisão humana;
projetos em consulta ocultam ações de alteração de dados.
O editor compacto de membros preserva papéis personalizados e os prazos por
papel, inclusive concessões sem expiração, ao editar os papéis fixos.
Os testes de fronteira impedem HTTP/DOM nas camadas puras.

Inspeção desktop/claro e móvel/escuro preservou o guia visual existente; a tabela
usa rolagem horizontal em telas estreitas. O detector visual emitiu apenas
avisos sobre cores já presentes em DESIGN.md. Capturas com dados sintéticos
permanecem locais. Não houve publicação, SMTP externo ou IA real.

As limitações e os caminhos de teste estão em
[local-user-stories.md](local-user-stories.md) e
[backlog-status.md](backlog-status.md).

## Histórico das validações anteriores

# Validação do frontend 0.2.0 — 11/10/2026

## Arquitetura multicamadas — 30/10/2026

- Organização concluída preservando os arquivos atuais: apresentação, aplicação
  de conta/workspace, domínio/contratos e transporte HTTP. Sem mudança de versão,
  HTML/CSS, rotas públicas ou dados de produção. Ver [architecture.md](architecture.md).
- Baseline: 100 testes, 8 integrações puladas por ausência dos caminhos dos backends.
- RED de arquitetura: sessão importava transporte e quatro telas importavam
  clientes HTTP concretos. Após extração, testes dessas fronteiras passaram.
- Casos de uso e domínio: login/identidade/sessão, logout com respostas antigas,
  cancelamento, expiração, falha após emissão do token, troca de senha, leituras
  compostas, normalização de competências e alterações de história por papel.
- Revisão independente das quatro mudanças não encontrou regressão funcional ou
  de segurança; apontou uma lacuna de testes sem DOM. A correção adicionou execução
  real de conta/workspace e dos módulos puros em Worker sem DOM e com fetch bloqueado,
  mais proteção de imports/globais. A fixture negativa do verificador falhou antes
  da implementação e passou depois; os dez testes de conta e sete de fronteiras passaram.
- Integração com os três backends refatorados: primeiro 120 testes aprovados sem
  skips em 130,357 s; após reforço da verificação, **124 testes aprovados sem skips
  em 113,660 s**. A execução final usou a mesma descoberta `unittest` com um runner
  de diagnóstico que registra erros JS/requisições sem alterar os testes ou produto.
- Uma execução intermediária de 124 testes teve um timeout de 4 s ao preencher
  o e-mail ainda desativado no setup de `test_logout_then_other_login_ignores_late_project_response`.
  Seis repetições isoladas passaram em 6,302 s; o problema não se reproduziu na
  suíte final instrumentada. Não foi alterado código nem timeout para ocultá-lo;
  a causa desse episódio isolado não foi estabelecida.
- O fluxo de colaboração/perfil com duas contas e três APIs reais passou,
  incluindo aceite de convite, status por Desenvolvedor, promoção a PO e remoção.
- Ambiente local reiniciado com o código refatorado e os mesmos bancos locais:
  três readiness HTTP 200, CORS correto, login da conta de teste existente e
  listagem de projetos HTTP 200 pelo Edge, sem erros JavaScript. Nenhum registro
  foi apagado; esse smoke fez apenas login e consultas.
- PostgreSQL, Docker e Azure não foram revalidados nesta etapa; fixtures usam
  SQLite e RSA temporários. As evidências históricas abaixo não substituem esse limite.

Para reproduzir a suíte, prepare os quatro ambientes conforme o README e defina
`AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH` com os checkouts
de Identidade, Projetos e Backlog que serão testados. Execute:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Os bancos dos testes reais são temporários e locais; não configure credenciais
de produção. Não há necessidade de acessar um arquivo de plano local para executar
ou interpretar os resultados acima.

## Conferência para PR — 30/10/2026

- Suíte completa: **100 testes aprovados, nenhum skip**, em 224.293 s, com
  as três APIs reais e SQLite/RSA temporários.
- Quatro regressões para falha/recarregamento do perfil, mudança remota de papel
  em membros e backlog e perda completa de acesso aos membros (404).
- Falha inicial do perfil mantém edição/Salvar desativados e oferece retentativa;
  atualização/reabertura consulta permissões atuais e remove controles revogados.
- Novos testes reproduziram as falhas antes das correções; a fixture de resposta
  atrasada do Backlog foi adaptada à consulta de permissões e voltou a passar.
- Revisão independente do frontend concluída; achados importantes corrigidos e
  diff final aprovado. Evidências anteriores abaixo referem-se aos estados históricos.
- Backends revalidados com PostgreSQL descartável: Identidade 200, Projetos 137,
  Backlog 194 aprovados sem skips. Checks API/container dos três PRs passaram.

## Colaboração/perfil 0.4.0 — 28/10/2026, somente local

- Suíte completa: **96 testes aprovados, nenhum skip**, em 131,831 s, com as três
  APIs reais e SQLite/RSA temporários. Nenhuma credencial ou banco remoto.
- Teste ampliado de duas contas passou separadamente em 13,943 s: código de convite,
  perfil, acesso Desenvolvedor/status, promoção a PO na UI/API, remoção e código usado negado.
- Backends completos com PostgreSQL descartável: Identidade 200, Projetos 137,
  Backlog 194 aprovados sem skips. ICU und preserva os testes de busca Unicode.
- Seis capturas locais em `.impeccable/review/`: perfil, backlog Desenvolvedor e
  membros; desktop claro 1366×900 e celular escuro 390×844, sem overflow horizontal.
  Revisão visual própria preservou Inter, tokens e identidade do módulo 6.
- Detector Impeccable manteve avisos históricos de paleta/Inter definidos pelo guia;
  não representam troca de marca ou dependência nova.
- Revisão independente deste lote indisponível por limite dos auxiliares;
  revisão própria e testes concluídos. Evidências históricas abaixo não a substituem.
- Tudo local: sem publicação, deploy, tag, push ou alteração de main.

Windows, Python 3.12.15 e Playwright com Microsoft Edge. A suíte completa executou
**63 testes aprovados, sem skips**, com os três caminhos de backend configurados.
O backend do backlog executou 118 testes aprovados e um skip PostgreSQL local opt-in.

Os quatro componentes foram exportados somente com arquivos públicos para árvores
novas; ambientes Python 3.12 foram instalados do zero e a suíte integrada foi
reexecutada usando exclusivamente esses checkouts, sem configuração privada do desenvolvedor.

## Evidência integrada

Cadastro pelo navegador → login → projeto → duas histórias → prioridade alta e
status concluído → reinício do backlog → história recuperada. Outra conta recebeu
404 nas quatro operações; história de outro projeto também ficou inacessível.
Sem token, 401. As três APIs desse teste usam apenas SQLite/RSA/contas temporários.

Separadamente, a instância de desenvolvimento no Neon confirmou TLS verify-full,
schema `backlog`, runtime com SELECT/INSERT/UPDATE e ausência de CREATE/DELETE/acesso
às tabelas dos outros módulos. Criação, alteração, leitura e recuperação após
reinício da API foram verificadas sem exclusão de registros ou schemas.

## Interface

Formulários validam título 1–120 Unicode e descrição/critérios até 2000; foco vai
ao primeiro erro. HTML aparece como texto; quebras de linha são preservadas.
Testes cobrem paginação, prioridade/status, reabertura, duplo envio, 401/404/503,
respostas antigas após troca de projeto/logout e sucesso seguido de recarga falha.
Essa falha confirma a gravação, sem reenviar automaticamente.
Quando a recarga retorna 401, o login preserva a confirmação de criação ou
atualização junto ao aviso de sessão encerrada. A normalização dos espaços Unicode
concorda com o backend; histórias antigas com espaços adicionais continuam legíveis.

Capturas geradas pela fixture com dados sintéticos, APIs reais temporárias e viewport
desktop 1366×900 / celular 390×844. Não incluem tokens, credenciais ou contas reais.

![Backlog no desktop, tema claro](screenshots/backlog-desktop-light.png)

![Backlog no celular, tema escuro](screenshots/backlog-mobile-dark.png)

[Confirmação de criação preservada após a sessão expirar](screenshots/backlog-created-session-expired.png).
Essa captura usa respostas controladas para reproduzir POST 201 seguido de GET 401;
as duas capturas do backlog acima usam os três serviços reais temporários.

## Reproduzir e apresentar

Instale os ambientes e configure `AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH`,
`BACKLOG_BACKEND_PATH` como no [README](../README.md). Execute a suíte completa.
Sem nenhum caminho, seis integrações são puladas explicitamente.
Para renovar capturas sintéticas, a fixture de backlog aceita
`CAPTURE_BACKLOG_EVIDENCE` com um diretório local de saída.

Mostre uma necessidade do usuário e seus critérios, a entrega principal primeiro,
o progresso salvo e o bloqueio para outra conta. Isso demonstra organização e
acompanhamento de entregas, além do login. Grave/capture a demonstração e vincule
a versão específica do código publicada para a apresentação P6.

PostgreSQL destrutivo local não executou (sem banco loopback configurado; daemon
Docker indisponível). O smoke Neon é separado. Docker/deploy/CI/CD permanecem
fora da validação; equipes/RBAC e demais funções do módulo completo continuam futuras.
# Gerenciamento básico integrado — candidato 0.3.0 — 28/10/2026

- Baseline: 73 testes, com seis integrações opt-in puladas antes de configurar APIs.
- TDD do lote: seis testes novos falharam por ausência dos clientes/controles;
  os cenários passaram após implementar os contratos e formulários.
- **Suíte final: 85 testes aprovados, nenhum skip**, em 156,50 s, com
  `AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH`
  apontando aos worktrees locais novos.
- O navegador usa as três APIs reais com SQLite, chaves e contas sintéticos:
  cria/edita/busca projeto com objetivo, refina textos/critérios de história,
  filtra por texto/status/prioridade, reinicia Backlog e reencontra dados;
  troca a senha, recebe saída local, senha antiga é recusada e nova autentica.
- Casos negativos incluem validação da política configurada, senha atual errada,
  conteúdo literal, falha de PATCH com rascunho preservado e logout com resposta
  de senha atrasada sem restaurar sessão, além das regressões anteriores.
- Revisão independente encontrou dois defeitos recuperáveis e os três cenários
  reproduzidos em RED passaram após correção: PATCH confirmado → recarga 401
  mantém aviso de sucesso; GET 503 ao atualizar preserva rascunhos de projeto/história.
- Seis capturas conferidas: Backlog, edição de projeto e troca de senha em desktop
  claro 1366×900 e celular escuro 390×844. Sem overflow horizontal; sistema visual
  navy/Inter preservado. DESIGN.md e seu sidecar não foram alterados.
- Detector executado uma vez: avisos de RGB/fontes correspondem aos tokens e à
  fonte Inter explicitamente fixados pelo sistema existente, sem mudança de paleta.

Verificação independente de persistência PostgreSQL dos backends: Identidade 156,
Projetos 114 e Backlog 149 aprovados sem skips. A busca Unicode depende de locale
compatível no PostgreSQL; Backlog foi validado com ICU/und. O navegador usa SQLite
temporário: sua evidência não substitui o teste PostgreSQL.

Sem publicação, push, merge, tags, grants remotos ou autoria/coautoria de IA.
Trocar senha encerra a sessão local; revogar JWT nos consumidores, MFA, equipes/RBAC
e recuperação por e-mail permanecem fora deste lote. Migração de Projetos e permissões
do banco devem ser executadas explicitamente pelo operador antes de publicar.
