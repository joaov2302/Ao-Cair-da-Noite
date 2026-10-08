"""PostgreSQL portátil, somente em .local-test; sem serviços ou dados da mesa."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / '.local-test'
BIN = LOCAL / 'runtime' / 'pgsql' / 'bin'
DATA = LOCAL / 'postgres' / 'data'
CONFIG = LOCAL / 'postgres.json'
URL = 'https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip'
SHA256 = '80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f'


def run(exe, *args):
    subprocess.run([str(BIN / (exe + '.exe')), *map(str, args)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop'])
    args = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('Runtime portátil para Windows; em Linux use deploy/compose.test.yml.')
    if args.action == 'stop':
        if DATA.exists():
            run('pg_ctl', '-D', DATA, '-m', 'fast', '-w', 'stop')
        return
    LOCAL.mkdir(exist_ok=True)
    if not (BIN / 'initdb.exe').exists():
        archive = LOCAL / 'postgresql-17.11-5.zip'
        if not archive.exists():
            urllib.request.urlretrieve(URL, archive)
        with archive.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != SHA256:
                raise SystemExit('Hash do pacote PostgreSQL divergiu; não executar.')
        with zipfile.ZipFile(archive) as package:
            members = [n for n in package.namelist() if n.startswith(('pgsql/bin/', 'pgsql/lib/', 'pgsql/share/'))]
            package.extractall(LOCAL / 'runtime', members)
    if not DATA.exists():
        if CONFIG.exists():
            raise SystemExit('Configuração existente sem cluster; conferir antes de recriar.')
        config = {'POSTGRES_USER': 'acdn_test', 'POSTGRES_PASSWORD': secrets.token_urlsafe(36),
                  'POSTGRES_HOST': '127.0.0.1', 'POSTGRES_PORT': '55432'}
        CONFIG.write_text(json.dumps(config), encoding='utf-8')
        password_file = LOCAL / 'initdb-password'
        password_file.write_text(config['POSTGRES_PASSWORD'], encoding='utf-8')
        try:
            run('initdb', '-D', DATA, '-U', 'acdn_test', '--pwfile', password_file,
                '--auth', 'scram-sha-256', '--encoding', 'UTF8', '--locale', 'C')
        finally:
            password_file.unlink(missing_ok=True)
    if not CONFIG.exists():
        raise SystemExit('Cluster sem configuração de teste; não reutilizar.')
    status = subprocess.run([str(BIN / 'pg_ctl.exe'), '-D', str(DATA), 'status'], capture_output=True)
    if status.returncode == 0:
        print('Cluster de teste já iniciado.')
        return
    run('pg_ctl', '-D', DATA, '-l', LOCAL / 'postgres.log', '-o', '-h 127.0.0.1 -p 55432', '-w', 'start')


if __name__ == '__main__':
    main()
