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
    this.statusTarget.textContent = this.readyValue;
  }

  changed() {
    const file = this.inputTarget.files?.[0];
    if (file) this.show(file);
    else { this.clearPreview(); this.statusTarget.textContent = ""; }
  }

  private accept(file: File) {
    if (!allowed.has(file.type)) { this.statusTarget.textContent = this.formatValue; return; }
    if (file.size > 10 * 1024 * 1024) { this.statusTarget.textContent = this.sizeValue; return; }
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      this.inputTarget.files = transfer.files;
      this.show(file);
    } catch {
      this.statusTarget.textContent = this.unsupportedValue;
    }
  }

  paste(event: ClipboardEvent) {
    const target = event.target as HTMLElement | null;
    if (target instanceof Element && target.closest('textarea, [contenteditable="true"], input:not([type="file"])')) return;
    const items = Array.from(event.clipboardData?.items ?? []);
    const image = items.find(item => item.kind === "file" && item.type.startsWith("image/"))?.getAsFile()
      ?? Array.from(event.clipboardData?.files ?? []).find(file => file.type.startsWith("image/"));
    if (!image) { this.statusTarget.textContent = this.emptyValue; return; }
    event.preventDefault();
    this.accept(image);
  }

}
