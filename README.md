# Frontend

O frontend segue arquitetura multicamadas com apresentação, casos de uso,
domínio e clientes HTTP separados. Componentes e fluxos reais estão em
[Arquitetura](docs/architecture.md).

## Recursos da versão 0.5.0

Sessões persistentes no backend, renovação, bloqueio por tentativas, recuperação,
confirmação de e-mail, MFA e administração global. Na conta, abra **Segurança e
sessões**, **Equipes e alocação** ou **Notificações**. Administradores também têm
**Administração**, inclusive caixa postal de desenvolvimento quando habilitada.

No projeto, **Gerenciar projeto e planejamento** reúne contexto/orçamento/datas,
ciclo de vida, equipes, papéis personalizados, concessões por papel e histórico.
O quadro oferece histórias/épicos/tarefas, campos orientados, MoSCoW, esforço,
responsáveis, bloqueios, dependências e ordenação por arraste ou teclado.

Veja [guia dos fluxos](docs/local-user-stories.md),
[situação das US](docs/backlog-status.md) e [validação](docs/verification.md).
IA real e o contrato externo de revisão ainda precisam de validação;
simulação é identificada. O transporte Resend recebeu teste real de envio e
recebimento, limitado à conta do titular pelo remetente de teste atual. Isso
não comprova recuperação/confirmação ponta a ponta por e-mail externo.

## Colaboração e perfil

Na conta, edite resumo, senioridade, competências/domínio e disponibilidade.
Compartilhe seu ID para receber um convite; cole o código e aceite ou recuse.
Em **Membros e papéis**, gestores convidam e editam os papéis fixos e a expiração
do vínculo, ou removem integrantes. O proprietário permanece protegido.
Desenvolvedor pode consultar o backlog e alterar somente status; PO/PM também
refinam/criam. O servidor autoriza cada operação; 403 não encerra a sessão.
Códigos e JWT ficam somente em memória e são limpos ao sair.

Atualizar acessos/histórias consulta as permissões atuais e remove controles
revogados. Se o perfil não carregar, a edição permanece desativada e o botão
**Tentar carregar perfil novamente** permite recuperar os dados antes de editar.

Use as versões dos três serviços verificadas na entrega, com as migrações e grants
explícitos dos respectivos guias; a combinação histórica de colaboração era
Identidade 0.3.0, Projetos 0.4.0 e Backlog 0.3.0. O convite vale até sete dias,
limitado também pela expiração do vínculo. O Resend fica somente no backend de
Identidade; envio a outros destinatários exige remetente/domínio autorizado.

Criar conta, entrar, organizar projetos e acompanhar histórias priorizadas até a
conclusão continua sendo o fluxo principal. Versão SemVer `0.5.0` em
[VERSION](VERSION), preparada para publicação; alterações em
[CHANGELOG.md](CHANGELOG.md). A versão no arquivo não comprova deploy.

HTML/CSS/JavaScript modular, sem dependências de produto ou build. Identidade visual
do módulo 6, fontes locais e temas claro/escuro. O portal definitivo será o do módulo 6;
esta interface demonstra o recorte local e permite reaproveitar clientes/tokens visuais.

## Refinamento visual

Entrada com contexto no desktop, conta com dados e atalhos separados e workspace
com filtros, tabelas e quadro refinados. A identidade do módulo 6, as cores, Inter,
as fontes locais e as camadas existentes foram preservadas, sem novas dependências
ou build. Veja [decisões e evidências](docs/premium-frontend.md) e o
[sistema visual](DESIGN.md). A revisão independente das 36 capturas foi concluída;
os dois achados tiveram correção e recaptura aprovadas. A evidência visual local
não comprova disponibilidade da versão em produção.

## Executar

Para publicação no Azure Static Web Apps e retomada das APIs suspensas, siga o [guia de deploy](docs/deploy-azure.md). A configuração pública de produção é gerada no artefato, preservando os endereços locais no código fonte.

URLs e contrato para os colegas estão no [guia de integração entre módulos](docs/integracao-outros-modulos.md).

Prepare cada backend pelo README correspondente:

| API | Repositório | Porta |
| --- | --- | --- |
| Identidade | [MOD1-IdentityService](https://github.com/Ckenz0/MOD1-IdentityService) | 8000 |
| Projetos | [MOD1-ProjectsServices](https://github.com/briankfreire/MOD1-ProjectsServices) | 8001 |
| Backlog | [MOD1-BacklogService](https://github.com/igorcpds/MOD1-BacklogService) | 8002 |

Identidade precisa de banco/chave RSA preparados; projetos/backlog precisam de seus
schemas/tabelas e migrações explícitas. Configure `AUTH_API_BASE_URL` em Projetos
e Backlog, `PROJECTS_API_BASE_URL` no Backlog e `BACKLOG_API_BASE_URL` em Projetos.
Preserve verificação online habilitada. Configure CORS nas três APIs para `http://127.0.0.1:5173` e inicie
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
   sem convite não pode acessar o projeto nem suas histórias.
7. Teste teclado, temas e celular; saia e confira novamente o acesso.

O valor é tornar necessidades, critérios de entrega, prioridades e progresso visíveis,
preservando dados e acesso por conta. [Resultados e capturas](docs/verification.md).

JWT fica somente em memória; recarregar a página exige login. Só o tema pode persistir.
Logout revoga a sessão no servidor e limpa imediatamente a aba. Troca/reset de
senha revogam todas as sessões; consumidores consultam o estado online.
Cadastro permite login imediato, com confirmação de e-mail disponível separadamente.
Há recuperação de senha, equipes, RBAC personalizado, tarefas e estimativas.
Sprints e exclusão individual de histórias não fazem parte desta entrega.

## Gerenciamento básico

- Na conta, **Alterar senha** solicita a senha atual, a nova e a confirmação.
  A interface mostra a política configurada pela Identidade e encerra a sessão
  após salvar. A política atual também revoga as credenciais nos consumidores.
- Em Projetos, registre o objetivo, use **Editar projeto** para refinar nome,
  descrição e objetivo, ou busque pelo nome. A edição pode ser cancelada.
- No Backlog, refine título, descrição e critérios de aceite; busque por título,
  descrição ou ID e combine filtros de status/prioridade. Descarte restaura o
  último valor salvo. Falhas de rede preservam o rascunho para nova tentativa.

A base histórica 0.3.0 usava Identidade 0.2.0, Projetos 0.3.0 e Backlog 0.2.0.
Em banco de Projetos anterior, executar a migração administrativa explícita
conforme o README desse backend. Nenhuma tela executa migração ou concede acesso.
Status/etiquetas, equipes, papéis personalizados, recuperação, MFA e MoSCoW foram
acrescentados desde essa base. IA real e compatibilidade com o módulo externo
de revisão continuam pendentes, conforme a matriz de US.

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
$env:MAIL_PROVIDER = 'auto'
Get-ChildItem Env: | Where-Object { $_.Name -like 'RESEND*' } | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
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
export MAIL_PROVIDER=auto
# Execute sem variáveis RESEND_* e sem credenciais de e-mail reais no processo.
.venv/bin/python -m unittest discover -s tests -v
```

Fixtures usam SQLite, chaves/contas temporárias e portas livres; não acessam Neon.
Sem os caminhos, integrações correspondentes são puladas explicitamente.
Isso não comprova PostgreSQL, Docker ou deploy.

Sistema visual: [DESIGN.md](DESIGN.md); [fontes e licenças](docs/font-sources.md).
[Conferência dos requisitos](docs/requirements-review.md).
