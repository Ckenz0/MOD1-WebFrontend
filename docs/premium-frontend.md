# Refinamento visual do frontend

Registro local de 31/10/2026. O refinamento amplia a identidade existente do guia visual do módulo 6: azul-marinho, neutros claros/escuros, Inter e estados semânticos permanecem. Impeccable orientou a hierarquia, os componentes e a documentação; Taste Skill forneceu a direção editorial-greeting (seed 748895891), adaptada ao guia existente. A composição editorial aparece na apresentação e no ritmo da interface; a autoridade da marca continua sendo o guia do módulo 6.

## Implementação

`public/styles/premium.css`, carregado após tokens, estilos base e workspace, concentra o refinamento de apresentação. `public/index.html` organiza o contexto de entrada, os dados da conta, os atalhos e as preferências. O sistema efetivo está em [DESIGN.md](../DESIGN.md); a prévia de componentes acompanha o sidecar `.impeccable/design.json`.

- Entrada: contexto de acessos, projetos e backlog ao lado do formulário no desktop. Até 800px, o contexto é ocultado e o formulário fica centralizado.
- Conta: dados e ações principais ao lado dos atalhos de conta e organização; convite, perfil e preferências seguem em seções próprias. No celular, as áreas e os dados se empilham.
- Projetos e workspace: largura máxima de 1180px, separação entre conteúdo e formulário, filtros alinhados, tabelas com linhas mais legíveis e quadro com cartões delimitados. Tabelas densas rolam dentro da própria região, sem alargar a página.
- Estados: foco visível, rótulos persistentes, cores acompanhadas por texto/ícones e feedback de hover/pressionamento. A antiga animação de entrada do perfil foi suprimida. Transições de cor e borda duram 160ms apenas quando não há preferência por movimento reduzido.

A paleta e as fontes locais foram preservadas. O detalhe vermelho do identificador usa o token de marca existente; não altera o significado dos estados. Não foram adicionadas dependências de runtime, etapa de build ou mudanças em contratos HTTP e fronteiras entre apresentação, aplicação, domínio e infraestrutura.

## Evidência local

Na preparação da versão 0.5.0, em 01/11/2026, a suíte completa foi reexecutada:
**152 testes aprovados, sem skips, em 181,392 s**, com as três APIs reais locais,
`MAIL_PROVIDER=auto` e sem variáveis `RESEND_*` no processo. As evidências visuais
abaixo pertencem à revisão de 31/10/2026; não houve nova alteração de paleta ou UI
na preparação da versão. Detalhes em [verification.md](verification.md).

A suíte final concluiu **152 testes em 196,583s**, incluindo as duas regressões adicionadas nesta etapa, com as três APIs locais preparadas. Para reproduzir, configure `AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH` conforme a seção de testes do [README](../README.md), e execute na raiz do frontend:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

A conferência visual produziu **36 capturas** com dados sintéticos: seis telas, temas claro e escuro e larguras de 1440px, 768px e 390px. Essas capturas foram feitas no navegador real com Playwright. As verificações registraram ausência de overflow da página e de erros JavaScript, além da preservação da paleta.

O inspetor do Taste Skill registrou **0 FAIL e 0 WARN** nas seis telas e três larguras, com exceção declarada para a regra `assistant-palette`, necessária para preservar a marca. As medições do inspetor usaram snapshots do DOM visível com o CSS efetivo inline: a SPA mantém títulos ocultos no documento e a ferramenta pode escolher o primeiro `h1` ou medir antes do carregamento do CSS. Esse resultado se refere à inspeção dos snapshots; as 36 capturas reais com Playwright são uma evidência separada.

Um smoke test no servidor local `http://127.0.0.1:5173`, com APIs reais locais, percorreu login/conta, projetos, segurança/sessões e logout. Não alterou e-mail ou dados de produção. As evidências locais não comprovam disponibilidade de produção, deploy ou integração com os frontends dos outros grupos.

A revisão independente inspecionou as 36 capturas e encontrou dois problemas: filtros móveis excessivamente altos e foco com pouco contraste no workspace escuro. Ambos foram reproduzidos por novos testes antes da correção. O ajuste remove a base de altura dos campos no formulário móvel e usa a cor de texto do tema nos contornos de foco de botões e regiões roláveis. Os dois testes passaram após a correção.

O revisor conferiu as recapturas dos cenários afetados e reexecutou os testes específicos: ambos os achados foram classificados como resolvidos, com veredito `ship` no escopo desses dois itens. Foram produzidas quatro capturas adicionais de foco. Nenhuma publicação, merge ou deploy foi realizado.

## Revisão premium e barra da plataforma — 25/11/2026

Registro local, sem commit, publicação ou deploy. A paleta do guia do Módulo 6, Inter,
os temas, os contratos HTTP e as camadas foram preservados. Impeccable (modo Operate)
orientou estados, hierarquia e documentação; da Taste Skill foram usados apenas o
layer de microinterações (passo de 1px, seta de 3px, pressionamento a 0,985), a
entrada única do painel de boas-vindas e o `copy-lint` (0 FAIL, 0 WARN). As regras
da Taste Skill para sites institucionais (fotografias, uma seção por tela, cenas)
não se aplicam a uma interface de tarefa e não foram adotadas.

- Barra comum: `public/nav.js` copiado do arquivo combinado entre os grupos, com
  `MODULO_ATUAL = 1` e o endereço do Módulo 2 na lista `MODULOS`. O link "Ir para o
  conteúdo" é reposicionado antes da barra e fica acima dela ao receber foco.
- Moldura: barra navy, cabeçalho do módulo ("Projetos") em superfície com linha
  fina e conteúdo sobre o fundo neutro; cabeçalho, conteúdo e rodapé compartilham
  as mesmas bordas (1180px).
- Entrada: painel navy com o texto original de apresentação (título, frase e a
  lista Acessos/Projetos/Backlog com as descrições), ao lado do formulário;
  verificação de acesso em faixa abaixo. Até 960px, apenas formulário e
  verificação, centralizados. A prévia de backlog que ocupava o painel foi
  retirada a pedido do usuário.
- Conta: quatro cartões em grade de 12 colunas, atalhos com ícones e ID da conta
  em JetBrains Mono. Projetos e histórias: linhas clicáveis inteiras, data ou
  prioridade à direita e chevron; busca de projetos em grade.
- Estados: cor de foco por tema (`#2F3F7F` claro, `#A9B4E4` escuro), anel de 3px
  nos campos, contorno no botão primário do tema escuro, erros mantendo borda
  vermelha durante o foco.

Capturas com API simulada em
[screenshots/premium-2026-11-25](screenshots/premium-2026-11-25/): 1440, 1024,
820 e 390px, claro e escuro, incluindo foco do link de salto e validação. O
detector do Impeccable aponta Inter como fonte comum (mantida por exigência do
guia) e o divisor da verificação de acesso sem recuo lateral (padrão existente).

Suíte local em 25/11/2026 (`.venv` do worktree, Edge headless, sem APIs reais):
**217 testes aprovados, 16 skips** (os mesmos testes de API real da linha de base,
que tinha 212 aprovados). Os cinco testes novos em `tests/test_platform_nav_ui.py`
cobrem links e módulo ativo, módulo sem endereço desativado, link de salto como
primeira parada acima da barra, barra independente de `app.js` e rolagem própria
em 320px.

## Navegação reorganizada — 25/11/2026

A pedido do usuário, que achou a navegação confusa: menu lateral fixo e página
única do projeto, escolhidos entre as alternativas apresentadas. O detalhe do
projeto deixou de abrir abaixo da lista. Backlog, quadro, membros e planejamento
viraram abas da mesma página, e cada tela ganhou endereço próprio para o voltar do
navegador. Da Taste Skill vieram o item atual com `aria-current`, o indicador
deslizante das abas e a folha de menu de 56px no celular; do Impeccable (Operate),
o vocabulário único de componentes e a ausência de barra lateral em caixa
arredondada. Testes atualizados para os novos caminhos, mais dois testes novos
(voltar/avançar e menu no celular). Suíte local:
**219 testes aprovados**, com os 16 testes de API real pulados sem backends. Os
testes de API real também foram ajustados aos novos caminhos, mas não foram
executados. Capturas: `screenshots/premium-2026-11-25/`.

## Visual de gerenciador de issues — 25/11/2026

A pedido do usuário, com a skill `frontend-design`: estrutura e densidade próximas
do YouTrack, com a paleta navy do Guia mantida sem alteração (pedido explícito).
Saiu a barra de cabeçalho do módulo; o tema alterna por um botão redondo fixo no
canto inferior direito. O menu lateral ganhou marca, "Novo projeto" e opção de
recolher para ícones; o conteúdo ficou plano, com linhas finas e controles de
32–34px com mouse (44px em toque). Listas de projetos e histórias receberam
blocos de iniciais, selos de prioridade e estado; o quadro marca cada cartão com a
cor MoSCoW; visão geral e edição de história têm painel de campos à direita.
O texto "Alta · Concluído" continua no conteúdo da lista para leitores de tela e
testes, com o separador apenas oculto visualmente. Suíte local: **219 aprovados,
16 skips** de API real. As capturas da pasta foram substituídas pelo novo visual.
