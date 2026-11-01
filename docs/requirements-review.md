# Conferência dos requisitos

## Versão 0.5.0 — preparada para publicação em 01/11/2026

O frontend integra as três APIs com arquitetura interna multicamadas, contas e
sessões seguras, equipes, papéis por projeto, planejamento e backlog com
histórias/épicos/tarefas, estimativas, MoSCoW e quadro. O refinamento premium
preserva as cores atuais e as fontes do módulo 6. A revisão independente das
36 capturas e das correções está em [premium-frontend.md](premium-frontend.md).

Logout e troca/reset de senha revogam sessões no servidor. Confirmação de e-mail
e MFA estão implementados; o cadastro ainda permite login imediato. O transporte
Resend teve envio e recebimento reais verificados somente para a conta do titular,
limite do remetente de teste. Esse teste não comprova o fluxo externo completo de
reset ou confirmação, nem autoriza afirmar envio para qualquer destinatário.

IA real e o contrato efetivo do módulo de revisão de código continuam pendentes.
Sprints, exclusão individual de histórias e integração com o portal definitivo
do módulo 6 não fazem parte desta entrega. A [matriz de US](backlog-status.md),
o [guia dos fluxos](local-user-stories.md) e a [validação](verification.md)
registram o alcance e os limites das evidências. A versão preparada não comprova
publicação ou disponibilidade de produção.

## Registro histórico — MVP P6 — 11/10/2026

As versões, capacidades ausentes e limitações abaixo descrevem exclusivamente
o recorte demonstrado em 11/10/2026. Não representam o estado da versão 0.5.0.

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
