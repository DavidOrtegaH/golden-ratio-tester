import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const rectangle = resolve('artifacts/e2e-fixtures/rectangle.png');
const invalid = resolve('artifacts/e2e-fixtures/invalid.png');
const result = (page: import('@playwright/test').Page) => page.locator('#analysis-result');
const originTime = (page: import('@playwright/test').Page) => page.evaluate(() => performance.timeOrigin);

test('one document: select, translate, analyze, toggle, download, reset cookie and delete', async ({ page }, info) => {
  await page.goto('/');
  const originalTime = await originTime(page);
  await page.locator('#image').setInputFiles(rectangle);
  const preview = await page.locator('[data-image-input-target="preview"]').getAttribute('src');
  await page.getByRole('button', { name: 'English', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  expect(await page.locator('[data-image-input-target="preview"]').getAttribute('src')).toBe(preview);
  await page.getByRole('button', { name: 'Analyze image ↗', exact: true }).click();
  await expect(result(page).getByRole('heading', { name: 'What the geometry says.' })).toBeVisible();
  await expect(result(page).locator('.result-count')).toHaveText('1');
  await result(page).getByRole('button', { name: 'Hide guides', exact: true }).click();
  await expect(result(page).locator('[data-result-image]')).toHaveAttribute('src', /original\/$/);
  const downloadPromise = page.waitForEvent('download');
  await result(page).getByRole('link', { name: 'Download PNG with guides ↓', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('golden-ratio-tester.png');
  const exported = info.outputPath('export.png'); await download.saveAs(exported);
  const bytes = readFileSync(exported); expect(bytes.readUInt32BE(16)).toBe(320); expect(bytes.readUInt32BE(20)).toBe(240);
  await page.getByRole('button', { name: 'Español', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'es');
  await expect(result(page).getByRole('button', { name: 'Mostrar guías', exact: true })).toBeVisible();
  await page.locator('summary[data-i18n=privacy]').click();
  await page.getByRole('button', { name: 'Olvidar mi idioma', exact: true }).click();
  await expect.poll(async () => (await page.context().cookies()).some(c => c.name === 'golden_ratio_tester_language')).toBe(false);
  await result(page).getByRole('button', { name: 'Eliminar mi imagen', exact: true }).click();
  await expect(result(page)).toBeHidden();
  await expect(page.locator('#image')).toHaveValue('');
  await expect(page.locator('#image')).toBeFocused();
  expect(await originTime(page)).toBe(originalTime);
  expect(new URL(page.url()).pathname).toBe('/');
});

test('invalid image and connection failure are recoverable without losing selection', async ({ page }) => {
  await page.goto('/');
  await page.locator('#image').setInputFiles(invalid);
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(page.locator('[data-workspace-target="status"]')).toContainText('No se pudo leer');
  await page.locator('#image').setInputFiles(rectangle);
  await page.route('http://127.0.0.1:8001/', route => route.request().method() === 'POST' ? route.abort() : route.continue());
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(page.locator('[data-workspace-target="status"]')).toContainText('No se pudo conectar');
  await expect(page.locator('#image')).toBeEnabled();
  expect(await page.locator('#image').evaluate((input: HTMLInputElement) => input.files?.[0]?.name)).toBe('rectangle.png');
  await page.unroute('http://127.0.0.1:8001/');
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(result(page).locator('.result-count')).toHaveText('1');
  const previousImage = await result(page).locator('[data-result-image]').getAttribute('src');
  await page.locator('#image').setInputFiles(resolve('artifacts/e2e-fixtures/replacement.png'));
  await expect(result(page)).toBeHidden();
  await expect.poll(async () => (await page.request.get(previousImage!)).status()).toBe(404);
});

test('paste event, keyboard controls, responsive widths and accessibility', async ({ page }, info) => {
  await page.goto('/');
  await page.evaluate(bytes => {
    const transfer = new DataTransfer();
    transfer.items.add(new File([new Uint8Array(bytes)], 'pasted.png', { type: 'image/png' }));
    // Firefox discards clipboardData supplied to a synthetic ClipboardEvent.
    // Use an explicit fixture payload; File/DataTransfer/FileList stay native
    // to each browser. This checks event handling, not the OS clipboard.
    const event = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: transfer });
    document.body.dispatchEvent(event);
  }, [...readFileSync(rectangle)]);
  await expect(page.locator('[data-image-input-target="preview"]')).toBeVisible();
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).press('Enter');
  await expect(result(page).locator('.result-count')).toHaveText('1');
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    const layout = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth,
      overflow: [...document.querySelectorAll<HTMLElement>('body *')].filter(el => el.getBoundingClientRect().right > innerWidth + 1).slice(0, 8).map(el => ({tag:el.tagName,classes:el.className,right:el.getBoundingClientRect().right})) }));
    expect(layout.document, JSON.stringify(layout)).toBeLessThanOrEqual(layout.viewport);
    await page.screenshot({ path: info.outputPath(`workspace-${width}.jpg`), fullPage: true });
  }
  const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({ path: info.outputPath('workspace.jpg'), fullPage: true });
  await page.screenshot({ path: info.outputPath('workspace-viewport.jpg') });
});

test('standard forms still work with scripts disabled', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:8001/');
  await page.locator('#image').setInputFiles(rectangle);
  await page.getByRole('button', { name: 'Analizar imagen ↗', exact: true }).click();
  await expect(result(page).locator('.result-count')).toHaveText('1');
  await result(page).getByRole('button', { name: 'Ocultar guías', exact: true }).click();
  await expect(result(page).locator('[data-result-image]')).toHaveAttribute('src', /original\/$/);
  await context.close();
});
