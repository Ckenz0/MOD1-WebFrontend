# Changelog

## 0.10.0 — navegação e refinamento visual, 25/11/2026

- Barra comum dos módulos (`public/nav.js`, combinada entre os grupos) no topo de
  todas as telas, com o Módulo 1 ativo e o endereço do Módulo 2 (GitHub Sync).
  O link "Ir para o conteúdo" continua sendo a primeira parada do teclado.
- Cabeçalho do módulo renomeado para **Projetos** (Módulo 1 · Contas, projetos e
  backlog), com ícone de pasta, favicon e título da aba alinhados.
- Entrada com painel navy e o texto original de apresentação ao lado do formulário;
  conta em cartões; listas de projetos e histórias com linha clicável inteira;
  busca de projetos em grade; verificação de acesso em faixa única.
- Estados refinados: foco com cor de foco por tema, anel nos campos, botões com
  passo de 1px e seta, sublinhado desenhado nas ações de texto. Paleta, Inter e
  contratos HTTP preservados; sem dependências ou build.
- Navegação reorganizada: menu lateral fixo após o login (folha de tela cheia no
  celular), com Início, Projetos, Equipes e alocação, Notificações, Segurança e
  sessões, Administração para administradores e um único Sair.
- Página única do projeto com trilha e abas, que substitui o detalhe abaixo da
  lista e os botões "Gerenciar projeto e planejamento", "Abrir quadro e itens" e
  "Voltar…". A antiga aba Contexto passa a se chamar Planejamento; criar um
  projeto abre a página dele.
- Endereço por tela (`#/inicio`, `#/projetos/<id>/<aba>`…): voltar e avançar do
  navegador funcionam; links públicos de e-mail e recuperação continuam valendo.
- Visual de gerenciador de issues (inspirado no YouTrack) na mesma paleta navy:
  menu lateral cinza com "Novo projeto" e opção de recolher para ícones, conteúdo
  plano com linhas finas, controles compactos com mouse, listas com selos de
  prioridade e estado, cartões do quadro com faixa MoSCoW e painel de campos na
  visão geral e na edição de história.
- Sem barra de cabeçalho do módulo; o tema alterna por um botão redondo fixo no
  canto inferior direito.
- O indicador das abas cobre exatamente o texto da aba ativa.
- "Confira seu acesso" aparece no login e, depois de entrar, somente em Segurança
  e sessões.
- Conteúdo legível dentro dos campos: seleção múltipla mostra todas as opções
  (antes ficava cortada em 34px), campo de arquivo estilizado, competências do
  perfil em uma linha, tabelas sem palavras partidas e coluna de ações alinhada.
- Endereço inicial restaurado após concluir o login; telas de confirmação e
  recuperação são limpas ao voltar à navegação autenticada.
- Acesso revogado ou projeto indisponível apaga detalhes e ações em cache e
  retorna à lista atualizada, preservando a sessão nos erros 403/404.
- Menu móvel contém o foco e bloqueia os controles encobertos; fechar, sair ou
  ampliar a tela restaura a interação com o conteúdo.

## 0.9.0 — artefatos no projeto, 24/11/2026

- Aba Artefatos com vínculo explícito ao projeto M3, filtros, versões e download.
- Edição do vínculo somente com permissão; consultas pelo backend e apenas GET
  ao provedor, sem token na URL e sem disparar análise de IA.
- Cancelamento de respostas antigas e ações acessíveis em celular.
- [Uso e limites](docs/module3-artifacts.md).

## 0.8.0 — curadoria no projeto, 18/11/2026

- Aba Curadoria com feed de tecnologia e pesquisa explícita de artigos,
  disponível para quem tem `project:read`, inclusive em projetos arquivados.
- Recomendações de treinamento com tópicos podem abrir uma pergunta editável.
- Resultados com links HTTP(S) protegidos, estados de carregamento e falha,
  indicação de fontes indisponíveis e limite de artigos por resposta.
- O cliente cancela solicitações ao sair da seção. Depois de uma falha de
  pesquisa, o usuário decide se envia a pergunta novamente.

## 0.7.0 — integração com Code Review, 16/11/2026

- Revisões de código por item, com PR ou arquivos Python, arquitetura e IA
  opcional; credenciais do Módulo 4 permanecem somente no backend.
- Análise válida inicia apenas itens “A fazer”; a conclusão continua manual.
- Relatórios, achados e estado da IA exibidos em texto seguro, com histórico
  restrito ao item/projeto e persistência após reinício.
- Pedidos idempotentes, recuperação após conflito e proteção contra reenvio de
  resultados incertos, inclusive ao navegar entre páginas do histórico.
- Aceite com três APIs temporárias/provedor controlado e cenário real do
  Módulo 4; matriz de US atualizada para a regra aprovada.

## 0.6.1 — fechamento de 15/11/2026

- Equipes consultáveis por leitores sem buscar alocações restritas; controles,
  tipos e aprovações de IA respeitam as permissões atuais de cada operação.
- Retorno do workspace de projeto à lista de projetos, preservando o retorno
  ao perfil nas ferramentas da conta.
- Aceite opt-in de e-mail com Resend real e Gemini real usando APIs/bancos
  temporários e navegador; regressões de uso único dos links e revogação.
- Matriz de US, integração, versões e evidências atualizadas; contrato externo
  de revisão de código continua como dependência explícita.

## 0.6.0 — 2026-11-15

- Recomendações identificam Google Gemini e exibem papéis e ações em português, preservando as cores e os temas existentes.
- Análises sem sugestões podem ser dispensadas e não oferecem aprovação; decisões com sugestões continuam exigindo ação humana explícita.
- Interface explica o envio do contexto autorizado ao provedor; texto do modelo continua sendo exibido como texto seguro.
- Contrato, mock e simulação Postman locais, com smoke HTTP dos três adaptadores, sem dependência de chave real ou banco remoto.
- Integração Gemini implementada nas APIs e verificada com a chave real pelos adaptadores; a interface mantém revisão humana das sugestões.

## 0.5.0 — 2026-11-01, preparada para publicação

- Arquitetura multicamadas: apresentação/DOM, aplicação, domínio e infraestrutura HTTP separados, com testes das fronteiras e casos de uso sem DOM/rede.
- Contas com sessões persistidas no backend, renovação, bloqueio por tentativas, revogação, recuperação, confirmação de e-mail, MFA e administração global.
- Equipes, convites, alocação, notificações, metadados/planejamento de projetos, papéis personalizados, concessões e histórico.
- Histórias orientadas, épicos/tarefas, MoSCoW, esforço, responsáveis, bloqueios, dependências e quadro com arraste/ordenação por teclado.
- Refinamento premium de entrada, conta, projetos e workspace; cores atuais do módulo 6, fontes locais e temas preservados. Revisão independente de 36 capturas, com os dois achados corrigidos e recapturados.
- Guia de integração para os outros módulos e documentação atualizada, distinguindo limites atuais dos registros históricos do MVP.
- Resend implementado na infraestrutura de Identidade e envio/recebimento real de transporte verificado. O remetente de teste limita destinatários à conta do titular; isso não comprova fluxo externo real de reset ou confirmação.
- Pendências explícitas: provedor/modelo real de IA e contrato efetivo com o produtor externo de revisão de código. Simulação permanece identificada.

A versão SemVer é independente das APIs. A preparação e os testes locais não
comprovam publicação, tag ou deploy; confirme SHA, versão e ambiente no fechamento
da entrega.

## Histórico anterior

## Colaboração e perfil (0.4.0) — candidato local, 2026-10-28

- Atualização/reabertura de membros e atualização do backlog consultam as permissões atuais; perda de acesso remove controles anteriores.
- Falha inicial do perfil mantém campos e Salvar desativados e oferece retentativa de carregamento.
- Regressões para rebaixamento de papel, remoção/404, retentativa do perfil e descarte de respostas antigas com consulta de permissões.
- Perfil privado com resumo, senioridade, competências/domínio e disponibilidade.
- Convite por código: gerar para UUID/papéis, aceitar/recusar na conta sem URL ou armazenamento persistente.
- Painel de membros, múltiplos papéis, expiração do vínculo e remoção com confirmação; dono protegido.
- Ações coerentes com permissões: Desenvolvedor altera somente status; PO/PM refinam/criam.
- 403 mantém sessão; logout/troca de contexto descarta respostas antigas e códigos.
- Testes com duas contas e três APIs, incluindo promoção a PO e remoção; desktop/celular nos dois temas.

Versão candidata: `0.4.0`, definida em `VERSION`. O frontend possui versão SemVer
independente dos serviços. A versão será publicada após revisão e integração;
esta mudança não cria tag ou release.

## Unreleased

### Gerenciamento básico (0.3.0)

- Troca autenticada de senha, política configurável exibida e saída local após sucesso.
- Objetivo e edição de projetos; busca por nome com paginação filtrada.
- Refinamento de título/descrição/critérios de histórias, busca e filtros combinados.
- Cancelamento, validação, proteção contra duplo envio e preservação de rascunhos.
- Confirmação de gravação quando recarga falha; respostas antigas descartadas após logout.
- Regressões de navegador e fluxo completo com as três APIs reais e dados temporários.
- Evolução MINOR sem alteração da identidade visual ou dependências do produto.

### Deploy Azure

- Publicação manual no Static Web Apps com configuração HTTPS gerada somente no artefato público.
- Preparação limitada das APIs suspensas, cancelamento e preservação das gravações sem reenvio automático.
- Guia de configuração Azure integrado aos serviços e Neon.

### Backlog (0.2.0)

- Histórias por projeto com título, descrição e critérios de aceite.
- Prioridades alta/média/baixa e progresso a fazer/em andamento/concluído.
- Paginação, validação dos campos, confirmação de gravação e recuperação de falhas.
- Integração com três APIs, isolamento de contas e persistência após reinício.
- Confirmação de criação/atualização preservada se a recarga encerrar a sessão.
- Espaços Unicode no título alinhados ao backend, com leitura de histórias antigas.
- Concordância das mensagens de validação e indisponibilidade corrigida.

### Added

- Cadastro público, login, identidade, verificação de acesso e logout.
- Criação, listagem paginada e consulta dos projetos do usuário autenticado.
- Validação junto aos campos, teclado, temas e identidade visual do módulo 6.
- Sessão em memória e descarte de respostas antigas após logout/troca de conta.
- Testes de navegador e integração real com autenticação/projetos.
- Roteiro, capturas e conferência dos requisitos do MVP.

### Fixed

- Limpeza dos bancos temporários aguarda a liberação dos arquivos no Windows.
