# Ao Cair da Noite

Caderno de personagens em português: criação guiada de nível 1, comparação dos quatro arquétipos e revisão assíncrona do mestre.

React/TypeScript/Vite no frontend; Django 5.2 LTS e Django REST Framework na API. PostgreSQL configurado para produção; SQLite somente no desenvolvimento.

## Executar no Windows

Pré-requisitos: Python 3.13 e Node.js 24.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm.cmd ci --prefix frontend
.\.venv\Scripts\python.exe backend\manage.py migrate
```

Em um terminal:

```powershell
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

Em outro:

```powershell
npm.cmd run dev --prefix frontend
```

Abra **http://127.0.0.1:5173**. Crie sua conta pela interface; não existem senhas de demonstração embutidas. Criar campanha atribui o papel de mestre ao criador. Convites são individuais e expiram em sete dias. Jogadores só veem as próprias fichas; o mestre vê as fichas de sua campanha.

Alternativa com processos em segundo plano e logs locais:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1
```

O script imprime os IDs dos processos iniciados. Encerre apenas esses processos quando terminar. A opção `-ExecutionPolicy Bypass` vale apenas para esse processo do PowerShell.

## Verificar

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend\manage.py test core
npm.cmd run build --prefix frontend
npm.cmd test --prefix frontend
cd frontend
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Os comandos Django acima verificam SQLite quando não há configuração PostgreSQL; sete testes concorrentes são pulados nesse modo. Para evidência completa e E2E, inicie o PostgreSQL exclusivo de testes:

```powershell
.\.venv\Scripts\python.exe scripts\postgres-local.py start
.\.venv\Scripts\python.exe scripts\test_env.py api
npm.cmd run test:e2e --prefix frontend
.\.venv\Scripts\python.exe scripts\postgres-local.py stop
```

O runtime portátil do Windows fica em `.local-test/`, com senha aleatória, sem serviço do Windows e sem migrar o SQLite da mesa. Cada rodada cria um banco PostgreSQL novo. Playwright usa portas **8011/5175**, recusa servidores preexistentes e registra somente usuários e campanhas **sintéticos**. As decisões dos testes não são decisões da mesa real.

Com Vite aberto, reproduza instalação, build, testes e E2E numa cópia do frontend, evitando módulos bloqueados pelo Windows:

```powershell
.\.venv\Scripts\python.exe scripts\frontend-checks.py --e2e
```

O PostgreSQL deve estar iniciado e o Chromium instalado. Consulte [testes e isolamento](docs/testing.md) para a alternativa com Docker e localização das evidências.

## Regras e limites

Cinco atributos base (FOR/AGI/VIG/PRE/INT), faixa 0–3 e até 9 pontos. Soma incompleta pode ser salva; fica pendente até definição de R09. Atributo 0 usa 2d20 e o menor resultado, conforme orientação do usuário em 08/10/2026. Demais atributos usam maior resultado de atributo × d20. Rolagem mostra resultado bruto: treinamento e vantagem/desvantagem ainda não foram definidos.

Recursos iniciais dos quatro arquétipos são calculados e explicados pela API, com seção e hash da fonte. Recursos atuais ficam separados. Editar a ficha ou mudar decisões da campanha invalida aprovação anterior; snapshots e comentários históricos permanecem.

Raça, perícias, equipamentos e técnicas são registros manuais para revisão. Nenhum benefício racial ou grau de treinamento é aplicado automaticamente. R06/R08/R09 bloqueiam aprovação até decisão registrada do mestre. Aprovar o registro manual não transforma a interpretação em automação. O catálogo de imagens começa vazio. Não há livros, capturas, fichas reais ou tokens privados no repositório.

Documentação: [prompt revisado](docs/prompt-desenvolvimento.md), [estado e verificações](docs/execucao.md), [operação](docs/operacao.md).

## PostgreSQL

Com Docker ativo, defina uma senha local antes de iniciar o serviço:

```powershell
$env:POSTGRES_PASSWORD = 'sua-senha-local'
docker compose -f deploy\compose.yml up -d
$env:POSTGRES_DB = 'acdn'
$env:POSTGRES_USER = 'acdn'
$env:POSTGRES_HOST = '127.0.0.1'
.\.venv\Scripts\python.exe backend\manage.py migrate
```

Este Compose é o banco da aplicação; para testes use o runtime acima ou `deploy/compose.test.yml`. As variáveis de `.env.example` devem ser exportadas no terminal: esse arquivo não é carregado automaticamente. Para produção, configure também chave secreta, hosts e HTTPS. [Operação e publicação](docs/operacao.md) registra os gates ainda pendentes. PostgreSQL 17.11 passou localmente na rodada 01; API e E2E estão preparados para PostgreSQL no CI, cuja execução remota continua pendente.
