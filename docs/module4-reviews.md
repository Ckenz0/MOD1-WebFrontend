# Revisões de código por item

No espaço de trabalho, abra **Quadro e itens**, selecione um item e escolha
**Revisões de código**. O histórico é consultado somente ao abrir essa tela e
contém registros daquele projeto e item. Leitores do backlog podem consultar
os registros mesmo com novas análises desativadas.

O formulário exige permissão para atualizar a situação, projeto gravável e
integração habilitada no Backlog. Escolha uma origem: URL HTTPS de Pull Request
do GitHub ou até 20 arquivos Python, somando até 100.000 bytes UTF-8. Arquitetura
inicial: multicamadas. O uso de IA exige marcar a opção explicitamente; começa
desmarcada. O código é encaminhado ao serviço externo pelo backend. Credenciais
Basic do provedor ficam exclusivamente no Backlog; o navegador usa a sessão M1.

Uma análise válida pode iniciar um item a fazer. Itens em andamento ou
concluídos preservam sua situação, e concluir a entrega exige ação humana.
A interface recarrega o item após a resposta para exibir a situação e a versão
efetivamente persistidas. Conflitos, mudança de acesso ou falhas têm indicação
própria no registro e não significam conclusão.

Achados, texto de IA e relatório Markdown são exibidos como texto. A interface
não interpreta HTML, executa trechos retornados nem publica comentários em PR.

## Falhas e identificadores

Cada envio explícito recebe um UUID. Em falha ambígua de rede, o identificador
continua visível e nenhum POST é repetido automaticamente. A interface consulta
o histórico; se essa leitura também falhar, é necessário atualizar as revisões
antes de liberar uma nova análise. Registros pendentes ou incertos mostram um
aviso de possível duplicidade. Uma nova solicitação exige escolher explicitamente
**Nova análise mesmo com risco de duplicidade** e recebe outro UUID.

Conflitos de versão também exigem recarregar os registros e o item. Se o
histórico já contém o resultado terminal daquela solicitação, a próxima análise
explícita recebe outro UUID. Quando o UUID não aparece na página consultada,
o resultado permanece desconhecido e uma nova análise exige a confirmação de
possível duplicidade. O aviso de registros pendentes ou incertos conhecidos
permanece ao trocar de página. Novos envios ficam na primeira página do histórico.

Sair da tela ou trocar a sessão invalida operações pendentes, inclusive durante
a leitura de arquivos. Código e credenciais não são guardados em localStorage
ou sessionStorage. O histórico persistente pertence ao serviço de Backlog.

## Verificação local

Os testes de domínio e do controlador real ficam em `tests/test_module4_ui.py`.
Eles cobrem limites de origem, arquivos, bytes UTF-8, permissões, desativação,
texto seguro, atualização de versão, falha de rede sem reenvio e cancelamento
durante leitura de arquivo.

`tests/test_module4_real_api.py` usa três APIs temporárias com bancos SQLite
descartáveis e um provedor HTTP loopback. A execução comum exige definir
`AUTH_BACKEND_PATH`, `PROJECTS_BACKEND_PATH` e `BACKLOG_BACKEND_PATH` para os
checkouts locais. Não lê arquivos privados, não utiliza credenciais reais,
não chama o proprietário externo e mantém notificações/e-mail desativados.
Esse teste verifica transporte, início do item, replay sem novo POST, preservação
após reinício e falha incerta sem alterar a situação.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p test_module4_ui.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_module4_real_api.py -v
```
