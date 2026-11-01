# Fluxos da versão 0.5.0

Os quatro repositórios usam microsserviços com arquitetura interna multicamadas.
A versão 0.5.0 está preparada para publicação. Os fluxos abaixo têm evidência
local; SHA, versão e disponibilidade do ambiente publicado exigem conferência
separada na entrega.

## Onde testar

- Na conta: **Segurança e sessões**, **Equipes e alocação**, **Notificações** e,
  somente para administrador global, **Administração**.
- No login: **Esqueci minha senha**. Links de confirmação e recuperação abrem
  formulários próprios; o fragmento do endereço é removido antes do envio.
- No projeto: **Gerenciar projeto e planejamento** reúne orçamento, escopo,
  datas, etiquetas, stack, requisitos, ciclo de vida, equipes, papéis e histórico.
- No backlog: **Abrir quadro e itens** oferece histórias, épicos e tarefas,
  persona/ação/objetivo, MoSCoW, estimativas, responsável, bloqueios e dependências.
  O quadro aceita movimento entre situações e ordenação manual dentro da coluna;
  os botões Subir/Descer oferecem alternativa por teclado.
- Recomendações mostram justificativa, evidências, origem e decisão humana.
  Simulação é identificada. Requisição sem provedor configurado informa
  indisponibilidade, sem inventar uma recomendação.

## Sessão e indisponibilidade

Credenciais ficam somente na memória da aba. Recarregar exige novo login.
A sessão padrão tem 15 minutos de inatividade e máximo de 8 horas.
A renovação é compartilhada e sobrevive ao cancelamento de uma tela;
logout sempre impede uma resposta antiga de restaurar a sessão.
Falhas 503 preservam a tela/formulário para nova tentativa e não são tratadas
como credenciais inválidas. A API permanece autoridade para cada permissão.

MFA requer senha e um aplicativo TOTP. Guarde os códigos de recuperação exibidos
uma única vez. Alterar/redefinir senha encerra todas as sessões. A recuperação
continua exigindo o segundo fator quando estiver ativo.

## Limites explícitos

- Caixa postal local é um instrumento de teste restrito a administrador; não
  comprova entrega externa. O transporte real escolhido é o Resend, implementado
  no backend de Identidade. O teste real de transporte teve envio e recebimento
  confirmados para a conta do titular, único destino permitido pelo remetente de
  teste atual. Isso não comprova reset/confirmação reais de ponta a ponta nem
  envio para terceiros. Para ampliar os destinos, configure remetente/domínio
  autorizado no backend. Nenhuma chave é configurada no frontend.
- IA tem contrato/adaptador configurável e testes controlados. Qualidade e
  integração de um provedor/modelo real ainda precisam de validação.
- Uso de acesso desconhecido não é tratado como acesso não utilizado.
  Recomendações de revogação exigem uma janela completa observada (30 dias por
  padrão, configurável na solicitação), excluem proprietário/solicitante e
  precisam de aprovação humana. Uso recente invalida uma proposta antiga.
- Integração com revisão de código depende do contrato do outro grupo; o contrato
  local proposto não prova compatibilidade com esse produtor.
- O editor exige referências por identificador para épicos, responsáveis e
  dependências; o servidor valida escopo e permissões. Não inventa candidatos.
- Ordenação manual exige um conjunto canônico completo, com limite de 100 itens
  no controle da interface. Respostas parciais não viram reordenação destrutiva.

## Camadas no navegador

Apresentação: `app.js` compõe dependências; `workspace-controller.js`,
`workspace-view.js`, `public-auth-controller.js` e os controladores existentes
tratam DOM e interação. Aplicação: `account-application.js`,
`session-application.js`, `workspace-application.js` recebem adaptadores.
Domínio: `planning-domain.js`, contratos de conta/projeto/história e permissões.
Infraestrutura: clientes HTTP existentes e `platform-api.js`, sem DOM/storage.
`tests/test_layer_dependencies.py` verifica a direção das dependências.

## Verificação reproduzível

Execute `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
Para incluir integrações reais, configure `AUTH_BACKEND_PATH`,
`PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH` com os checkouts locais.
As fixtures inicializam bancos SQLite temporários, chaves próprias, portas
loopback e Edge headless, e encerram apenas os processos que criaram.
Não usam banco de produção. `test_advanced_real_api.py` cobre projeto/papéis/
história/quadro e MFA/caixa postal/confirmação/reset com serviços reais locais.
