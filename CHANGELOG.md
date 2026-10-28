# Changelog

## Colaboração e perfil (0.4.0) — candidato local, 2026-10-28

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
