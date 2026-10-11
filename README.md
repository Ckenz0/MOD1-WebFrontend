# Frontend

MVP integrado: criar conta, entrar, organizar projetos e acompanhar histórias
priorizadas até a conclusão. Versão candidata SemVer `0.2.0` em [VERSION](VERSION);
alterações em [CHANGELOG.md](CHANGELOG.md).

HTML/CSS/JavaScript modular, sem dependências de produto ou build. Identidade visual
do módulo 6, fontes locais e temas claro/escuro. O portal definitivo será o do módulo 6;
esta interface demonstra o recorte local e permite reaproveitar clientes/tokens visuais.

## Executar

Prepare cada backend pelo README correspondente:

| API | Repositório | Porta |
| --- | --- | --- |
| Identidade | [MOD1-IdentityService](https://github.com/Ckenz0/MOD1-IdentityService) | 8000 |
| Projetos | [MOD1-ProjectsServices](https://github.com/briankfreire/MOD1-ProjectsServices) | 8001 |
| Backlog | [MOD1-BacklogService](https://github.com/igorcpds/MOD1-BacklogService) | 8002 |

Identidade precisa de banco/chave RSA preparados; projetos/backlog precisam de seus
schemas/tabelas. Configure CORS nas três APIs para `http://127.0.0.1:5173` e inicie
os serviços em terminais próprios. Use as instruções de instalação de cada repositório.

Na raiz do frontend, com Python instalado:

```powershell
python -m http.server 5173 --bind 127.0.0.1 --directory public
```

Abra **http://127.0.0.1:5173**. URLs públicas estão em `public/config.js`:
`API_BASE_URL`, `PROJECTS_API_BASE_URL`, `BACKLOG_API_BASE_URL`. Coloque somente URLs,
sem chaves, DSNs ou senhas. `localhost` e `127.0.0.1` são origens distintas.
Para hospedagem, use HTTPS e CORS correspondente à origem publicada.

## Demonstrar

1. Verifique o acesso antes de entrar: a consulta protegida deve ser recusada.
2. Crie conta e entre; confira validação dos campos e dados da identidade.
3. Abra **Meus projetos**, crie um projeto e escolha **Backlog** no detalhe.
4. Crie histórias com descrição/critérios de aceite e prioridades alta/média/baixa.
5. Abra uma história, altere a prioridade e avance de **A fazer** para **Em andamento**
   e **Concluído**. A lista reflete a prioridade e o progresso salvos.
6. Reinicie o backlog, atualize as histórias e confira persistência. Outra conta
   não pode acessar o projeto nem suas histórias.
7. Teste teclado, temas e celular; saia e confira novamente o acesso.

O valor é tornar necessidades, critérios de entrega, prioridades e progresso visíveis,
preservando dados e acesso por conta. [Resultados e capturas](docs/verification.md).

JWT fica somente em memória; recarregar a página exige login. Só o tema pode persistir.
Logout não revoga JWT no servidor. Cadastro permite login imediato, sem confirmação
de posse do e-mail ou recuperação de senha. Projetos têm proprietário único; não há
equipes/RBAC. Backlog não inclui tarefas, sprints, estimativas, exclusão ou edição do texto.

Falha de rede não equivale a acesso negado. Se POST/PATCH tiver sucesso e a recarga
falhar, a tela confirma a gravação e orienta atualizar a lista. Timeout não confirma
gravação; não há reenvio automático. 401/expiração retorna ao login.

## Testes

Requer Python 3.12, uv e Microsoft Edge instalado. Na raiz do frontend:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r tests/requirements.txt
$env:AUTH_BACKEND_PATH = 'C:\CAMINHO\MOD1-IdentityService'
$env:PROJECTS_BACKEND_PATH = 'C:\CAMINHO\MOD1-ProjectsServices'
$env:BACKLOG_BACKEND_PATH = 'C:\CAMINHO\MOD1-BacklogService'
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Os caminhos representam seus checkouts; cada backend deve ter `.venv` e pacote
preparados. Em Unix:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r tests/requirements.txt
export AUTH_BACKEND_PATH=/CAMINHO/MOD1-IdentityService
export PROJECTS_BACKEND_PATH=/CAMINHO/MOD1-ProjectsServices
export BACKLOG_BACKEND_PATH=/CAMINHO/MOD1-BacklogService
.venv/bin/python -m unittest discover -s tests -v
```

Fixtures usam SQLite, chaves/contas temporárias e portas livres; não acessam Neon.
Sem os caminhos, integrações correspondentes são puladas explicitamente (seis testes
quando nenhum backend está configurado). Isso não comprova PostgreSQL, Docker ou deploy.

Sistema visual: [DESIGN.md](DESIGN.md); [fontes e licenças](docs/font-sources.md).
[Conferência dos requisitos](docs/requirements-review.md).
