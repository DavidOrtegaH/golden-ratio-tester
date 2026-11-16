import assert from "node:assert/strict";
import { after, test } from "node:test";
import { JSDOM } from "jsdom";
import { Application } from "@hotwired/stimulus";
import WorkspaceController from "../frontend/workspace_controller";

const copy = { processing: "processing", network_error: "network_error", server_error: "server_error",
  complete: "complete", deleted: "deleted", new_selection: "new_selection", expired_notice: "expired_notice",
  rate_limit: "rate_limit", hide: "Hide", show: "Show", annotated: "annotated", original: "original",
  tagline: "test", intro: "intro", wiki_url: "https://en.wikipedia.org/wiki/Golden_ratio",
  paste_ready: "ready", paste_empty: "empty", paste_unsupported: "unsupported", size: "size", format: "format" };
const bank = Object.entries(copy).map(([key, value]) => `<span data-copy="${key}">${value}</span>`).join("");
const dom = new JSDOM(`<body data-controller="workspace">${bank}
 <span data-i18n="intro">intro</span><a data-wiki href="https://es.wikipedia.org/"></a>
 <form action="/language/" data-action="submit->workspace#language"><input name="csrfmiddlewaretoken" value="csrf">
 <input name="token"><button name="language" value="en" data-language-choice data-busy-control>English</button></form>
 <form action="/" data-workspace-target="form" data-action="submit->workspace#analyze">
 <input name="csrfmiddlewaretoken" value="csrf"><input type="file" name="image" data-workspace-target="input" data-busy-control>
 <button data-busy-control>Analyze</button></form>
 <p data-workspace-target="status"></p><div hidden data-workspace-target="results"></div>
 </body>`, { url: "http://localhost/" });
const win = dom.window;
for (const key of ["window", "document", "MutationObserver", "Element", "Node", "HTMLElement", "HTMLInputElement", "HTMLButtonElement", "KeyboardEvent", "MouseEvent", "CustomEvent", "FormData"] as const) {
  Object.defineProperty(globalThis, key, { configurable: true, value: key === "window" ? win : (win as any)[key] });
}
const app = Application.start(win.document.documentElement);
app.register("workspace", WorkspaceController);
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
await tick();
const form = win.document.querySelector<HTMLFormElement>('[data-workspace-target="form"]')!;
form.reportValidity = () => true;
const input = form.querySelector<HTMLInputElement>('[name="image"]')!;
const selected = new win.File(["image"], "photo.png", { type: "image/png" });
Object.defineProperty(input, "files", { get: () => [selected] });
const results = win.document.querySelector<HTMLElement>('[data-workspace-target="results"]')!;
const status = win.document.querySelector<HTMLElement>('[data-workspace-target="status"]')!;
const controller = app.getControllerForElementAndIdentifier(win.document.body, "workspace") as WorkspaceController;
const html = `<section data-result-token="private-token"><h2 tabindex="-1">Result</h2>
 <a href="/result/private-token/?guides=0" data-guide-toggle data-action="workspace#toggle">Hide</a>
 <img data-result-image data-overlay="/overlay/" data-original="/original/" src="/overlay/">
 <form action="/delete/private-token/" data-action="submit->workspace#remove"><input name="csrfmiddlewaretoken" value="csrf"><button>Delete</button></form></section>`;
let calls: { url: string; options: RequestInit }[] = [];
let respond: (url: string, options: RequestInit) => Promise<Response> = async () => Response.json({ ok: true, token: "private-token", html, expires_in: 900 });
win.fetch = (async (url: string | URL | Request, options: RequestInit) => {
  calls.push({ url: String(url), options }); return respond(String(url), options);
}) as typeof fetch;

test("analysis renders in the current document and uses CSRF multipart data", async () => {
  const document = win.document;
  const event = new win.SubmitEvent("submit", { bubbles: true, cancelable: true });
  form.dispatchEvent(event); await tick();
  assert.equal(event.defaultPrevented, true);
  assert.equal(win.document, document);
  assert.equal(win.location.pathname, "/");
  assert.equal(results.hidden, false);
  assert.equal(status.textContent, "complete");
  assert.equal(win.document.activeElement?.tagName, "H2");
  assert.equal((calls[0].options.body as FormData).get("csrfmiddlewaretoken"), "csrf");
  assert.equal(calls[0].options.credentials, "same-origin");
  assert.equal(input.disabled, false);
});

test("guide toggle switches the image without a request", async () => {
  const before = calls.length;
  results.querySelector<HTMLAnchorElement>('[data-guide-toggle]')!.click(); await tick();
  assert.equal(results.querySelector<HTMLImageElement>("img")!.getAttribute("src"), "/original/");
  assert.equal(results.querySelector('[data-guide-toggle]')!.textContent, "Show");
  assert.equal(calls.length, before);
});

test("language changes preserve selection, result and hidden-guide choice", async () => {
  respond = async () => Response.json({ ok: true, token: "private-token", html, expires_in: 900, lang: "en", copy: { ...copy, intro: "English intro" } });
  win.document.querySelector<HTMLButtonElement>('button[value="en"]')!.click(); await tick();
  assert.equal(win.document.documentElement.lang, "en");
  assert.equal(win.document.querySelector('[data-i18n="intro"]')!.textContent, "English intro");
  assert.equal(input.files![0], selected);
  assert.equal(results.querySelector<HTMLImageElement>("img")!.getAttribute("src"), "/original/");
  assert.equal((calls[calls.length - 1].options.body as FormData).get("language"), "en");
  assert.equal((calls[calls.length - 1].options.body as FormData).get("token"), "private-token");
});

test("errors retain the selected image and unlock controls", async () => {
  respond = async () => Response.json({ ok: false, code: "rate_limit" }, { status: 429 });
  form.dispatchEvent(new win.SubmitEvent("submit", { bubbles: true, cancelable: true })); await tick();
  assert.equal(status.textContent, "rate_limit");
  assert.equal(input.files![0], selected);
  assert.equal(input.disabled, false);
  respond = async () => { throw new TypeError('Failed to fetch "network"'); };
  form.dispatchEvent(new win.SubmitEvent("submit", { bubbles: true, cancelable: true })); await tick();
  assert.equal(status.textContent, "network_error");
});

test("duplicate submissions are ignored while analysis is busy", async () => {
  let finish!: (response: Response) => void;
  respond = () => new Promise(resolve => { finish = resolve; });
  const before = calls.length;
  form.dispatchEvent(new win.SubmitEvent("submit", { bubbles: true, cancelable: true }));
  form.dispatchEvent(new win.SubmitEvent("submit", { bubbles: true, cancelable: true }));
  assert.equal(calls.length, before + 1);
  assert.equal(form.getAttribute("aria-busy"), "true");
  const navigation = new win.MouseEvent('click', { cancelable: true });
  controller.newImage(navigation);
  assert.equal(navigation.defaultPrevented, true);
  assert.equal(results.hidden, false);
  finish(Response.json({ ok: true, token: "private-token", html, expires_in: 900 })); await tick();
});

test("delete clears result, resets the input view and stays on the page", async () => {
  let resets = 0;
  win.document.body.addEventListener("workspace:reset", () => resets++);
  respond = async () => Response.json({ ok: true });
  results.querySelector<HTMLButtonElement>("button")!.click(); await tick();
  assert.equal(results.hidden, true);
  assert.equal(results.childElementCount, 0);
  assert.equal(resets, 1);
  assert.equal(status.textContent, "deleted");
  assert.equal(win.location.pathname, "/");
});

test("expiry removes stale controls with a recoverable message", () => {
  results.innerHTML = html; results.hidden = false;
  controller.expired();
  assert.equal(results.hidden, true);
  assert.equal(status.textContent, "expired_notice");
});

after(() => { controller.disconnect(); app.stop(); win.close(); });
