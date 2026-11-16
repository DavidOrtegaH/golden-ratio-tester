import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';

test('real local Python analysis, no uploads, language, guides, original-sized download and deletion', async ({ page }, info) => {
  const badRequests: string[] = [], errors: string[] = [];
  page.on('request', request => {
    if (request.method() !== 'GET' || new URL(request.url()).origin !== 'http://127.0.0.1:8002') badRequests.push(request.url());
  });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./');
  const timeOrigin = await page.evaluate(() => performance.timeOrigin);
  await expect(page.locator('#image')).toBeEnabled();
  expect(await page.context().cookies()).toEqual([]);
  await page.locator('#image').setInputFiles('artifacts/e2e-fixtures/rectangle.png');
  await page.getByRole('button', { name: 'English', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await page.getByRole('button', { name: 'Analyze image ↗', exact: true }).click();
  await expect(page.locator('#analysis-result .result-count')).toHaveText('1');
  const image = page.locator('[data-result-image]');
  const annotated = await image.getAttribute('src');
  await page.getByRole('button', { name: 'Hide guides', exact: true }).click();
  expect(await image.getAttribute('src')).not.toBe(annotated);
  await page.getByRole('button', { name: 'Español', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Mostrar guías', exact: true })).toBeVisible();
  const downloaded = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Descargar PNG con guías ↓', exact: true }).click();
  const download = await downloaded, path = info.outputPath('export.png');
  await download.saveAs(path);
  const png = readFileSync(path); expect(png.readUInt32BE(16)).toBe(320); expect(png.readUInt32BE(20)).toBe(240);
  expect(download.suggestedFilename()).toBe('golden-ratio-tester.png');
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath('pages.jpg'), fullPage: true });
  await page.getByRole('button', { name: 'Eliminar mi imagen', exact: true }).click();
  await expect(page.locator('#analysis-result')).toBeHidden();
  await expect(page.locator('#image')).toHaveValue('');
  await page.locator('summary[data-i18n="privacy"]').click();
  await page.getByRole('button', { name: 'Olvidar mi idioma', exact: true }).click();
  expect(await page.context().cookies()).toEqual([]);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(timeOrigin);
  expect(badRequests).toEqual([]); expect(errors).toEqual([]);
  await page.locator('#image').setInputFiles('artifacts/e2e-fixtures/spiral.png');
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(page.locator('#analysis-result tbody')).toContainText('Tramo de espiral');
  expect(Number(await page.locator('#analysis-result .result-count').textContent())).toBeGreaterThanOrEqual(1);
});

test('paste, invalid image recovery and cancellation without a page reload', async ({ page }) => {
  await page.goto('./');
  await expect(page.locator('#image')).toBeEnabled();
  await page.locator('#image').setInputFiles('artifacts/e2e-fixtures/invalid.png');
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(page.locator('[data-workspace-target="status"]')).toContainText('No se pudo leer');
  await page.evaluate(bytes => {
    const transfer = new DataTransfer(); transfer.items.add(new File([new Uint8Array(bytes)], 'pasted.png', { type: 'image/png' }));
    const event = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: transfer }); document.body.dispatchEvent(event);
  }, [...readFileSync('artifacts/e2e-fixtures/rectangle.png')]);
  await expect(page.locator('[data-image-input-target="preview"]')).toBeVisible();
  // Leave the engine request pending until cancellation; no timing race with
  // an immediate network failure hiding the Cancel button in faster engines.
  await page.route('**/runtime/**', () => {});
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Cancelar análisis', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Cancelar análisis', exact: true }).click();
  await expect(page.locator('#image')).toBeEnabled();
  await expect(page.locator('[data-workspace-target="status"]')).toContainText('cancelado');
  await expect(page.locator('#analysis-result')).toBeHidden();
  expect(await page.locator('#image').evaluate((e: HTMLInputElement) => e.files?.[0]?.name)).toBe('pasted.png');
});
