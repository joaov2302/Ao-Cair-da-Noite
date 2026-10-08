# Testes isolados — rodada 01

Validado localmente em 08/10/2026. PostgreSQL 17.11, Python 3.13.14, Django 5.2.18, DRF 3.18.3, psycopg 3.3.6, Node 24.17.0 e npm 11.13.0. Vite 8.3.4 e Vitest 4.1.11 foram instalados pelo lockfile. O CI remoto ainda não foi executado nesta rodada.

## Windows sem Docker

Use o ambiente virtual e dependências do README. Os [binários oficiais EDB](https://www.enterprisedb.com/download-postgresql-binaries) são baixados pela primeira execução, somente para `.local-test/`. O script fixa versão/URL/hash observado do pacote; esse hash local não é apresentado como assinatura independente do fabricante. Não instala serviço, não altera PATH, não habilita virtualização e não modifica o banco de desenvolvimento.

```powershell
.\.venv\Scripts\python.exe scripts\postgres-local.py start
.\.venv\Scripts\python.exe scripts\test_env.py api
npm.cmd run test:e2e --prefix frontend
.\.venv\Scripts\python.exe scripts\postgres-local.py stop
```

Instale Chromium se ainda não estiver disponível: `npx.cmd --prefix frontend playwright install chromium`. As credenciais aleatórias do cluster ficam em `.local-test/postgres.json`, ignorado pelo Git; não copie esse arquivo para tickets ou relatórios.

`test_env.py` aceita somente host local e usuário dedicado `acdn_test`. Sem variáveis PostgreSQL explícitas, lê a configuração portátil e confere `SHOW data_directory` contra `.local-test/postgres/data`. Nunca usa `POSTGRES_DB` herdado: gera `acdn_api_<12 hex>` ou `acdn_e2e_<12 hex>` e cria esse banco novo; se a criação falhar, não reutiliza outro banco. Aplica migrations somente nessa base. A suíte Django cria e destrói apenas `test_acdn_api_<12 hex>`; a base vazia de preparação e os bancos E2E permanecem para inspeção. Não há limpeza de volume/banco da aplicação.

## Instalação do frontend sem disputar o Vite aberto

```powershell
.\.venv\Scripts\python.exe scripts\frontend-checks.py --e2e
```

O script copia o frontend para `.local-test/frontend-<12 hex>`, instala o lockfile com `npm ci`, executa build/Vitest e, com `--e2e`, verifica esse mesmo código no navegador usando o backend do repositório e o Python do ambiente virtual. Não copia `node_modules` nem builds antigos. PostgreSQL e Chromium são pré-requisitos. Logs ficam em `test-results/frontend-<12 hex>/checks.log`.

## Docker, quando disponível

Em vez do runtime portátil, configure senha exclusiva no terminal e use o Compose de testes, com projeto e volume distintos do Compose da aplicação:

```powershell
# Defina POSTGRES_PASSWORD no ambiente sem registrar seu valor no Git.
docker compose -f deploy\compose.test.yml up -d --wait
$env:POSTGRES_USER = 'acdn_test'
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_PORT = '55432'
.\.venv\Scripts\python.exe scripts\test_env.py api
npm.cmd run test:e2e --prefix frontend
docker compose -f deploy\compose.test.yml stop
```

Não inicie os dois runtimes na mesma porta. A configuração portátil não é usada quando uma senha explícita foi exportada. Docker local não foi validado: o pipe `dockerDesktopLinuxEngine` estava ausente e `VirtualizationFirmwareEnabled=False`. A alternativa portátil foi a execução comprovada.

## E2E e identidade dos alvos

`config.settings_test` exige PostgreSQL e nomes sintéticos explícitos. O runner fornece banco, módulo de settings, caminhos de Python/manage.py e pasta de artefatos. A chamada direta do Playwright sem esses valores é recusada. Cada invocação pelo comando npm prepara outro banco.

Backend: `127.0.0.1:8011`; Vite: `127.0.0.1:5175`, proxy fixado para a API de teste e `strictPort`. Ambos usam `reuseExistingServer:false`; porta ocupada aborta a execução. Cookies de sessão têm nome próprio. As portas normais 8000/5173 permanecem disponíveis para a aplicação da mesa. Foi comprovada a recusa de uma API preexistente na porta 8011 e a recusa do Playwright sem configuração exclusiva (`test-results/isolation.log`).

## Consistência e compatibilidade

Toda mutação de ficha adquire bloqueios em **campanha → ficha**, dentro de `transaction.atomic`. Decisões globais adquirem a campanha; decisões individuais adquirem campanha e ficha. O bloqueio explícito de ficha usa `select_for_update(of=('self',))`; o filtro de campanha com `DISTINCT` é usado para autorização, não para bloquear. Convites usam o bloqueio de sua própria linha; esse fluxo não adquire bloqueio de ficha.

O ponto de consistência da aprovação é a transação que lê as decisões aplicáveis e grava parecer/auditoria sob esses bloqueios. Continua sendo usado o conjunto exato de registros em `Submission.decisions`, ordenado por ID, combinado com a revisão do servidor. Se a decisão vence, a aprovação antiga recebe 409. Se a aprovação vence, a decisão posterior faz a projeção `approved` retornar falso, preservando parecer, snapshot e auditoria históricos. O bloqueio de campanha serializa escritas da mesma campanha: escolha conservadora para o volume atual, sem adicionar schema nesta rodada.

Cadastro duplicado simultâneo trata a violação de unicidade fora do bloco atômico e retorna 400 com mensagem em português. Criação de ficha e auditoria passaram a ser atômicas; as demais mutações já eram transacionais. Falha sintética de auditoria comprovou rollback integral em criação, edição, recursos, envio, parecer e decisão.

Os sete testes de concorrência usam `TransactionTestCase`, conexões independentes, barreiras/eventos e observação de `pg_stat_activity` nas duas ordens da corrida de aprovação. Os testes de disputa verificam PIDs diferentes e o nome real do banco de testes. SQLite pula esses casos; seus resultados não comprovam bloqueio de linhas. Referências: [bloqueios Django](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [transações Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

Sem nova migration, conversão de UUID, alteração de contratos, decisões de regra ou migração do banco pessoal. Recursos atuais continuam separados; atributo zero continua 2d20 com menor resultado.

## CI

Os jobs backend e E2E usam a ação local `.github/actions/postgres-test`: cria container PostgreSQL 17 na porta 55432, gera senha aleatória por job, mascara o valor e exporta por `GITHUB_ENV`. A prontidão exige conexão TCP no container. API executa checks, verificação de migrations, migrations reais, identificação de banco e suíte completa. E2E usa o mesmo runner de isolamento. Logs e capturas são anexados por `upload-artifact`, mesmo após falha.

Os YAMLs foram parseados localmente. Isso verifica estrutura sintática, não comprova execução no GitHub. O próximo gate é executar o workflow após commit/push autorizados; esta rodada não fez nenhum deles.
