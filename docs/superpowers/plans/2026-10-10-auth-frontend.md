# Authentication Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Entregar um frontend de demonstração que autentica contas reais e
consulta sua identidade, seguindo a identidade visual do módulo 6.

**Architecture:** Aplicação estática com HTML semântico, CSS por tokens e módulos
JavaScript ES. Cliente HTTP, estado da sessão e apresentação têm responsabilidades
separadas. O backend existente permanece como autoridade de autenticação.

**Tech Stack:** HTML, CSS, JavaScript e servidor HTTP estático; Python 3.12+,
unittest e Playwright apenas para testes; Microsoft Edge já instalado neste host.

**Spec:** `docs/superpowers/specs/2026-10-10-auth-frontend-design.md`.

## Global Constraints

- Produto sem framework, dependências JavaScript ou etapa de build.
- Login, usuário autenticado, atualização de dados, sair e seleção claro/escuro.
- Sem cadastro público, recuperação de senha, refresh token, projetos ou backlog.
- API pública configurada em `public/config.js`: `http://127.0.0.1:8000`.
- Frontend local: `http://127.0.0.1:5173`; CORS da API inclui exatamente essa origem.
- Senha literal, inclusive espaços; JWT e identidade apenas em memória.
- Entrar na tela autenticada somente após sucesso em `/auth/me`.
- Tokens CSS com os nomes e valores exatos da especificação/PDF.
- Ações: `#1E2A5A`, hover `#2F3F7F`; nenhuma ação primária vermelha.
- Inter 400/500/600; JetBrains Mono somente para código; fontes e licenças locais.
- Escala de texto: 12, 14, 16, 20, 24 e 32 px; mínimo 12 px.
- Português brasileiro, foco visível, teclado, mensagens anunciadas e movimento reduzido.
- Exibir dados da API como texto, nunca como HTML; não exibir ou registrar JWT/senha.
- Logout local não promete revogação do token no servidor.
- Registrar separadamente browser, API real, PostgreSQL, Docker e deploy.
- Publicar commits neste repositório; hospedagem do aplicativo fica fora desta etapa.

## Review Focus

1. Logout enquanto `/auth/me` está pendente: resposta tardia nunca restaura sessão.
2. Aba suspensa até depois da expiração: ao retornar, exige login antes de qualquer ação.
3. Resposta 200 com JSON inválido ou campos ausentes: erro compreensível, sem sessão válida.
4. Nome/e-mail longos ou conteúdo semelhante a HTML: texto literal, sem overflow ou execução.
5. Armazenamento de tema indisponível: a aplicação e a troca de tema continuam funcionando.

## Estrutura e limites

Produto: `public/index.html`, `public/config.js`, `public/styles/tokens.css`,
`public/styles/app.css`, `public/scripts/api.js`, `public/scripts/session.js`,
`public/scripts/app.js` e `public/assets/fonts/`.

Testes: `tests/browser_support.py` para servidor HTTP temporário e navegador;
`tests/test_api_session.py` para módulos; `tests/test_ui.py` para comportamento;
`tests/test_real_api.py` para a integração real opt-in. Fixar dependências de teste
resolvidas em `tests/requirements.txt`; nenhum pacote é enviado ao navegador.

Documentação: `README.md`, `PRODUCT.md`, `DESIGN.md` e
`docs/verification.md`. Manter evidências temporárias e dados/chaves fora do Git.

### Task 1: Cliente HTTP e sessão em memória

**Files:** criar `public/config.js`, `public/scripts/api.js`,
`public/scripts/session.js`, `tests/browser_support.py`,
`tests/test_api_session.py`, `tests/requirements.txt` e `.gitignore`.

**Interfaces:**
- `createApiClient({ baseUrl, fetchImpl = fetch, timeoutMs = 10000 })` produz
  `login(email, password, { signal } = {}) -> Promise<TokenResponse>` e
  `getMe(token, { signal } = {}) -> Promise<UserIdentity>`.
- `ApiError` possui `kind`: `credentials`, `unauthorized`, `validation`,
  `unavailable`, `network`, `timeout`, `invalid-response` ou `cancelled`.
- `TokenResponse`: `access_token: string`, `token_type: "bearer"`,
  `expires_in: number` positivo e finito.
- `UserIdentity`: `id`, `email`, `display_name`, `created_at` como strings
  validadas e `is_active: boolean`; não converter entrada malformada em sucesso.
- `createSession({ now = Date.now } = {})` produz `start(tokenResponse)`,
  `isActive() -> boolean`, `getToken() -> string | null` e `clear()`.
- Configuração exporta `API_BASE_URL` sem segredos.
- O suporte de testes usa Playwright síncrono, Edge headless e servidor estático
  em porta local livre; fecha navegador, servidor e diretórios temporários.
- `BrowserCase(unittest.TestCase)` fornece `self.page`, `self.base_url`,
  `self.token_response` sintético e `self.identity` válida. Cada teste tem contexto
  limpo. Para testar apenas módulos, o servidor oferece `/__test__/`, página vazia
  de mesma origem. `RealApiCase` será definida na Task 3 para integração sem mocks.

- [x] Criar infraestrutura de teste e fixar as dependências resolvidas. Testes
  podem carregar módulos por uma página mínima servida pelo próprio suporte.
- [x] Escrever `test_literal_password_and_bearer_header`, capturando a chamada
  enviada e verificando `username`, senha `"  password12345  "`,
  `application/x-www-form-urlencoded` e `Authorization: Bearer synthetic-token`.
- [x] Escrever `test_invalid_responses_fail_closed` para JSON malformado,
  `expires_in` ausente/zero/string e identidade incompleta; nenhum gera sucesso.
- [x] Escrever `test_session_expires_and_never_persists`, com relógio injetado:
  token expira no limite, `clear()` remove acesso e local/sessionStorage ficam vazios.

```python
def test_session_expires_and_never_persists(self):
    self.page.goto(self.base_url + "/__test__/")
    result = self.page.evaluate("""async () => {
      const { createSession } = await import('/scripts/session.js');
      let now = 1000;
      const session = createSession({ now: () => now });
      session.start({access_token:'synthetic-token', token_type:'bearer', expires_in:30});
      const before = session.getToken();
      now = 31000;
      const expired = session.getToken();
      session.clear();
      return {before, expired, active:session.isActive(),
              stored:localStorage.length + sessionStorage.length};
    }""")
    self.assertEqual(result, {"before":"synthetic-token", "expired":None,
                             "active":False, "stored":0})
```

- [x] Escrever casos distintos para 401, 422, 503, rede, timeout e cancelamento;
  erros nunca incluem senha, JWT ou conteúdo bruto de exceção remota.
- [x] Executar os testes antes dos módulos; confirmar falha pela ausência do produto.
- [x] Implementar as interfaces, validação de resposta e AbortController combinado
  com timeout; sessões expiradas não retornam token utilizável.
- [x] Executar novamente o conjunto alvo; confirmar zero falhas e fechar recursos.
- [x] Commit: `feat: add authentication client and in-memory session`.

Comando: `uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -p test_api_session.py -v`.

### Task 2: Telas e identidade visual

**Files:** criar `public/index.html`, `public/styles/tokens.css`,
`public/styles/app.css`, `public/scripts/app.js`, fontes/licenças em
`public/assets/fonts/`, `tests/test_ui.py` e contexto em `PRODUCT.md`.

**Interfaces:**
- Consome `API_BASE_URL`, cliente HTTP e sessão da Task 1.
- `app.js` associa eventos ao DOM e controla as telas sem expor JWT em atributos.
- `applyTheme(theme: "light" | "dark")` define `data-theme` na raiz; persistência
  usa apenas a chave `mod1-theme`, com leitura/escrita protegidas contra erro.
- Login usa rótulos “E-mail” e “Senha”, botão “Entrar”, controle “Mostrar senha”.
- Perfil apresenta nome/e-mail reais e ações “Atualizar dados” e “Sair”.
- Regiões de mensagem identificam carregamento e erros para leitores de tela.

- [x] Escrever testes de login válido: resposta de token sozinha não mostra perfil;
  perfil só aparece após `/auth/me`; segredo nunca aparece no DOM nem em storage.

```python
def test_login_displays_identity_without_exposing_token(self):
    self.page.route("**/auth/token", lambda route: route.fulfill(json=self.token_response))
    self.page.route("**/auth/me", lambda route: route.fulfill(json=self.identity))
    self.page.goto(self.base_url)
    self.page.get_by_label("E-mail", exact=True).fill(self.identity["email"])
    self.page.get_by_label("Senha", exact=True).fill("  password12345  ")
    self.page.get_by_role("button", name="Entrar", exact=True).click()
    expect(self.page.get_by_text(self.identity["email"], exact=True)).to_be_visible()
    self.assertNotIn(self.token_response["access_token"], self.page.content())
    self.assertEqual(self.page.evaluate("sessionStorage.length"), 0)
```

- [x] Escrever `test_login_errors_and_duplicate_submit`: 401 exibe
  “E-mail ou senha inválidos”; envio duplo gera só um pedido; 503/rede permitem retry.
- [x] Escrever `test_logout_ignores_late_identity`: atrasar atualização do perfil,
  clicar “Sair”, liberar resposta e confirmar que a tela de login permanece.
- [x] Escrever `test_expiration_after_hidden_tab`: avançar relógio enquanto aba
  está inativa; retomar e confirmar login antes de nova chamada autenticada.
- [x] Escrever `test_untrusted_long_identity_is_plain_text`: usar nome contendo
  `<img src=x onerror=alert(1)>`, e-mail longo e confirmar texto literal/sem overflow.
- [x] Escrever `test_theme_when_storage_is_blocked`: fazer Storage lançar erro;
  login e seleção de tema ainda funcionam. Incluir reload: sessão se perde, tema permanece
  apenas quando o armazenamento está disponível.
- [x] Executar o conjunto alvo e confirmar falhas pela ausência das telas.
- [x] Ler `impeccable` craft-floor antes de editar a UI; registrar composição
  aprovada e fontes oficiais com licenças, sem acrescentar capacidades ao MVP.
- [x] Implementar HTML/CSS/tokens com identificação textual e dois temas;
  mensagens específicas, foco visível, teclado, campos e controles acessíveis.
- [x] Implementar eventos, senha literal, abort de pedidos, proteção contra
  resposta atrasada e retorno ao login em expiração/401. Falha de rede ao atualizar
  perfil preserva dados anteriores e informa o erro enquanto a sessão for válida.
- [x] Limpar a senha após login bem-sucedido ou saída; mostrar/ocultar preserva o
  valor e altera estado acessível. Enter envia pelo mesmo fluxo do botão.
- [x] Executar o conjunto alvo; confirmar zero falhas.
- [x] Commit: `feat: add branded login and authenticated user interface`.

Comando: `uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -p test_ui.py -v`.

### Task 3: Integração com a API real e CORS

**Files:** criar `tests/test_real_api.py`; ampliar somente o suporte de testes
necessário em `tests/browser_support.py`; criar instruções iniciais em `README.md`.

**Interfaces:**
- Teste opt-in lê `AUTH_BACKEND_PATH`, diretório do backend com pacote e ambiente
  já preparados. Ausência resulta em skip explícito, não prova de integração.
- O fixture usa o Python desse backend para criar chave RSA, SQLite temporário e
  conta sintética por `UserService`, e iniciar `python -m uvicorn` em porta livre.
- `JWT_ISSUER` de teste e `CORS_ORIGINS` correspondente à origem exata do servidor
  estático são definidos apenas no ambiente do subprocesso de teste.
- O servidor estático de teste fornece configuração apontando ao fixture sem
  modificar `public/config.js` rastreado. Requisições da API real não são mockadas.
- `RealApiCase(BrowserCase)` fornece o backend preparado por teste; a conta
  sintética usa `conta@example.com`, nome `Conta de teste` e senha literal
  `"  password12345  "`. Não usar dados de pessoas reais nos fixtures.

- [x] Escrever `test_real_login_identity_update_and_logout`, usando navegador real
  e API real; verificar nome/e-mail, atualização, credenciais incorretas e saída.

```python
def test_real_login_identity_update_and_logout(self):
    self.page.goto(self.base_url)
    self.page.get_by_label("E-mail", exact=True).fill("conta@example.com")
    self.page.get_by_label("Senha", exact=True).fill("  password12345  ")
    self.page.get_by_role("button", name="Entrar", exact=True).click()
    expect(self.page.get_by_text("conta@example.com", exact=True)).to_be_visible()
    self.page.get_by_role("button", name="Atualizar dados", exact=True).click()
    expect(self.page.get_by_text("conta@example.com", exact=True)).to_be_visible()
    self.page.get_by_role("button", name="Sair", exact=True).click()
    expect(self.page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
```

- [x] Escrever `test_disallowed_origin_cannot_complete_login`, alterando apenas
  CORS no fixture; a UI não autentica e explica falha de conexão.
- [x] Escrever `test_real_inactive_user_rejected`: desativar conta pelo caso de uso
  administrativo no fixture; novo login é recusado e `/auth/me` deixa de autenticar.
- [x] Executar testes com backend configurado; qualquer falha de produto precisa
  ser investigada antes de ajustes. Skip não é considerado aprovação.
- [x] Ajustar integração ou fixture somente conforme falhas observadas; rodar
  novamente os casos afetados até passarem.
- [x] Confirmar limpeza de banco/chave e encerramento dos subprocessos. Credenciais
  são sintéticas; fixtures nunca usam bancos, chaves ou contas reais do usuário.
- [x] Documentar execução dos serviços, CORS, CLI de contas e limites do logout.
- [x] Commit: `test: verify browser authentication against the real API`.

Comandos PowerShell, após preparar o ambiente existente do backend:

```powershell
$env:AUTH_BACKEND_PATH = 'C:\Users\cauek\.codex\worktrees\2ecd\MOD1-EngenhariaSoftware'
uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -p test_real_api.py -v
```

Este teste comprova integração HTTP/CORS com SQLite temporário, não PostgreSQL.

### Task 4: Verificação visual e entrega

**Files:** finalizar `README.md`, criar `DESIGN.md`, `.impeccable/design.json`
conforme o fluxo de documentação do Impeccable e `docs/verification.md`.
Modificar produto somente para defeitos efetivamente encontrados.

**Interfaces:** produto das Tasks 1–3; guia visual e especificação aprovada.

- [x] Capturar uma rodada conjunta: desktop 1440×1000 e celular 390×844, ambos
  nos temas claro/escuro, cobrindo login e perfil. Inspecionar foco por teclado,
  mensagens anunciadas, contraste, fontes locais, texto longo e overflow.
- [x] Corrigir em um único lote os defeitos encontrados; confirmar somente as
  capturas/verificações afetadas, com no máximo mais uma rodada visual.
- [x] Documentar o sistema construído em DESIGN.md e seu sidecar de tokens;
  registrar fontes, licenças, layouts e estados reais, sem inventar logotipo.
- [x] Finalizar README com `python -m http.server 5173 --bind 127.0.0.1 --directory public`,
  configuração pública da API, CORS e roteiro de demonstração login → perfil → sair.
- [x] Escrever matriz de cobertura em `docs/verification.md`: testes de navegador,
  integração HTTP real, CLI/JWKS em suíte do backend, PostgreSQL/Docker/deploy pendentes.
- [x] Rodar uma suíte final completa e `git diff --check`; ler saída integral e
  registrar aprovados, falhas e skips. Não repetir após sucesso sem novas mudanças.
- [x] Revisar toda a entrega conforme o método de execução selecionado, corrigir
  achados relevantes e revalidar apenas o que mudou.
- [x] Commit: `docs: document frontend usage and verification`.
- [x] Enviar a branch ao GitHub e entregar arquivos, evidências e instruções.
  Não presumir autorização para merge; disponibilizar o resultado para revisão.

Comandos finais:

```powershell
uv run --no-project --with-requirements tests/requirements.txt python -m unittest discover -s tests -v
git diff --check
```

Se a política do Windows bloquear a ferramenta de automação, registrar o bloqueio,
prosseguir com verificações permitidas e deixar explícito que browser QA ficou
pendente. Não modificar políticas de segurança para executar testes.

## Referências de teste

- [Playwright: Microsoft Edge instalado e canal msedge](https://playwright.dev/python/docs/browsers#google-chrome--microsoft-edge).
- [Playwright: integração com unittest](https://playwright.dev/python/docs/test-runners#use-unittest).

## Handoff

Recomendação: execução **nativa**, pelo agente atual, por serem quatro tarefas
sequenciais e pequenas com interfaces compartilhadas. A alternativa é execução
com subagentes e revisão independente por tarefa. A execução começa após o
usuário revisar este plano e escolher o método, conforme `superpowers:writing-plans`.
