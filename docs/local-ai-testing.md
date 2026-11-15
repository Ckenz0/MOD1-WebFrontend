# Testes da integração Gemini

## Fechamento de 15/11/2026

Gemini real está configurado nas três APIs publicadas. O teste opt-in
`tests/test_gemini_real_api.py` também passou com Edge, APIs reais locais e dados
sintéticos: sete chamadas ao Google retornaram HTTP 200 e geraram propostas
persistidas. Nenhum perfil sem consentimento ou credencial foi enviado no corpo.
As propostas/decisões continuaram iguais após reiniciar as APIs.

| Tipo | Sugestões na última rodada | Decisão exercitada |
| --- | ---: | --- |
| `roles` | 1 | Aprovação explícita, concessão e evento/outbox conferidos, repetição idempotente |
| `teams` | 0 | Análise vazia dispensada; nenhuma equipe criada |
| `skills_map` | 3 | Rejeição sem alterar dados de negócio |
| `training` | 2 | Rejeição sem alterar dados de negócio |
| `access_revocation` | 1 | Contexto alterado: aprovação recusada com 409, proposta expirada sem revogar acesso |
| `initial_backlog` | 2 | Aprovação explícita criou itens; repetição não duplicou itens |
| `access_anomalies` | 0 | Análise vazia dispensada; nenhuma conta alterada |

O resultado vazio de equipes é válido e não comprova aprovação de equipe com
Gemini nessa rodada. O caminho positivo de criação/vínculo/notificação de equipe
continua coberto pelos testes controlados do serviço de Projetos. Não há uma
pendência de chave/provedor; a utilidade das sugestões deve ser avaliada no
contexto real de cada projeto. A reprodução opt-in está na seção
[Aceitação local com Gemini real](#aceitação-local-com-gemini-real).

## Histórico — preparação de 05/11/2026

Estado de 05/11/2026: integração implementada em branches locais, sem push,
tag, release ou deploy. Candidatos SemVer: Identidade 0.5.0, Projetos 0.6.0,
Backlog 0.5.0 e Frontend 0.6.0. As versões publicadas não foram atualizadas.

As três APIs selecionam Gemini explicitamente; o provedor HTTP genérico continua
sendo o padrão. O navegador chama somente as APIs do módulo. A chave fica no
ambiente do backend e nunca deve entrar em `public/`, `config.js` ou commits.

## O que foi verificado

As suítes completas passaram: Identidade 336 testes, Projetos 271, Backlog 349 e
Frontend 159. Foram ignorados 8 testes PostgreSQL em Identidade, 10 PostgreSQL e
1 dependente do caminho de outro serviço em Projetos e 2 PostgreSQL em Backlog.
Os testes de PostgreSQL exigem banco local descartável configurado; nenhum banco
remoto foi usado. Esses números não incluem uma chamada real ao Google.

- Testes dos adaptadores e serviços cobrem sete tipos de análise, validação de
  referências e evidências, contexto autorizado, aprovação humana e falhas sem
  gravar recomendações ou alterar permissões/backlog.
- O smoke com os adaptadores reais e a simulação HTTP Postman passou em 22 casos:
  sete tipos com resultado vazio e, para cada backend, quota 429,
  indisponibilidade 503, timeout, JSON inválido e truncamento. O log da simulação
  confirmou as 22 chamadas esperadas, sem repetição observada.
- A interface cobre aprovação explícita, análise vazia dispensável, falha do
  provedor e texto malicioso exibido sem executar HTML. Cores e temas existentes
  foram preservados; desktop e celular foram inspecionados nos dois temas.
- A revisão independente final dos quatro repositórios foi concluída. O achado
  de campos fora do schema Gemini no Backlog foi corrigido e passou por uma
  rerevisão com 92 testes. O contrato do provedor HTTP genérico foi preservado.
- A demonstração local usa SQLite e contas fictícias separados. Seis gerações
  HTTP retornaram 201; aprovar essas análises vazias retornou 409 sem efeitos.
  Revogação por inatividade retornou 409 porque o ambiente novo ainda não tem
  uma janela completa de atividade observada. Não se fabrica esse histórico.

Esses resultados comprovam o comportamento local contra respostas controladas.
**Não comprovam disponibilidade, quota, gratuidade ou qualidade do Gemini real.**
A rodada de 05/11 não incluiu chamadas reais. A verificação posterior abaixo
registra os testes autorizados com chave privada e dados fictícios.

## Verificação real dos adaptadores — 14/11/2026

Os sete tipos foram executados nos adaptadores reais contra o endpoint oficial
`https://generativelanguage.googleapis.com/v1beta`, com `gemini-3.5-flash-lite`:

| API | Tipos | Resultado com dados sintéticos |
| --- | --- | --- |
| Identidade | `access_anomalies` | HTTP 200, sem sugestões ou evidências inventadas |
| Projetos | `roles`, `access_revocation`, `teams`, `skills_map`, `training` | HTTP 200 nos cinco, propostas vazias sem candidatos elegíveis e evidências autorizadas |
| Backlog | `initial_backlog` | HTTP 200, uma história válida e uma evidência do projeto |

`roles` recebeu primeiro HTTP 503 do Google e passou em uma repetição manual
limitada. Não foram adicionados retries automáticos ou fallback. A simulação HTTP
foi repetida após a correção: 22 casos passaram e o log confirmou 22 requisições.

O schema completo de Identidade retornava HTTP 400; remover apenas `maxItems` dos
arrays enviados produziu HTTP 200. Os adaptadores agora copiam o schema sem esse
limite para geração e continuam validando todos os limites nos modelos locais.
Regressões cobrem arrays aninhados, schema original preservado e rejeição acima
do máximo. A documentação Google também descreve a complexidade adicionada por
[limites de arrays](https://ai.google.dev/gemini-api/docs/structured-output#simplifying-complex-schemas).

Essas chamadas não abriram bancos nem persistiram propostas ou alteraram
permissões. Elas não validam todos os fluxos HTTP/UI, a qualidade geral ou todas
as US de IA. Os processos da demonstração simulada e a configuração Azure foram
preservados; o runtime exige configuração explícita conforme descrito abaixo.
Nenhuma chave ou evidência privada faz parte desta documentação.

As suítes completas dos backends passaram após a correção: Identidade 343
aprovados/8 ignorados, Projetos 287/11 e Backlog 354/2, totalizando **984
aprovados e 21 ignorados**. Os ignorados exigem PostgreSQL local descartável ou
o caminho de outro serviço, ausentes nessa execução; nenhum banco remoto foi
usado. Ruff, verificação de formato e mypy passaram nos três backends. Os três
testes do harness de smoke também passaram. Permanece o aviso já existente de
depreciação Starlette/httpx no TestClient de Backlog. A suíte UI completa não foi
repetida nesta correção, que não alterou código da interface.

## Repetir a simulação HTTP

Instale Postman CLI 1.70 ou superior e prepare o `.venv` de cada API. Na raiz do
frontend, execute em um terminal:

```powershell
postman simulation run postman/simulations/gemini-local/gemini-local.sim.yaml --port 4010 --no-history --output ndjson
```

Em outro terminal, substitua os caminhos pelos seus checkouts:

```powershell
python scripts/smoke_gemini.py --identity-path C:/dev/Identity --projects-path C:/dev/Projects --backlog-path C:/dev/Backlog --base-url http://127.0.0.1:4010/v1beta
```

O harness usa apenas a chave fictícia `test-only-key`, não lê `.env`, não abre
bancos e executa cada adaptador em processo separado. Os modelos `mock-*` existem
somente no fixture local; não devem ser usados na API Google. Confirme 22 eventos
`request` no log para avaliar repetição. Outros acessos à demonstração adicionam
eventos; use um processo de simulação separado para uma contagem isolada.

O mock foi gerado de um contrato parcial baseado na referência oficial e depois
adaptado para validar requests e injetar falhas determinísticas. Não foi obtido
de um workspace publicado pelo Google; a busca de proprietário estava indisponível.
O contrato não pretende descrever a API Gemini inteira. Veja
[contrato](../postman/contracts/gemini-generate-content.yaml) e
[contexto da simulação](../postman/simulations/gemini-local/gemini-local.context.yaml).

## Habilitar o provedor real nas APIs

Crie uma chave no [Google AI Studio](https://aistudio.google.com/api-keys) e
configure as variáveis no ambiente de **cada backend**, usando seu arquivo local
ignorado ou o inicializador local. Um `.env` na raiz de outro checkout não é
carregado automaticamente pelo serviço.

```dotenv
AI_PROVIDER=gemini
AI_SIMULATED=false
GEMINI_API_KEY=<sua-chave-local>
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_OUTPUT_TOKENS=4096
```

Reinicie somente os processos locais e gere uma recomendação usando um projeto
fictício. Confira `provider=gemini`, o modelo configurado, `simulated=false`,
justificativa e referências. Esses metadados identificam o adaptador; um endereço
loopback ainda pode apontar para o mock. Confirme o endereço oficial para validar
a chamada real. Revise a proposta antes de aprovar: a geração não altera acessos
nem cria itens automaticamente. Propostas sem sugestões podem ser dispensadas;
a API rejeita sua aprovação com 409.

A disponibilidade e os limites dependem do projeto Google, não da assinatura do
aplicativo Gemini. Confira [modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
e [preços e faixa gratuita](https://ai.google.dev/gemini-api/docs/pricing) antes do
teste. Use dados fictícios na faixa gratuita, conforme os termos do provedor.
Não habilite faturamento como parte deste procedimento local.

Documentação específica de cada API: `docs/gemini.md` no respectivo repositório.
O contrato externo com o módulo de revisão de código e a configuração do envio
transacional são etapas independentes desta integração.


## Aceitação local com Gemini real

`tests/test_gemini_real_api.py` executa o frontend no Edge headless, três APIs reais
em portas locais livres e o endpoint oficial HTTPS do Google Gemini. Não usa
respostas simuladas nem substitui a resposta do provedor. O teste é opt-in e pode
consumir a cota da chave configurada. A descoberta normal da suíte o ignora e não
lê arquivos de credenciais.

### Preparação e execução

Prepare os quatro ambientes virtuais com as dependências de teste de cada
repositório. O frontend precisa de Playwright e do Microsoft Edge instalado,
conforme os demais testes de navegador. As APIs precisam estar instaladas nos
respectivos ambientes virtuais; não é necessário iniciar serviços manualmente.

No PowerShell, a partir da raiz do frontend:

```powershell
$env:AUTH_BACKEND_PATH = 'C:/caminho/Identidade'
$env:PROJECTS_BACKEND_PATH = 'C:/caminho/Projetos'
$env:BACKLOG_BACKEND_PATH = 'C:/caminho/Backlog'
$env:GEMINI_ACCEPTANCE_ENV_FILE = 'C:/caminho/privado/.env'
$env:GEMINI_ACCEPTANCE_MODEL = 'gemini-3.5-flash-lite'
$env:RUN_REAL_GEMINI_ACCEPTANCE = '1'
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_gemini_real_api.py -v
```

O arquivo privado deve conter `GEMINI_API_KEY=...` e permanecer ignorado pelo Git.
Também é possível fornecer `GEMINI_API_KEY` pelo ambiente; nesse caso nenhum
arquivo é lido. A chave nunca deve ser incluída no comando, em capturas ou em
relatórios. Depois da execução, remova `RUN_REAL_GEMINI_ACCEPTANCE` do ambiente
para que a suíte normal continue sem chamadas externas.

### Garantias verificadas

- Os sete tipos são solicitados pelos controles reais da interface:
  `access_anomalies`, `roles`, `access_revocation`, `teams`, `skills_map`,
  `training` e `initial_backlog`.
- Cada resposta deve ser uma proposta persistida `pending`, versão 1,
  `provider=gemini`, `simulated=false`, com o modelo escolhido, resumo e
  justificativa. A interface identifica a origem e informa que nenhuma alteração
  foi aplicada.
- A geração e a rejeição preservam projeto, membros, equipes e itens. Propostas
  aplicáveis de papéis/equipes e backlog só alteram dados depois do clique de
  aprovação, com repetição idempotente. O teste confere concessões/evento/outbox
  para papéis e vínculos/notificações internas para equipes quando sugeridas.
  Na rodada registrada acima, equipes retornou vazio, então esse caminho
  positivo ficou coberto pelos testes controlados. Análise vazia pode ser dispensada.
- As propostas e decisões devem continuar iguais após reiniciar as três APIs.
  A leitura pela conta sem acesso, por outro projeto ou sem autenticação é
  bloqueada. A análise administrativa exige administrador.
- Histórico de uso desconhecido retorna conflito antes de chamar Gemini. Para
  testar revogação, somente a observação temporal de um membro sintético é
  preparada diretamente no SQLite temporário. Quando há sugestões aplicáveis,
  uma mudança dessa observação após a geração impede a aprovação e persiste a
  proposta como expirada.
- O transporte HTTP real é observado nos processos temporários. Devem ocorrer
  exatamente sete chamadas Gemini HTTP 200. Não são encaminhados Bearer/cookie
  nem a chave no corpo. O perfil profissional sem consentimento é excluído do
  prompt; candidatos, projeto, evidências e elegibilidade para revogação são
  conferidos contra o contexto autorizado. Referências da análise de acessos
  devem pertencer aos usuários e eventos de auditoria enviados.

Cada execução cria bancos SQLite, chave RSA e serviços efêmeros exclusivamente
locais, com contas e projeto fictícios. Envio de e-mail e Módulo 6 são
explicitamente desativados; nenhum worker de entrega é iniciado. O observador
de transporte permite apenas chamadas locais e o host oficial do Gemini.
Os processos pertencentes ao teste são encerrados e os bancos são removidos ao
final, inclusive se uma asserção falhar.

Um resumo sanitizado da última execução integralmente aprovada é salvo em
`.local/gemini-acceptance/summary.json`, ignorado pelo Git. Ele contém modelo,
horário, tipos, quantidades de sugestões e decisões, sem chave, tokens, e-mails,
corpos de prompts ou texto gerado. A documentação publicada não depende desse
arquivo para explicar ou executar o teste.

### Limites da evidência

A saída textual e o número de sugestões não são determinísticos. As asserções
verificam contratos, referências autorizadas e efeitos das decisões, sem exigir
uma frase ou proposta específica. As verificações de aplicação do backlog e
expiração por mudança de contexto dependem de haver sugestões aplicáveis; o
resumo registra as decisões efetivamente exercitadas.

Este teste não demonstra qualidade em todos os contextos profissionais, precisão
estatística da IA, entrega de notificações, envio de e-mail ou funcionamento das
APIs implantadas. Os testes unitários de adaptadores e serviços continuam sendo
a evidência para respostas malformadas, indisponibilidade, cota, dados inventados
e outras falhas injetadas. Os testes de interface com respostas controladas
continuam cobrindo renderização segura e mensagens de erro.
