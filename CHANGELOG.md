# Changelog

Versão candidata: `0.2.0`, definida em `VERSION`. O frontend possui versão SemVer
independente dos serviços. A versão será publicada após revisão e integração;
esta mudança não cria tag ou release.

## Unreleased

### Backlog (0.2.0)

- Histórias por projeto com título, descrição e critérios de aceite.
- Prioridades alta/média/baixa e progresso a fazer/em andamento/concluído.
- Paginação, validação dos campos, confirmação de gravação e recuperação de falhas.
- Integração com três APIs, isolamento de contas e persistência após reinício.

### Added

- Cadastro público, login, identidade, verificação de acesso e logout.
- Criação, listagem paginada e consulta dos projetos do usuário autenticado.
- Validação junto aos campos, teclado, temas e identidade visual do módulo 6.
- Sessão em memória e descarte de respostas antigas após logout/troca de conta.
- Testes de navegador e integração real com autenticação/projetos.
- Roteiro, capturas e conferência dos requisitos do MVP.

### Fixed

- Limpeza dos bancos temporários aguarda a liberação dos arquivos no Windows.
