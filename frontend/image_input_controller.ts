import { Controller } from "@hotwired/stimulus";

const allowed = new Set(["image/png", "image/jpeg", "image/webp"]);

export default class extends Controller<HTMLFormElement> {
  static targets = ["input", "preview", "status", "tools"];
  static values = { ready: String, empty: String, unsupported: String, size: String, format: String };
  declare inputTarget: HTMLInputElement;
  declare previewTarget: HTMLImageElement;
  declare statusTarget: HTMLElement;
  declare toolsTarget: HTMLElement;
  declare readyValue: string;
  declare emptyValue: string;
  declare unsupportedValue: string;
  declare sizeValue: string;
  declare formatValue: string;
  private previewUrl?: string;

  connect() { this.toolsTarget.hidden = false; }

  disconnect() {
    this.clearPreview();
  }

  private clearPreview() {
    if (this.previewUrl) URL.revokeObjectURL(this.previewUrl);
    this.previewUrl = undefined;
    this.previewTarget.removeAttribute("src");
    this.previewTarget.hidden = true;
  }

  private show(file: File) {
    this.clearPreview();
    this.previewUrl = URL.createObjectURL(file);
    this.previewTarget.src = this.previewUrl;
    this.previewTarget.hidden = false;
    this.message('paste_ready', this.readyValue);
    this.dispatch('changed');
  }

  private message(key: string, text: string) {
    this.statusTarget.textContent = text;
    this.statusTarget.dataset.i18n = key;
  }

  changed() {
    this.inputTarget.setCustomValidity('');
    const file = this.inputTarget.files?.[0];
    if (file && (!allowed.has(file.type) || file.size > 10 * 1024 * 1024)) {
      const tooLarge = file.size > 10 * 1024 * 1024;
      const text = tooLarge ? this.sizeValue : this.formatValue;
      this.clearPreview();
      this.inputTarget.setCustomValidity(text);
      this.message(tooLarge ? 'size' : 'format', text);
      this.dispatch('changed');
      return;
    }
    if (file) this.show(file);
    else { this.reset(); this.dispatch('changed'); }
  }

  reset() {
    this.inputTarget.setCustomValidity('');
    this.clearPreview();
    this.statusTarget.textContent = '';
    delete this.statusTarget.dataset.i18n;
  }

  private accept(file: File) {
    if (!allowed.has(file.type)) { this.message('format', this.formatValue); return; }
    if (file.size > 10 * 1024 * 1024) { this.message('size', this.sizeValue); return; }
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      this.inputTarget.files = transfer.files;
      this.inputTarget.setCustomValidity('');
      this.show(file);
    } catch {
      this.message('paste_unsupported', this.unsupportedValue);
    }
  }

  paste(event: ClipboardEvent) {
    if (this.element.getAttribute('aria-busy') === 'true') return;
    const target = event.target as HTMLElement | null;
    if (target instanceof Element && target.closest('textarea, [contenteditable="true"], input:not([type="file"])')) return;
    const items = Array.from(event.clipboardData?.items ?? []);
    const image = items.find(item => item.kind === "file" && item.type.startsWith("image/"))?.getAsFile()
      ?? Array.from(event.clipboardData?.files ?? []).find(file => file.type.startsWith("image/"));
    if (!image) { this.message('paste_empty', this.emptyValue); return; }
    event.preventDefault();
    this.accept(image);
  }

}
