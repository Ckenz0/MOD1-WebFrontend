# Frontend de demonstração da autenticação

Data: 10/10/2026. Status: especificação aprovada pelo usuário; aguardando revisão
do plano de implementação.

## Objetivo e contexto

Criar um frontend separado para demonstrar a contribuição de Caue ao módulo 1:
entrar com uma conta existente e consultar a identidade autenticada pela API real.
O público são alunos, colegas e professor durante a apresentação do MVP.
Sucesso significa demonstrar esse fluxo completo, com erros compreensíveis e
identidade visual compatível com o módulo 6.

O repositório é `https://github.com/Ckenz0/MOD1-Frontend`. O portal central da
plataforma será desenvolvido pelo módulo 6; este frontend poderá continuar como
ferramenta de demonstração e fornecer padrões e telas para a integração futura.
O backend de autenticação permanece em `MOD1-EngenhariaSoftware`, atualmente na
worktree `feat/auth-mvp`.

Fonte visual: `C:\Users\cauek\Downloads\Guia_Visual_Modulo6.pdf`, versão 1.0,
outubro de 2026, sete páginas. O guia determina cores, fontes e tokens; não
determina framework nem fornece um logotipo oficial utilizável como arquivo.

## Abordagens consideradas

1. **HTML, CSS e JavaScript com módulos ES — recomendação.** Duas telas são
   suficientes para a demonstração. Não exige Node.js, instalação de dependências
   do produto nem build. Tokens e o cliente HTTP podem ser reaproveitados; levar
   as telas a um framework exigirá adaptar os componentes.
2. **React e Vite.** Facilita ampliar o frontend com componentes e rotas. Exige
   Node.js e uma cadeia de dependências; a stack do módulo 6 ainda não foi
   informada, portanto a compatibilidade futura não está garantida.
3. **Next.js.** Possibilita lógica intermediária no servidor, mas adiciona um
   runtime e responsabilidades de autenticação que este MVP não precisa.

A abordagem aprovada é HTML, CSS e JavaScript com módulos ES, conforme a
recomendação 1. As alternativas ficam registradas como contexto da decisão.

## Escopo e telas

### Login

- Identificação textual “Módulo 1 · Autenticação”, título “Entrar” e orientação
  de que a conta é fornecida pelo responsável do módulo.
- Campos de e-mail e senha, rótulos visíveis e autocomplete apropriado.
- Controle acessível para mostrar ou ocultar a senha.
- Ação principal “Entrar”; envio pelo botão ou pela tecla Enter.
- Estado de envio impede pedidos duplicados e informa “Entrando…”.
- Erros distinguem credenciais inválidas, indisponibilidade e falha de conexão.
- A senha nunca é aparada: espaços são parte da senha conforme o contrato da API.

### Usuário autenticado

- Saudação com o nome retornado pela API, e-mail e situação da conta em texto.
- Data de criação apresentada em português brasileiro.
- “Atualizar dados” consulta novamente `/auth/me` e trata erros de conexão.
- “Sair” encerra a sessão deste navegador e retorna ao login.
- Token expirado ou resposta 401 encerra a sessão com explicação ao usuário.
- A interface não exibe, copia nem baixa o JWT ou a senha.

Cadastro público, recuperação de senha, refresh token, login social, projetos,
equipes, backlog, papéis e dashboard geral ficam fora deste MVP. O backend atual
não oferece os três primeiros fluxos. Não haverá telas ou dados simulados no
produto para sugerir capacidades ausentes.

## Composição visual

Modo de uso: operar uma tarefa breve durante uma demonstração, em desktop ou
celular. A interface acompanha inicialmente a preferência de tema do sistema e
oferece um seletor claro/escuro.

No desktop, o cabeçalho traz identificação do módulo e seletor de tema. O
conteúdo tem largura confortável de leitura; o login aparece em um painel único,
com título, campos e botão em sequência vertical. Uma breve nota explica a
origem da conta. Na tela autenticada, nome e e-mail lideram o painel, seguidos
dos dados da conta e ações. Não há menu lateral sem destinos reais.

No celular, os mesmos elementos ficam em uma coluna, com margens de pelo menos
16 px, botões adequados ao toque e sem rolagem horizontal. A prioridade visual
continua sendo concluir a ação principal.

## Identidade visual obrigatória

Todos os componentes referenciam tokens CSS; valores hexadecimais ficam apenas
na definição dos tokens. Os nomes e valores do guia são preservados.

| Token | Claro | Escuro |
| --- | --- | --- |
| `--color-primary` | `#1E2A5A` | `#1E2A5A` |
| `--color-primary-hover` | `#2F3F7F` | `#2F3F7F` |
| `--color-brand-accent` | `#C8102E` | `#C8102E` |
| `--color-bg` | `#F6F7FA` | `#0F1220` |
| `--color-surface` | `#FFFFFF` | `#181C2E` |
| `--color-border` | `#E2E5EC` | `#2A2F45` |
| `--color-text` | `#1A1D29` | `#E8EAF2` |
| `--color-text-muted` | `#5B6275` | `#9AA0B4` |

Preservar também os tokens de prioridade: crítica `#DC2626`, alta `#EA580C`,
média `#B45309`, baixa `#64748B`, sucesso `#16A34A`; e os tokens de gráficos:
`#3B5BDB`, `#0EA5A4`, `#8B5CF6`, `#F59E0B`, `#EC4899`. Estes últimos ficam
disponíveis como parte do padrão compartilhado, sem acrescentar gráficos ao MVP.

Inter é a fonte da interface, com pesos 400, 500 e 600. JetBrains Mono é
reservada a código e identificadores técnicos; a tela principal não precisa
usá-la. A escala é 12, 14, 16, 20, 24 e 32 px. Nenhum texto fica abaixo de 12 px.
As fontes serão servidas localmente, preservando as respectivas licenças.

Azul-marinho é a cor de ação. Vermelho não será usado em botões; a cor crítica
fica reservada aos estados de erro pertinentes. Verde pode acompanhar um ícone
de conta ativa, mas o texto permanece na cor principal. Status sempre tem texto
ou ícone além da cor. Sem logotipo fornecido, usar identificação textual.

## Contrato de integração

O endereço da API fica em configuração pública separada, inicialmente
`http://127.0.0.1:8000`. Essa configuração não contém segredos nem permite mudar
o endereço por um parâmetro arbitrário recebido na URL.

1. `POST /auth/token`, com `application/x-www-form-urlencoded`, campos
   `username` e `password`.
2. Consumir `access_token`, `token_type` e `expires_in` da resposta.
3. `GET /auth/me`, com `Authorization: Bearer <token>`.
4. Mostrar a página autenticada somente depois de obter uma identidade válida.

O cliente HTTP controla timeout e cancelamento. Respostas precisam ser
validadas antes de atualizar a interface. Uma resposta atrasada não pode
restabelecer uma sessão encerrada. Dados retornados pela API entram no DOM
como texto, sem interpretar HTML.

401 no login resulta em “E-mail ou senha inválidos”. 401 em `/auth/me` exige
novo login. 422 informa que os dados enviados precisam de revisão. 503,
timeout e falha de rede informam indisponibilidade com possibilidade de tentar
novamente; nenhum conteúdo bruto de exceções do servidor é exibido.

## Sessão e configuração local

JWT e identidade ficam apenas em memória. Recarregar ou fechar a página exige
novo login; não haverá checkbox “Lembrar de mim”. A preferência de tema pode
ser persistida em armazenamento local, separadamente da sessão.

`expires_in` define o limite local de duração; o frontend verifica esse limite
antes de ações e após retomar uma aba. O servidor continua sendo a autoridade
para validar o acesso. Sair limpa o estado local, cancela requisições pendentes
e não promete revogação do token no servidor.

O frontend será servido em `http://127.0.0.1:5173`, por servidor HTTP local,
sem abrir arquivos diretamente com `file://`. A API deverá receber
`CORS_ORIGINS=["http://127.0.0.1:5173"]` no ambiente. O README explicará como
configurar a API, criar uma conta pelo CLI e iniciar os dois serviços.

O repositório será preparado para commit e push; publicação de uma aplicação
em serviço de hospedagem não integra esta etapa. Em uma hospedagem futura,
frontend e API precisam de URLs acessíveis e configuração HTTPS/CORS adequada.

## Organização proposta

- `public/index.html`: estrutura semântica e regiões das duas telas.
- `public/config.js`: endereço público da API.
- `public/styles/tokens.css`: identidade compartilhada do guia.
- `public/styles/app.css`: composição, componentes, responsividade e temas.
- `public/scripts/api.js`: cliente HTTP e tradução de respostas.
- `public/scripts/session.js`: estado em memória e expiração.
- `public/scripts/app.js`: apresentação e eventos da interface.
- `public/assets/fonts/`: fontes locais e licenças.
- `tests/`: verificações relevantes do fluxo de autenticação.
- `README.md`: execução, integração e limites do MVP.
- `PRODUCT.md` e `DESIGN.md`: contexto do produto e decisões visuais.

## Acessibilidade e validação

Rótulos associados aos campos, foco visível, navegação completa por teclado,
mensagens de erro anunciadas, estados de carregamento identificados e respeito
a `prefers-reduced-motion`. Conferir contraste nos dois temas, especialmente
foco e controles sobre superfícies escuras.

Validar no navegador o login válido, credenciais incorretas, API indisponível,
sessão expirada, atualização de dados e sair. Verificar que tokens não entram
em URLs, logs ou armazenamento persistente e que respostas atrasadas não
restauram uma sessão encerrada.

Executar o fluxo com a API real e uma conta de teste, incluindo CORS. Capturar
desktop e celular, nos temas claro e escuro, e verificar teclado e ausência de
rolagem horizontal. Registrar qualquer limitação do ambiente de testes.

Os testes anteriores do backend aprovaram 93 casos e pularam seis ligados ao
PostgreSQL. Isso fornece contexto, mas não substitui os testes deste frontend.
A demonstração temporária com SQLite precisa ser identificada como tal; não
comprova PostgreSQL, Docker ou deploy.

## Próxima etapa

A especificação foi aprovada. Revisar o plano de implementação elaborado
conforme `superpowers:writing-plans` e selecionar sua forma de execução. Só
então iniciar o código do frontend.
