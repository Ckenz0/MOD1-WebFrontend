# MOD1 Frontend

Frontend de demonstração da autenticação: login, identidade do usuário, atualização
dos dados e saída. HTML, CSS e JavaScript modular; sem dependências de produto ou build.
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

No diretório do backend, crie a conta por CLI, digitando a senha de forma oculta:

```powershell
uv run --locked python -m mod1_auth.cli create-user --email seu-email@example.com --name "Seu nome"
uv run --locked python -m uvicorn mod1_auth.main:create_app --factory --host 127.0.0.1 --port 8000
```

Contas são administradas no backend; não existe cadastro ou recuperação de senha nesta interface.

## Demonstração

1. Entre com o e-mail e a senha da conta criada. Espaços na senha são preservados.
2. Confira nome, e-mail, situação da conta e data de criação.
3. Use **Atualizar dados** para consultar novamente a identidade na API.
4. Teste credenciais incorretas e os temas claro/escuro.
5. Use **Sair** para encerrar a sessão deste navegador.

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
