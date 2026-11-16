import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
const local = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
const python = process.env.E2E_PYTHON || (existsSync(local) ? local : 'python');
export default defineConfig({
  testDir: './e2e-pages', globalSetup: './e2e/setup.ts', workers: 1, timeout: 240000,
  expect: { timeout: 180000 }, outputDir: 'artifacts/pages-test-results',
  reporter: [['list'], ['json', { outputFile: 'artifacts/pages-test-results.json' }]],
  use: { baseURL: 'http://127.0.0.1:8002/golden-ratio-tester/', headless: true, screenshot: 'only-on-failure' },
  projects: ['chromium', 'firefox', 'webkit'].map(browserName => ({ name: browserName, use: { browserName: browserName as 'chromium' | 'firefox' | 'webkit' } })),
  webServer: { command: `"${python}" scripts/serve_pages.py`, url: 'http://127.0.0.1:8002/golden-ratio-tester/', reuseExistingServer: false },
});
