# Aceite dos fluxos de e-mail — 15/11/2026

Recuperação de senha e confirmação de titularidade foram exercitadas pelo Edge,
com as três APIs reais em loopback e SQLite/chaves/conta temporários. O transporte
foi o Resend real, com remetente do domínio verificado `ckenzo.me` e somente o
destinatário de teste previamente configurado pelo titular.

Foram enviadas duas mensagens, uma de confirmação e outra de recuperação. O
teste consultou as mensagens enviadas pela API do Resend e aguardou seu evento
de entrega antes de abrir os links retornados pelo provedor. Não usou a caixa
postal local nem links fabricados. Não houve alteração de conta ou banco de
produção. A confirmação é do servidor destinatário reportada pelo provedor;
esta execução não inspecionou manualmente a pasta de entrada ou spam.

O teste confirmou:

- Confirmação de e-mail pela interface e recusa de reutilização do link.
- Remoção do fragmento da URL antes da confirmação/reset.
- Reset com código de recuperação do segundo fator e recusa de reutilização.
- Senha anterior recusada; senha nova ainda exige MFA.
- Sessão anterior recusada pela Identidade, Projetos e Backlog.

## Reprodução com autorização explícita

Prepare as dependências de testes e os três backends conforme o README. Defina
`AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH` para esses
checkouts. O harness sempre cria bancos SQLite temporários e inicia APIs locais.

Configure por um mecanismo privado as variáveis `RESEND_API_KEY`, `RESEND_FROM`
e `RESEND_TEST_TO`; nunca coloque os valores no Git, no frontend ou na saída de
um comando. A chave deste teste precisa de leitura de mensagens enviadas para
validar a entrega e recuperar seu conteúdo. Essa permissão de leitura é do
teste; o backend de produção pode continuar com chave limitada ao envio.

Com autorização para enviar duas mensagens ao endereço configurado:

```powershell
$env:RUN_RESEND_E2E = '1'
.venv/Scripts/python.exe -m unittest discover -s tests -p test_resend_real_api.py -v
Remove-Item Env:RUN_RESEND_E2E
```

Sem o opt-in, o teste é ignorado e não envia mensagens. Aguardar a entrega tem
prazo limitado e não reenvia POST automaticamente. Uma falha de consulta ou
entrega exige diagnóstico antes de repetir a execução, pois pode já ter havido
envio. Não habilite tracing, HAR ou capturas com tokens/credenciais nesse fluxo.

Contratos oficiais utilizados: [listar mensagens enviadas](https://resend.com/docs/api-reference/emails/list-emails)
e [consultar uma mensagem enviada](https://resend.com/docs/api-reference/emails/retrieve-email).
