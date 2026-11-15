import assert from "node:assert/strict";
import { after, test } from "node:test";
import { JSDOM } from "jsdom";
import { Application } from "@hotwired/stimulus";
import ImageInputController from "../frontend/image_input_controller";

const dom = new JSDOM(`<form data-controller="image-input" data-action="paste@window->image-input#paste"
 data-image-input-ready-value="ready" data-image-input-empty-value="empty"
 data-image-input-denied-value="denied" data-image-input-unsupported-value="unsupported"
 data-image-input-size-value="large" data-image-input-format-value="format">
 <input type="file" name="image" required data-image-input-target="input" data-action="change->image-input#changed">
 <div hidden data-image-input-target="tools"><button type="button" data-image-input-target="button" data-action="image-input#read">Paste</button></div>
 <p data-image-input-target="status"></p><img hidden data-image-input-target="preview">
 </form>`, { url: "http://localhost/" });
const window = dom.window;
for (const name of ["window", "document", "MutationObserver", "Element", "Node", "HTMLElement", "KeyboardEvent", "MouseEvent", "File"] as const) {
  Object.defineProperty(globalThis, name, { configurable: true, value: name === "window" ? window : (window as any)[name] });
}
const clipboard: { read?: () => Promise<any[]> } = {};
Object.defineProperty(globalThis, "navigator", { configurable: true, value: { clipboard } });
const revoked: string[] = [];
let serial = 0;
URL.createObjectURL = () => `blob:test-${++serial}`;
URL.revokeObjectURL = url => revoked.push(url);
class Transfer {
  files: File[] = [];
  items = { add: (file: File) => this.files.push(file) };
}
Object.defineProperty(globalThis, "DataTransfer", { configurable: true, value: Transfer });
const form = window.document.querySelector("form")!;
const input = window.document.querySelector("input")!;
// jsdom has no DataTransfer implementation. The real-browser smoke check covers
// native FileList assignment; here we exercise the Stimulus events and UI state.
let files: File[] = [];
Object.defineProperty(input, "files", { get: () => files, set: value => { files = value; } });
const status = window.document.querySelector("p")!;
const preview = window.document.querySelector("img")!;
const button = window.document.querySelector("button")!;
const app = Application.start(window.document.documentElement);
app.register("image-input", ImageInputController);
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
await tick();
const controller = app.getControllerForElementAndIdentifier(form, "image-input") as ImageInputController;
assert.ok(controller);
let submits = 0;
form.addEventListener("submit", event => { event.preventDefault(); submits++; });

function paste(file?: File) {
  const event = new window.Event("paste", { bubbles: true, cancelable: true });
  Object.defineProperty(event, "clipboardData", { value: { items: file ? [{ kind: "file", type: file.type, getAsFile: () => file }] : [], files: [] } });
  window.dispatchEvent(event);
  return event;
}
const image = (name = "copied.png") => new window.File([new Uint8Array([1, 2, 3])], name, { type: "image/png" }) as unknown as File;

test("paste selects an image and shows a preview without submitting", () => {
  const file = image();
  assert.equal(paste(file).defaultPrevented, true);
  assert.equal(input.files![0], file);
  assert.equal(status.textContent, "ready");
  assert.equal(preview.hidden, false);
  assert.equal(submits, 0);
});

test("file selection replaces pasted preview and revokes its URL", () => {
  const old = preview.src;
  files = [image("selected.png")];
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
  assert.equal(input.files![0].name, "selected.png");
  assert.ok(revoked.includes(old));
  paste(image("replacement.png"));
  assert.equal(input.files![0].name, "replacement.png");
});

test("text-only, unsupported and oversized images preserve the selection", () => {
  const selected = input.files![0];
  assert.equal(paste().defaultPrevented, false);
  assert.equal(status.textContent, "empty");
  paste(new window.File(["<svg/>"], "x.svg", { type: "image/svg+xml" }) as unknown as File);
  assert.equal(status.textContent, "format");
  const large = image(); Object.defineProperty(large, "size", { value: 11 * 1024 * 1024 });
  paste(large);
  assert.equal(status.textContent, "large");
  assert.equal(input.files![0], selected);
});

test("paste button reads images only on explicit click", async () => {
  let reads = 0;
  clipboard.read = async () => { reads++; return [{ types: ["text/plain", "image/png"], getType: async () => new Blob(["image"], { type: "image/png" }) }]; };
  assert.equal(reads, 0);
  button.click(); await tick();
  assert.equal(reads, 1);
  assert.equal(input.files![0].name, "clipboard.png");
  assert.equal(button.disabled, false);
  assert.equal(submits, 0);
});

test("clipboard denial, empty result and unsupported API show guidance", async () => {
  clipboard.read = async () => { throw new Error("denied"); };
  await controller.read(); assert.equal(status.textContent, "denied");
  clipboard.read = async () => [];
  await controller.read(); assert.equal(status.textContent, "empty");
  delete clipboard.read;
  await controller.read(); assert.equal(status.textContent, "unsupported");
});

test("late clipboard reads cannot replace a newer selected file", async () => {
  let resolve!: (value: any[]) => void;
  clipboard.read = () => new Promise(done => { resolve = done; });
  const pending = controller.read();
  files = [image("newer.png")]; controller.changed();
  resolve([{ types: ["image/png"], getType: async () => new Blob(["image"]) }]);
  await pending;
  assert.equal(input.files![0].name, "newer.png");
});

test("disconnect revokes the final preview URL", () => {
  const old = preview.src;
  controller.disconnect();
  assert.ok(revoked.includes(old));
  assert.equal(preview.hidden, true);
});

after(() => { app.stop(); window.close(); });
