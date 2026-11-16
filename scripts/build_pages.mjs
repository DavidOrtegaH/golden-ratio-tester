import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { build } from 'esbuild';

const localPython = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
const python = process.env.E2E_PYTHON || (existsSync(localPython) ? localPython : 'python');
const prepared = spawnSync(python, ['scripts/build_pages.py'], { stdio: 'inherit' });
if (prepared.status !== 0) process.exit(prepared.status || 1);
await build({ entryPoints: ['frontend/pages.ts'], bundle: true, minify: true, target: 'es2020', outfile: 'artifacts/pages/app.js' });
await build({ entryPoints: ['frontend/pages_worker.ts'], bundle: true, minify: true, format: 'esm', target: 'es2020', outfile: 'artifacts/pages/worker.js' });
