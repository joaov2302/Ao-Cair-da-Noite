import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const result = spawnSync(python, [path.join(root, 'scripts/test_env.py'), 'e2e'], {cwd: root, stdio: 'inherit'});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
