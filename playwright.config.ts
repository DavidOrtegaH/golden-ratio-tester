import { defineConfig } from '@playwright/test';
import { resolve } from 'node:path';

const python = process.env.E2E_PYTHON ?? resolve(process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/setup.ts',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 30000 },
  outputDir: 'artifacts/e2e-results',
  reporter: [['list'], ['json', { outputFile: 'artifacts/e2e-results.json' }]],
  use: { baseURL: 'http://127.0.0.1:8001', headless: true, viewport: { width: 1280, height: 900 }, screenshot: 'only-on-failure' },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } },
             { name: 'firefox', use: { browserName: 'firefox' } },
             { name: 'webkit', use: { browserName: 'webkit' } }],
  webServer: {
    command: `"${python}" manage.py runserver 127.0.0.1:8001 --noreload`,
    url: 'http://127.0.0.1:8001', reuseExistingServer: false,
    env: { DJANGO_DEBUG: '1', ANALYSIS_RATE_LIMIT: '1000' },
  },
});
