# Entrega do Módulo 1 — integração final de 16/11/2026

O escopo implementado cobre **100 das 100 US distintas**. A US096 foi concluída
com a API real do Módulo 4 e a regra de início de trabalho aprovada pelo usuário;
US101 continua duplicada de US009. A [matriz](backlog-status.md) preserva os
estados iniciais históricos e aponta as evidências de cada capacidade.

Versões desta entrega: Backlog0.6.0, Frontend0.7.0. Identidade0.5.0 e
Projetos0.6.0 permanecem compatíveis. Consulte `/release.json` e OpenAPI para
versão/SHA efetivamente implantados; a versão do repositório não prova deploy.

## Aceite do Módulo 4 — 16/11/2026

A regra aprovada foi implementada e validada: uma análise válida inicia somente
itens a fazer; trabalho em andamento/concluído permanece como está e conclusão
é manual. Os registros são restritos ao projeto/item, persistidos antes do POST
e recuperáveis após reinício. Repetir o UUID com conteúdo igual não chama o
provedor; conteúdo diferente conflita. Falhas, versão ou acesso alterados não
concluem itens nem provocam retry automático. O ingresso legado de eventos
permanece desabilitado e separado da API síncrona real do Módulo 4.

- Backlog: **491 testes aprovados**, incluindo migração aditiva e concorrência
  em PostgreSQL descartável local. Ruff, formato e mypy passaram.
- Frontend: **187 testes executados, 185 aprovados e 2 opt-ins ignorados**,
  usando as três APIs temporárias. Os ignorados são Resend/Gemini reais, já
  validados na entrega anterior e não repetidos por esta alteração.
- O aceite controlado de navegador exercitou sucesso, Basic dedicado, texto
  seguro, replay, reinício e resposta incerta sem alteração do item. A revisão
  independente encontrou e acompanhou as correções de recuperação após 409,
  avisos entre páginas e indisponibilidade JWKS; não restaram achados materiais.
- Uma rodada de aceite com o serviço M4 real passou: análise estática de código
  fictício, **HTTP201**, um POST nessa rodada, transição `todo→in_progress`,
  persistência após reinício e replay sem segundo POST. IA não foi solicitada;
  não se infere que testes do código foram executados. O resultado informou
  `testes_executados=false`. Não houve comentário em PR nem criação/alteração de
  entidade de negócio de produção por esse teste.
- O segredo Basic é exclusivo da API do Backlog. O patch de publicação preserva
  CORS, JWT, Gemini e M6 e não repassa essa senha ao worker de notificações.
  A tabela própria foi preparada de forma aditiva, após backup validado,
  com SELECT/INSERT/UPDATE para runtime e sem acesso a outros schemas.

O histórico global do provedor não é disponibilizado aos usuários do módulo.
Respostas e Markdown são exibidos como texto; novo envio após resultado
desconhecido exige ação explícita e indicação de possível duplicidade.

## Histórico — fechamento de 15/11/2026

O escopo implementado cobre **99 das 100 US distintas**. A única história
dependente de outro grupo é US-096: contrato real do produtor de revisão de
código. O ingresso proposto continua desabilitado, sem contrato inventado.
US-101 repete US-009; os exemplos de checkout/campanha não são requisitos deste
módulo. A rastreabilidade está em [backlog-status.md](backlog-status.md).

## Correções finais do frontend 0.6.1

- Leitores consultam equipes sem solicitar alocações restritas a gestores.
- Gestão de equipes e de membros usam permissões independentes. Abas, geração
  e aprovação de IA respeitam os pré-requisitos de cada operação, incluindo
  leitura do contexto e projeto arquivado. Leitura/rejeição permanecem disponíveis.
- Sair do workspace do projeto volta à lista de projetos com foco no título;
  sair das ferramentas da conta volta ao perfil.

As regressões de permissões e navegação foram reproduzidas antes da correção e
passaram depois. A revisão independente reexecutou 9 testes de permissões e
2 de navegação, sem achados críticos/importantes remanescentes.

## Aceite das integrações

- [Resend](email-acceptance.md): duas mensagens reais, entrega reportada pelo
  provedor e links de confirmação/reset exercitados pelo navegador. Uso único,
  senha anterior recusada, sessões revogadas nas três APIs e MFA preservado.
- [Gemini](local-ai-testing.md): sete tipos reais, contexto autorizado,
  persistência após reinício, rejeição, aprovação explícita/idempotente de
  papéis/backlog e expiração por contexto alterado. Equipes retornou vazio válido;
  seu caminho positivo usa os testes controlados do backend.
- Módulo 6: eventos mapeados de Backlog e Projetos ativos em produção; um aviso
  real com escopo de projeto aceito com HTTP 200. Não houve inspeção visual da
  Central nem criação artificial de evento de negócio no banco de produção.
- Módulos 2 e 7: origens informadas liberadas nas três APIs. CORS recíproco nas
  APIs de outros grupos continua responsabilidade deles.

Os testes novos usam contas, bancos SQLite e chaves temporários. Nenhuma conta
ou dado de negócio de produção foi alterado. Testes destrutivos PostgreSQL
usaram apenas banco local descartável na publicação anterior.

Versões dos backends: Identidade 0.5.0, Projetos 0.6.0, Backlog 0.5.0. Chaves
Gemini/Resend/M6 ficam somente no servidor. A versão e o SHA efetivamente
implantados do frontend podem ser conferidos em `/release.json`; a versão do
repositório sozinha não comprova deploy.

Comandos, resultados e histórico: [verification.md](verification.md).
