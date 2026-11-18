# Curadoria no projeto

Em **Meus projetos**, abra um projeto, escolha **Gerenciar projeto e
planejamento** e selecione **Curadoria**. A seção carrega o feed de tecnologia
ao abrir. Quem tem `project:read` pode acessar o feed e fazer perguntas, inclusive
em projetos arquivados. A API de Projetos verifica a sessão ativa e a permissão
antes de consultar o Módulo 5 e novamente antes de entregar a resposta.

Para pesquisar, escreva uma **Pergunta sobre tecnologia** de 1 a 2.000
caracteres e clique em **Buscar artigos**. Esse clique envia a pergunta ao
Módulo 5. Um cartão de recomendação de treinamento com tópicos oferece **Buscar
materiais de estudo**. O botão abre a seção com uma pergunta editável feita
com os tópicos, aguardando o envio explícito.

## Contrato

O navegador usa a configuração existente da API de Projetos e a sessão atual
do Módulo 1.

| Operação | Rota da API de Projetos | Corpo |
| --- | --- | --- |
| Abrir o feed | `GET /projects/{project_id}/curation/feed` | Vazio |
| Pesquisar artigos | `POST /projects/{project_id}/curation/queries` | `{"pergunta":"..."}` |

As duas rotas recebem o Bearer pelo cabeçalho `Authorization`. Projetos solicita
o feed externo sem Bearer. Na pesquisa externa, encaminha o Bearer no cabeçalho
e somente a pergunta no corpo. O frontend não consulta nem edita conversas existentes.
O Módulo 5 pode registrar a pergunta enviada. Os dados do projeto permanecem intactos.
Configuração e comunicação com o Módulo 5 ficam na API de Projetos.

Ambas retornam `enabled`, `artigos`, `total`, `categoria`, `fontes_consultadas`,
`fontes_indisponiveis` e `truncated`. Cada artigo traz título, link, fonte,
idioma e data de publicação. A interface aceita até 50 artigos e sinaliza
truncamento e fontes indisponíveis. Os títulos e metadados são exibidos como
texto. Links absolutos HTTP(S) seguros abrem em outra aba com `noopener
noreferrer`.

## Resultados e falhas

- Um feed vazio e uma pesquisa sem resultados têm mensagens próprias.
- Com a integração desativada, o feed retorna `enabled: false` e a tela não
  oferece o formulário. A API recusa pesquisas com `503` nesse estado.
- Uma falha de feed pode ser retomada ao abrir **Curadoria** novamente. A busca
  segue disponível se o acesso for válido e o estado da integração for
  desconhecido por uma falha temporária do feed.
- Uma pesquisa sem resposta confirmada pode ter sido registrada pelo Módulo 5.
  A interface mantém a pergunta editável, informa essa possibilidade e aguarda
  outro envio explícito. Uma pesquisa em andamento aceita um único envio.
- Ao sair da seção, trocar de projeto ou encerrar a sessão, a interface
  descarta respostas antigas. Um `401` encerra o acesso e pede novo login.

## Verificação local

Com os caminhos das três APIs configurados e seus ambientes virtuais prontos,
execute a validação de navegador com banco, contas e provedor descartáveis.

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_module5*.py" -v
```

Para registrar as capturas do teste integrado, defina `CAPTURE_MODULE5_EVIDENCE`
com o diretório local de saída. O teste usa o provedor em loopback e verifica
ausência de rolagem horizontal na seção em 1366 e 390 pixels.
Veja os resultados em [Validação](verification.md).
