"""Cria banco novo por rodada. Nunca migra, limpa ou reutiliza banco existente."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('suite', choices=['api', 'e2e'])
    parser.add_argument('--frontend-dir', type=Path, default=ROOT / 'frontend')
    args = parser.parse_args()
    env = os.environ.copy()
    config = ROOT / '.local-test' / 'postgres.json'
    using_local_config = not env.get('POSTGRES_PASSWORD') and config.exists()
    if using_local_config:
        env.update(json.loads(config.read_text(encoding='utf-8')))
    required = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT']
    if any(not env.get(key) for key in required):
        raise SystemExit('Inicie postgres-local.py start ou configure o PostgreSQL exclusivo de testes.')
    if env['POSTGRES_HOST'] not in ('127.0.0.1', 'localhost') or env['POSTGRES_USER'] != 'acdn_test':
        raise SystemExit('Use somente PostgreSQL local com o usuário exclusivo acdn_test.')
    name = f'acdn_{args.suite}_{uuid.uuid4().hex[:12]}'
    with psycopg.connect(dbname='postgres', user=env['POSTGRES_USER'], password=env['POSTGRES_PASSWORD'],
                          host=env['POSTGRES_HOST'], port=env['POSTGRES_PORT'], autocommit=True) as admin:
        if using_local_config:
            actual = Path(admin.execute('SHOW data_directory').fetchone()[0]).resolve()
            expected = (ROOT / '.local-test' / 'postgres' / 'data').resolve()
            if actual != expected:
                raise SystemExit('Porta 55432 pertence a outro cluster; não prosseguir.')
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    env.update(POSTGRES_DB=name, DJANGO_SETTINGS_MODULE='config.settings_test', DJANGO_DEBUG='1', PYTHONIOENCODING='utf-8')
    print(f'Banco exclusivo: PostgreSQL {env["POSTGRES_HOST"]}:{env["POSTGRES_PORT"]}/{name}', flush=True)
    artifact = ROOT / 'test-results' / name
    artifact.mkdir(parents=True)

    def run(command):
        print('Executando: ' + ' '.join(map(str, command)), flush=True)
        result = subprocess.run(list(map(str, command)), cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        print(result.stdout, end='', flush=True)
        with (artifact / 'checks.log').open('a', encoding='utf-8') as log:
            log.write(' '.join(map(str, command)) + '\n' + result.stdout + f'\nExit: {result.returncode}\n')
        if result.returncode:
            raise SystemExit(result.returncode)

    manage = [sys.executable, ROOT / 'backend' / 'manage.py']
    run(manage + ['check'])
    run(manage + ['makemigrations', '--check', '--dry-run'])
    run(manage + ['migrate', '--noinput'])
    run(manage + ['shell', '-c', "from django.db import connection; print('vendor:', connection.vendor); c=connection.cursor(); c.execute('SELECT version(), current_database(), current_user, inet_server_port()'); print(c.fetchone())"])
    if args.suite == 'api':
        run(manage + ['test', 'core', '--noinput', '--verbosity', '2'])
    else:
        env['ACDN_E2E_RUN'] = name
        env['ACDN_TEST_PYTHON'] = sys.executable
        env['ACDN_TEST_MANAGE'] = str(ROOT / 'backend' / 'manage.py')
        env['ACDN_ARTIFACT_DIR'] = str(artifact)
        frontend = args.frontend_dir.resolve()
        run(['node', frontend / 'node_modules' / '@playwright' / 'test' / 'cli.js', 'test',
             '--config', frontend / 'playwright.config.ts'])
    print(f'Artefatos: {artifact}; banco sintético preservado para inspeção.', flush=True)


if __name__ == '__main__':
    main()
