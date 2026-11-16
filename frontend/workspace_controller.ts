import { Controller } from "@hotwired/stimulus";

interface Reply {
  ok: boolean;
  code?: string;
  lang?: string;
  copy?: Record<string, string>;
  html?: string;
  token?: string;
  expires_in?: number;
}

export default class extends Controller<HTMLElement> {
  static targets = ["form", "input", "results", "status"];
  declare formTarget: HTMLFormElement;
  declare inputTarget: HTMLInputElement;
  declare resultsTarget: HTMLElement;
  declare statusTarget: HTMLElement;
  private busy = false;
  private expiry?: ReturnType<typeof setTimeout>;
  private guidesVisible = true;

  connect() {
    this.syncToken();
    const result = this.resultsTarget.querySelector<HTMLElement>("[data-result-token]");
    if (result) {
      this.guidesVisible = result.dataset.guidesVisible !== "false";
      this.startExpiry(Number(result.dataset.expiresIn ?? 0));
      if (location.pathname.startsWith('/result/')) history.replaceState(null, '', '/');
    }
  }

  disconnect() { clearTimeout(this.expiry); }

  private enhanced() { return typeof window.fetch === "function" && typeof FormData !== "undefined"; }

  private text(key: string) {
    return this.element.querySelector<HTMLElement>(`[data-copy="${key}"]`)?.textContent ?? key;
  }

  private announce(key: string, error = false) {
    this.statusTarget.textContent = key ? this.text(key) : "";
    this.statusTarget.dataset.i18n = key;
    this.statusTarget.classList.toggle("text-danger", error);
  }

  private setBusy(busy: boolean) {
    this.busy = busy;
    this.formTarget.setAttribute("aria-busy", String(busy));
    this.element.querySelectorAll<HTMLInputElement | HTMLButtonElement>("[data-busy-control]")
      .forEach(control => { control.disabled = busy; });
  }

  private token() { return this.resultsTarget.querySelector<HTMLElement>("[data-result-token]")?.dataset.resultToken ?? ""; }

  private syncToken() {
    this.element.querySelectorAll<HTMLInputElement>('input[name="token"]').forEach(input => { input.value = this.token(); });
  }

  private async request(url: string, body: FormData): Promise<Reply> {
    const controller = typeof AbortController !== "undefined" ? new AbortController() : undefined;
    const timeout = controller ? setTimeout(() => controller.abort(), 60000) : undefined;
    try {
      const response = await window.fetch(url, { method: "POST", body, credentials: "same-origin",
        headers: { Accept: "application/json" }, signal: controller?.signal });
      if (!(response.headers.get("Content-Type") ?? "").includes("application/json")) throw new Error("network_error");
      const data = await response.json() as Reply;
      if (!response.ok || !data.ok) throw new Error(data.code ?? "server_error");
      return data;
    } finally { clearTimeout(timeout); }
  }

  private error(error: unknown) {
    const key = error instanceof Error && /^[a-z_]+$/.test(error.message) && this.element.querySelector(`[data-copy="${error.message}"]`)
      ? (error as Error).message : "network_error";
    this.announce(key, true);
  }

  private render(data: Reply, focus: boolean) {
    // HTML is an escaped, same-origin Django fragment; no uploaded HTML is rendered.
    this.resultsTarget.innerHTML = data.html ?? "";
    this.resultsTarget.hidden = !data.token;
    this.syncToken();
    this.applyGuides();
    this.startExpiry(data.expires_in ?? 0);
    if (focus && data.token) this.resultsTarget.querySelector<HTMLElement>("h2")?.focus();
  }

  private startExpiry(seconds: number) {
    clearTimeout(this.expiry);
    if (seconds > 0) this.expiry = setTimeout(() => this.expired(), seconds * 1000);
  }

  async analyze(event: SubmitEvent) {
    if (!this.enhanced()) return;
    event.preventDefault();
    if (this.busy || !this.formTarget.reportValidity()) return;
    const body = new FormData(this.formTarget);
    this.setBusy(true);
    this.announce("processing");
    try {
      const previous = this.token();
      const data = await this.request(this.formTarget.action, body);
      this.guidesVisible = true;
      this.render(data, true);
      this.announce("complete");
      if (previous && previous !== data.token) this.discard(previous);
    } catch (error) { this.error(error); }
    finally { this.setBusy(false); }
  }

  private applyGuides() {
    const image = this.resultsTarget.querySelector<HTMLImageElement>("[data-result-image]");
    const button = this.resultsTarget.querySelector<HTMLElement>("[data-guide-toggle]");
    if (!image || !button) return;
    image.src = this.guidesVisible ? image.dataset.overlay! : image.dataset.original!;
    image.alt = this.text(this.guidesVisible ? "annotated" : "original");
    button.textContent = this.text(this.guidesVisible ? "hide" : "show");
    button.setAttribute("aria-pressed", String(this.guidesVisible));
    button.dataset.i18n = this.guidesVisible ? "hide" : "show";
  }

  toggle(event: Event) {
    if (!this.enhanced()) return;
    event.preventDefault();
    this.guidesVisible = !this.guidesVisible;
    this.applyGuides();
  }

  async language(event: SubmitEvent) {
    if (!this.enhanced()) return;
    event.preventDefault();
    if (this.busy) return;
    const form = event.target as HTMLFormElement;
    const submitter = event.submitter as HTMLButtonElement | null
      ?? (document.activeElement instanceof HTMLButtonElement ? document.activeElement : null);
    const body = new FormData(form);
    body.set("language", submitter?.value ?? "es");
    body.set("token", this.token());
    this.setBusy(true);
    try {
      const data = await this.request(form.action, body);
      if (!data.copy || !data.lang) throw new Error("server_error");
      const copy = data.copy;
      document.documentElement.lang = data.lang;
      document.title = `Golden Ratio Tester — ${copy.tagline}`;
      this.element.querySelectorAll<HTMLElement>("[data-i18n]").forEach(element => {
        const key = element.dataset.i18n!;
        if (copy[key] !== undefined) element.textContent = copy[key];
      });
      this.element.querySelectorAll<HTMLElement>("[data-copy]").forEach(element => { element.textContent = copy[element.dataset.copy!] ?? ""; });
      document.querySelectorAll<HTMLElement>("[data-i18n-attribute]").forEach(element => {
        const [attribute, key] = element.dataset.i18nAttribute!.split(":");
        if (copy[key]) element.setAttribute(attribute, copy[key]);
      });
      this.element.querySelectorAll<HTMLAnchorElement>("[data-wiki]").forEach(link => { link.href = copy.wiki_url; });
      this.element.querySelectorAll<HTMLButtonElement>("[data-language-choice]").forEach(button => {
        const active = button.value === data.lang;
        button.setAttribute("aria-pressed", String(active));
        button.classList.toggle("btn-primary", active); button.classList.toggle("btn-outline-primary", !active);
      });
      for (const key of ["ready", "empty", "unsupported", "size", "format"]) {
        const source = ["ready", "empty", "unsupported"].includes(key) ? `paste_${key}` : key;
        this.formTarget.setAttribute(`data-image-input-${key}-value`, copy[source]);
      }
      if (this.inputTarget.validity.customError) {
        const key = this.inputTarget.files?.[0]?.size && this.inputTarget.files[0].size > 10 * 1024 * 1024 ? 'size' : 'format';
        this.inputTarget.setCustomValidity(copy[key]);
      }
      this.render(data, false);
    } catch (error) { this.error(error); }
    finally { this.setBusy(false); }
  }

  private discard(token: string) {
    const body = new FormData();
    body.set("csrfmiddlewaretoken", this.formTarget.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]')!.value);
    void this.request(`/delete/${encodeURIComponent(token)}/`, body).catch(() => { /* Expiry still bounds lifetime. */ });
  }

  selected() {
    if (this.token()) {
      this.discard(this.token());
      this.clearResults();
      this.announce("new_selection");
    }
  }

  private clearResults() {
    clearTimeout(this.expiry);
    this.resultsTarget.replaceChildren();
    this.resultsTarget.hidden = true;
    this.syncToken();
  }

  private reset() {
    this.clearResults();
    this.formTarget.reset();
    this.dispatch("reset");
    this.inputTarget.focus();
  }

  newImage(event: Event) {
    if (!this.enhanced()) return;
    event.preventDefault();
    if (this.busy) return;
    if (this.token()) this.discard(this.token());
    this.reset();
    this.announce("");
  }

  async remove(event: SubmitEvent) {
    if (!this.enhanced()) return;
    event.preventDefault();
    if (this.busy) return;
    const form = event.target as HTMLFormElement;
    const body = new FormData(form);
    this.setBusy(true);
    try { await this.request(form.action, body); this.setBusy(false); this.reset(); this.announce("deleted"); }
    catch (error) { this.error(error); }
    finally { this.setBusy(false); }
  }

  expired() {
    if (!this.token()) return;
    this.clearResults();
    this.announce("expired_notice", true);
  }
}
