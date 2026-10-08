"""Instala e verifica uma cópia do frontend sem disputar módulos do Vite aberto."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--e2e', action='store_true')
    args = parser.parse_args()
    target = ROOT / '.local-test' / ('frontend-' + uuid.uuid4().hex[:12])
    shutil.copytree(ROOT / 'frontend', target,
                    ignore=shutil.ignore_patterns('node_modules', 'dist', '*.tsbuildinfo', 'test-results', 'playwright-report'))
    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    if not npm:
        raise SystemExit('npm não encontrado.')
    logs = ROOT / 'test-results' / target.name
    logs.mkdir(parents=True)
    print('Cópia exclusiva: ' + str(target), flush=True)
    for arguments in [('ci',), ('run', 'build'), ('test',)]:
        result = subprocess.run([npm, *arguments], cwd=target, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace')
        print(result.stdout, end='', flush=True)
        with (logs / 'checks.log').open('a', encoding='utf-8') as output:
            output.write('npm ' + ' '.join(arguments) + '\n' + result.stdout + f'\nExit: {result.returncode}\n')
        if result.returncode:
            raise SystemExit(result.returncode)
    if args.e2e:
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'test_env.py'), 'e2e', '--frontend-dir', str(target)], check=True)


if __name__ == '__main__':
    main()
