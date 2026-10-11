# MOD1 Frontend

## Projetos do módulo de Brian

Após entrar, escolha **Meus projetos** para criar, listar e consultar os seus projetos.
O responsável é definido pela API usando a identidade autenticada. Outra conta não
consegue consultar um projeto seu, mesmo conhecendo seu UUID.

Em `public/config.js`, configure `PROJECTS_API_BASE_URL` com a URL pública da API de
projetos (`http://127.0.0.1:8001` na demonstração local). Mantenha `API_BASE_URL`
apontando para autenticação (`http://127.0.0.1:8000`). Não coloque chaves ou senhas
na configuração pública. As duas APIs precisam permitir a origem do frontend.

No Windows com ambientes temporários bloqueados, os testes podem usar:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r tests/requirements.txt
$env:AUTH_BACKEND_PATH = 'C:\CAMINHO\MOD1-EngenhariaSoftware'
$env:PROJECTS_BACKEND_PATH = 'C:\CAMINHO\projeto_eng_soft'
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Frontend de demonstração da autenticação: cadastro, login, identidade do usuário,
consulta dos dados, verificação de acesso protegido e saída. HTML, CSS e JavaScript modular; sem dependências de produto ou build.
Identidade visual compartilhada com o módulo 6, com fontes locais e temas claro/escuro.

## Executar

Requer um servidor HTTP estático; com Python instalado, execute na raiz do projeto:

```powershell
python -m http.server 5173 --bind 127.0.0.1 --directory public
```

Abra **http://127.0.0.1:5173**. `file://` não suporta este fluxo de módulos e API.

Prepare e inicie o [backend de autenticação](https://github.com/Ckenz0/MOD1-EngenhariaSoftware)
seguindo seu README. O backend precisa do banco e da chave RSA previamente inicializados.
Em seu ambiente, configure:

```dotenv
CORS_ORIGINS=["http://127.0.0.1:5173"]
```

O endereço da API está em `public/config.js`, inicialmente `http://127.0.0.1:8000`.
Essa configuração é pública e deve conter apenas o endereço do serviço. Para outra
origem de frontend, ajuste o CORS no backend; `localhost` e `127.0.0.1` são origens distintas.

No diretório do backend, inicie a API:

```powershell
uv run --locked python -m uvicorn mod1_auth.main:create_app --factory --host 127.0.0.1 --port 8000
```

Use **Criar conta** para cadastrar nome, e-mail e senha (12 a 128 caracteres), confirmando a senha no formulário. O cadastro permite login imediato; não verifica a posse do e-mail nem oferece recuperação de senha. Criação administrativa e desativação/reativação continuam disponíveis na CLI do backend. Este frontend exige a versão do backend que fornece `POST /auth/register`.

## Demonstração

1. Use **Verificar acesso** antes de entrar: a API deve recusar a consulta protegida.
2. Crie uma conta e teste as mensagens junto aos campos. Espaços na senha são preservados.
3. Entre e confira nome, e-mail, situação da conta e data de criação.
4. Use **Verificar acesso** após o login: a API deve permitir a consulta.
5. Use **Atualizar dados**, teste credenciais incorretas e os temas claro/escuro.
6. Use **Sair** e verifique o acesso novamente: a consulta sem sessão deve ser recusada.

O resultado de acesso vem de `/auth/me`; erro de rede ou serviço indisponível aparece como impossibilidade de verificar, não como bloqueio. Cadastro repetido não altera senha ou situação de uma conta existente e recebe a mesma confirmação geral.

O JWT fica apenas em memória. Recarregar/fechar a página exige novo login; somente
a preferência de tema pode persistir. Sair não revoga tokens no servidor. Expiração
ou 401 retorna ao login; uma falha de rede ao atualizar conserva os dados anteriores
enquanto a sessão estiver válida.

## Testes

Ferramentas de desenvolvimento: [uv](https://docs.astral.sh/uv/), Python 3.12 e
Microsoft Edge instalado. Playwright usa o navegador existente; as dependências
de teste estão fixadas e não são enviadas ao frontend.

```powershell
uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
```

Para executar também a integração real, aponte ao checkout do backend com `.venv`
e pacote preparados. Neste ambiente, a implementação está na worktree `feat/auth-mvp`:

```powershell
$env:AUTH_BACKEND_PATH = 'C:\Users\cauek\.codex\worktrees\2ecd\MOD1-EngenhariaSoftware'
uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
```

Os testes criam banco SQLite, chave e conta sintéticos temporários, iniciam a API
real e verificam HTTP/CORS no navegador. Não usam dados, contas ou bancos de produção.
Sem `AUTH_BACKEND_PATH`, três testes são pulados: integração real fica pendente.
SQLite não comprova PostgreSQL, Docker ou deploy.

## Integração futura

O portal central pertence ao módulo 6. Tokens CSS, cliente HTTP e fluxo de sessão
podem ser reaproveitados. Projetos, equipes e backlog pertencem a outros serviços.
Para hospedagem futura, API e frontend precisam ser acessíveis entre si, com HTTPS
e CORS configurados para a origem publicada.

Sistema visual: [DESIGN.md](DESIGN.md). Fontes e licenças:
[docs/font-sources.md](docs/font-sources.md). Cobertura, resultados e capturas:
[docs/verification.md](docs/verification.md).
Conferência dos requisitos, dependências e pendências antes de publicar:
[docs/requirements-review.md](docs/requirements-review.md).
