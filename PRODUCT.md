# MOD1 Frontend

## Purpose
Frontend de demonstração do serviço de autenticação do módulo 1. Alunos e
professor entram com uma conta existente e verificam a identidade autenticada.
O módulo 6 será o portal central da plataforma; este projeto permite demonstrar
o MVP local e reaproveitar tokens, cliente HTTP e padrões de interface.

## Platform
Web responsiva, HTML/CSS/JavaScript com módulos ES, sem build ou dependências do
produto. Python/Playwright são apenas ferramentas de desenvolvimento e testes.

## Scope
Login por e-mail/senha, consulta e atualização da identidade, saída local e
temas claro/escuro. API real em configuração pública; sessão somente em memória.
O responsável cria contas pelo CLI do backend. Não há cadastro público,
recuperação de senha, projetos, equipes, backlog ou revogação no logout.

## Brand commitments
Seguir Guia_Visual_Modulo6.pdf v1.0: tokens compartilhados, ações azul-marinho,
Inter 400/500/600, neutros distintos nos dois temas. Vermelho não é cor de ação.
Identificação textual do módulo; nenhum logotipo oficial foi fornecido.

## Success
Demonstrar login → dados reais da conta → atualizar → sair; explicar erros e
expiração. Teclado, celular e temas claros/escuros funcionam. Evidências de
browser/API real ficam separadas de PostgreSQL, Docker e deploy.
