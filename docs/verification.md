# Validação do frontend 0.2.0 — 11/10/2026

Windows, Python 3.12.15 e Playwright com Microsoft Edge. A suíte completa executou
**59 testes aprovados, sem skips**, com os três caminhos de backend configurados.
O backend do backlog executou 110 testes aprovados e um skip PostgreSQL local opt-in.

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

Capturas geradas pela fixture com dados sintéticos, APIs reais temporárias e viewport
desktop 1366×900 / celular 390×844. Não incluem tokens, credenciais ou contas reais.

![Backlog no desktop, tema claro](screenshots/backlog-desktop-light.png)

![Backlog no celular, tema escuro](screenshots/backlog-mobile-dark.png)

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
