import { Controller } from "@hotwired/stimulus";

const allowed = new Set(["image/png", "image/jpeg", "image/webp"]);

export default class extends Controller<HTMLFormElement> {
  static targets = ["input", "preview", "status", "button", "tools"];
  static values = { ready: String, empty: String, denied: String, unsupported: String, size: String, format: String };
  declare inputTarget: HTMLInputElement;
  declare previewTarget: HTMLImageElement;
  declare statusTarget: HTMLElement;
  declare buttonTarget: HTMLButtonElement;
  declare toolsTarget: HTMLElement;
  declare readyValue: string;
  declare emptyValue: string;
  declare deniedValue: string;
  declare unsupportedValue: string;
  declare sizeValue: string;
  declare formatValue: string;
  private previewUrl?: string;
  private revision = 0;

  connect() { this.toolsTarget.hidden = false; }

  disconnect() {
    this.revision++;
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
    this.revision++;
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
      this.revision++;
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

  async read() {
    if (!navigator.clipboard?.read) { this.statusTarget.textContent = this.unsupportedValue; return; }
    const revision = this.revision;
    this.buttonTarget.disabled = true;
    try {
      const items = await navigator.clipboard.read();
      for (const item of items) {
        const type = item.types.find(type => allowed.has(type));
        if (type) {
          const blob = await item.getType(type);
          if (this.revision !== revision || !this.element.isConnected) return;
          const extension = type.split("/")[1];
          this.accept(new File([blob], `clipboard.${extension}`, { type }));
          return;
        }
      }
      if (this.revision === revision) this.statusTarget.textContent = this.emptyValue;
    } catch {
      if (this.revision === revision) this.statusTarget.textContent = this.deniedValue;
    } finally {
      this.buttonTarget.disabled = false;
    }
  }
}
