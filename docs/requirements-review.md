# Conferência dos requisitos — MVP P6 — 11/10/2026

Referências fornecidas pelo aluno: documento da disciplina, slide P6 (demonstração,
link para versão específica e apresentação parcial) e Guia_Visual_Modulo6.pdf v1.0.
A orientação informada permite recorte local, com valor demonstrável ao usuário.

Recorte atual: cadastro → login → projeto → histórias priorizadas → progresso
persistente. Frontend `0.2.0`, backlog `0.1.0`; identidade/projetos permanecem nos
seus repositórios. A entrega não representa a conclusão do módulo 1 inteiro.

| Requisito | Situação / evidência |
| --- | --- |
| Cadastro e login imediato | API real, validação dos campos e senha preservada |
| Identidade e acesso protegido | Permitir/bloquear confirmado pela API |
| Projetos persistentes por proprietário | Criar/listar/consultar; outra conta recebe 404 |
| Histórias por projeto | Título, descrição e critérios de aceite |
| Prioridades e progresso | Alta/média/baixa, a fazer/em andamento/concluído |
| Autorização do backlog | JWT e confirmação pela API de projetos em cada operação |
| Persistência após reinício | Três APIs temporárias + smoke separado no Neon |
| Responsabilidades/dados separados | Identidade 8000, projetos 8001, backlog 8002; schemas próprios |
| Falhas e envio único | 401/404/503, duplo submit, cancelamento e gravação confirmada com recarga falha |
| Validação visual | Mensagens junto aos campos, foco, teclado, temas e celular 390px |
| Identidade visual | Tokens e fontes do DESIGN.md, sem mudar o sistema visual |
| Valor demonstrável | Necessidades verificáveis, prioridades claras e progresso salvo |

Permanecem fora do recorte: equipes/RBAC, tarefas/sprints, estimativas, IA,
edição/exclusão de histórias e integração com o portal definitivo do módulo 6.
Cadastro não confirma posse do e-mail nem recupera senha; logout não revoga JWT
já emitido. Proprietário único não equivale a controle por papéis.

Resultados e roteiro: [verification.md](verification.md). Para P6, grave ou capture
a demonstração e informe os links das versões específicas após publicar/revisar
as alterações. Docker, deploy e CI/CD não foram validados nesta etapa.
