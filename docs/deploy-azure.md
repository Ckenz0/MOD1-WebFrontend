# Frontend na Azure

O frontend usa Azure Static Web Apps Free, publicando somente `public/`. As APIs ficam em três Container Apps e o banco permanece no Neon. O provisionamento completo está no [guia de identidade](https://github.com/Ckenz0/MOD1-IdentityService/blob/main/docs/deploy-azure.md).

## Configurar

1. Integre a versão revisada com backlog/deploy em main. O workflow de publicação é manual e só executa nessa branch.
2. Crie os recursos pelo bootstrap Bicep do repositório de identidade e anote `frontendOrigin`. Essa origem precisa estar no CORS das três APIs.
3. Publique as imagens e aplique a fase de APIs. Anote as três URLs HTTPS estáveis.
4. No GitHub do frontend, Settings → Environments → demo, crie Variables `AUTH_API_URL`, `PROJECTS_API_URL` e `BACKLOG_API_URL`. Use somente as origens HTTPS, sem barra final, caminho ou credenciais.
5. No portal Azure, abra a Static Web App → Manage deployment token. Cadastre o token diretamente no Secret de Environment `AZURE_STATIC_WEB_APPS_API_TOKEN`.
6. Abra Actions → Publish frontend to Azure → Run workflow em main.

O workflow instala apenas ferramentas de desenvolvimento, executa a suíte de navegador, copia `public/` para um artefato e gera `config.js` com URLs públicas validadas. O upload pula o build, não inclui a raiz do repositório e não modifica o config local versionado. O token SWA não vai para o navegador. `staticwebapp.config.json` impede cache prolongado de config.js.

## Suspensão das APIs

Para URLs HTTPS, antes de operações a interface prepara o serviço e suas dependências por GET em /health/ready. O prazo total é de 90 segundos, com timeout de 30 segundos por tentativa e pausas de 2 segundos, tudo contado no prazo global. Há cache de prontidão por até 60 segundos, invalidado em indisponibilidade, erro de rede ou timeout. Não existe keep-alive periódico.

Durante a espera aparece “Preparando acesso…”. Cancelar ou sair impede o envio da operação pendente. O formulário preserva os dados se a preparação falhar. Cadastros, criação de projetos/histórias e alterações não são repetidos automaticamente após uma resposta incerta. Consulte a listagem antes de enviar uma gravação novamente. O modo local HTTP mantém o fluxo anterior.

## Validar e atualizar

Abra a URL pública de outra máquina e percorra cadastro → login → projetos → backlog. Confira teclado, mensagens de espera, duas contas isoladas, persistência e retomada após suspensão. Os testes de CI sem caminhos de backend têm skips explícitos de integração; isso não comprova integração com Neon/Azure. Para rodar o fluxo completo com APIs sintéticas locais, siga os caminhos de backend no README.

Cada publicação registra SHA e versão do frontend no resumo do workflow. Para rollback, publique novamente um commit revisado anterior pelo fluxo controlado; não edite arquivos diretamente no serviço. O Free tem limites de uso, e os recursos das APIs/registro/segredos/logs têm custos separados.
