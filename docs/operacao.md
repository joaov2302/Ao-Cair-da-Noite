# Operação

## Desenvolvimento

API apenas em `127.0.0.1:8000`; Vite em `127.0.0.1:5173` com proxy `/api`, preservando mesma origem e proteção CSRF. Banco local `backend/db.sqlite3` ignorado pelo Git. `.venv`, builds, logs, arquivos privados e resultados transitórios também ignorados.

## Produção pendente

Configurar PostgreSQL, segredo novo em `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, proxy HTTPS e servidor WSGI. Django impede produção sem segredo ou configuração PostgreSQL. O proxy serve `frontend/dist`, encaminha `/api` ao WSGI e nunca serve diretórios privados. Não há deploy automático neste projeto.

Não confiar em cabeçalhos de proxy encaminhados por clientes. Se usar `SECURE_PROXY_SSL_HEADER`, configure-o somente após comprovar que o proxy remove cabeçalhos externos. Executar `manage.py check --deploy` no ambiente real. Cookies de sessão HttpOnly e Secure/CSRF Secure são ativados em produção.

Autenticação tem limite local de tentativas por IP. Para múltiplos processos de produção, configurar cache compartilhado e limitação no proxy; o cache em memória de desenvolvimento não compartilha contadores entre workers. Convites individuais expiram em sete dias e são consumidos transacionalmente.

Backup PostgreSQL e arquivos privados precisa de procedimento e restauração demonstrada em ambiente separado antes da publicação. Nenhuma restauração foi demonstrada nesta execução.

## Conteúdo

RulesetVersion é imutável pela operação normal dos modelos/admin. Cada campanha aponta para uma versão. Evolução/migração de versão de campanha ainda não tem interface. Os cálculos usam a versão inicial implementada; não adicionar fórmulas executáveis ao catálogo JSON.

Imagens são cadastradas apenas por administrador e entregues por endpoint autenticado após aprovação e verificação de campanha. Não há rota pública para `MEDIA_ROOT`. Antes de importar uma imagem real: autorização explícita, validação de formato/dimensões e cálculo do hash. Cadastro/upload direto pelo navegador fica para curadoria posterior.

## Referências técnicas consultadas em 08/10/2026

- [Django 5.2.18](https://docs.djangoproject.com/en/5.2/releases/5.2.18/): patch adotado nesta implementação.
- [Autenticação DRF](https://www.django-rest-framework.org/api-guide/authentication/): sessão e CSRF; login implementado com view Django protegida inclusive antes da autenticação.
- [Vite](https://vite.dev/guide/): requisitos de Node para o ambiente utilizado.
