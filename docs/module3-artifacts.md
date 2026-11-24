# Artefatos nos projetos

A aba **Artefatos** está disponível a quem tem `project:read`. Usuários com
`project:update`, em um projeto editável, podem clicar em **Escolher projeto**,
selecionar o projeto correspondente no Módulo 3 e confirmar **Vincular projeto**.
O vínculo é explícito; nomes iguais não fazem associação automática. Também
é possível desvincular sem excluir qualquer arquivo.

Depois do vínculo, a tela permite pesquisar por nome, filtrar por tipo,
consultar versões e baixar a versão atual. Não faz upload, não cria projetos
no M3 e não dispara análise de IA. Resumos e classificações aguardam um GET
do provedor que permita descobrir o identificador de análise.

O navegador chama somente a API de Projetos com a sessão M1. O backend usa
GET na API pública do Módulo 3, sem repassar o token M1. Não há alteração de
CORS ou dependência de login no M3. O download é um anexo limitado a 10 MiB,
sem token na URL, cancelado ao trocar de contexto e sem visualização inline.

O vínculo usa os metadados existentes do projeto, sem nova tabela. A gravação
segue as permissões, o histórico e as notificações normais de edição do projeto.
Não vinculamos projetos de produção automaticamente durante a validação.

Erros e listas vazias aparecem na própria área. Recusa de um arquivo ou acesso
remove o conteúdo anterior; uma troca do vínculo exige atualizar a consulta.
Falhas do provedor não encerram a sessão M1. Leituras interrompidas não geram
downloads ou resultados antigos após navegar para outro projeto.

[Contrato das rotas e limites](https://github.com/briankfreire/MOD1-ProjectsServices/blob/main/docs/module3-artifacts.md)
e [validação](verification.md).
