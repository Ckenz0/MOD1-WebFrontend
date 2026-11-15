# Fechamento do Módulo 1 — 15/11/2026

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
