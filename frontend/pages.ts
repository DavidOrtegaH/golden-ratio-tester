import { Application, Controller } from '@hotwired/stimulus';
import ImageInputController from './image_input_controller';
let dictionaries: Record<string, Record<string, string>>;

interface Candidate {
  kind: string; points: number[][]; error: number; ratio: number;
  growth: number | null; support: number | null; metric: string;
}
type Language = 'es' | 'en';
class PagesController extends Controller<HTMLElement> {
  static targets = ['form', 'input', 'results', 'status'];
  declare formTarget: HTMLFormElement;
  declare inputTarget: HTMLInputElement;
  declare resultsTarget: HTMLElement;
  declare statusTarget: HTMLElement;
  private lang: Language = 'es';
  private busy = false;
  private worker?: Worker;
  private source?: HTMLCanvasElement;
  private original?: string;
  private annotated?: string;
  private candidates?: Candidate[];
  private guides = true;
  private timer?: ReturnType<typeof setTimeout>;
  private expire?: ReturnType<typeof setTimeout>;
  private generation = 0;
  private abortAnalysis?: () => void;

  async connect() {
    try {
      const response = await fetch(new URL('./copy.json', document.baseURI));
      if (!response.ok) throw new Error();
      dictionaries = await response.json();
    } catch {
      this.statusTarget.textContent = 'No se pudo cargar la aplicación. Recarga la página. / Could not load the app. Reload the page.';
      return;
    }
    const saved = document.cookie.split('; ').find(c => c.startsWith('golden_ratio_tester_language='))?.split('=')[1];
    this.lang = saved === 'en' ? 'en' : 'es';
    this.translate();
    this.element.querySelectorAll('[data-start-disabled]').forEach(e => e.removeAttribute('disabled'));
  }
  disconnect() { this.clear(); }
  private text(key: string) { return (dictionaries[this.lang] as Record<string, string>)[key] ?? key; }
  private announce(key: string, error = false) {
    this.statusTarget.dataset.i18n = key;
    this.statusTarget.textContent = key ? this.text(key) : '';
    this.statusTarget.classList.toggle('text-danger', error);
  }
  private setBusy(value: boolean) {
    this.busy = value;
    this.formTarget.setAttribute('aria-busy', String(value));
    this.element.querySelectorAll<HTMLInputElement | HTMLButtonElement>('[data-busy-control]')
      .forEach(e => e.disabled = value);
    const cancel = this.element.querySelector<HTMLElement>('[data-cancel]');
    if (cancel) cancel.hidden = !value;
  }
  language(event: SubmitEvent) {
    event.preventDefault();
    if (this.busy) return;
    const choice = (event.submitter as HTMLButtonElement)?.value;
    this.lang = choice === 'en' ? 'en' : 'es';
    const path = new URL('./', location.href).pathname;
    document.cookie = `golden_ratio_tester_language=${this.lang}; Max-Age=${choice === 'reset' ? 0 : 180 * 86400}; Path=${path}; SameSite=Lax${location.protocol === 'https:' ? '; Secure' : ''}`;
    this.translate();
  }
  private translate() {
    document.documentElement.lang = this.lang;
    document.title = `Golden Ratio Tester — ${this.text('tagline')}`;
    this.element.querySelectorAll<HTMLElement>('[data-i18n]').forEach(e => {
      if (e.dataset.i18n) e.textContent = this.text(e.dataset.i18n);
    });
    document.querySelectorAll<HTMLElement>('[data-i18n-attribute]').forEach(e => {
      const [attribute, key] = e.dataset.i18nAttribute!.split(':'); e.setAttribute(attribute, this.text(key));
    });
    this.element.querySelectorAll<HTMLAnchorElement>('[data-wiki]').forEach(e => e.href = this.text('wiki_url'));
    this.element.querySelectorAll<HTMLButtonElement>('[data-language-choice]').forEach(e => {
      const active = e.value === this.lang;
      e.setAttribute('aria-pressed', String(active));
      e.classList.toggle('btn-primary', active); e.classList.toggle('btn-outline-primary', !active);
    });
    const form = this.formTarget;
    for (const [attribute, key] of [['ready', 'paste_ready'], ['empty', 'paste_empty'], ['unsupported', 'paste_unsupported'], ['size', 'size'], ['format', 'format']]) {
      form.setAttribute(`data-image-input-${attribute}-value`, this.text(key));
    }
    if (this.candidates) this.renderResults(false);
  }
  selected() {
    if (this.busy) return;
    this.clear(); this.announce('new_selection');
  }
  private clear() {
    this.generation++;
    this.abortAnalysis?.(); this.abortAnalysis = undefined;
    this.worker?.terminate(); this.worker = undefined;
    clearTimeout(this.timer); clearTimeout(this.expire);
    if (this.original) URL.revokeObjectURL(this.original);
    if (this.annotated) URL.revokeObjectURL(this.annotated);
    this.original = this.annotated = undefined;
    if (this.source) { this.source.width = 0; this.source.height = 0; }
    this.source = undefined; this.candidates = undefined;
    this.resultsTarget.replaceChildren(); this.resultsTarget.hidden = true;
  }
  cancel() { this.clear(); this.setBusy(false); this.announce('cancelled'); }
  newImage(event: Event) {
    event.preventDefault(); if (this.busy) return;
    this.clear(); this.formTarget.reset();
    window.dispatchEvent(new Event('workspace:reset'));
    this.announce('deleted'); this.inputTarget.focus();
  }
  remove(event: Event) { this.newImage(event); }
  private async blob(canvas: HTMLCanvasElement) {
    return new Promise<Blob>((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('runtime_error')), 'image/png'));
  }
  async analyze(event: SubmitEvent) {
    event.preventDefault(); if (this.busy) return;
    const file = this.inputTarget.files?.[0];
    if (!file) { this.announce('missing', true); return; }
    if (file.size > 10 * 1024 * 1024) { this.announce('size', true); return; }
    this.clear(); this.setBusy(true); this.announce('processing');
    const generation = this.generation;
    try {
      if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) throw new Error('format');
      // Reject animation before native decoding (APNG acTL / WebP ANIM chunks).
      const bytes = new Uint8Array(await file.arrayBuffer());
      const view = new DataView(bytes.buffer);
      const tag = (i: number) => String.fromCharCode(...bytes.subarray(i, i + 4));
      if (tag(0) === 'RIFF') {
        if (tag(8) !== 'WEBP') throw new Error('format');
        for (let i = 12; i + 8 <= bytes.length;) {
          if (['ANIM', 'ANMF'].includes(tag(i))) throw new Error('format');
          const n = view.getUint32(i + 4, true); i += 8 + n + (n % 2);
        }
      } else if (tag(1) === 'PNG\r') {
        for (let i = 8; i + 12 <= bytes.length;) {
          if (tag(i + 4) === 'acTL') throw new Error('format');
          i += 12 + view.getUint32(i);
        }
      } else if (bytes[0] !== 255 || bytes[1] !== 216) throw new Error('format');
      const url = URL.createObjectURL(file);
      const image = new Image();
      try {
        await new Promise<void>((resolve, reject) => { image.onload = () => resolve(); image.onerror = () => reject(new Error('format')); image.src = url; });
      } finally { URL.revokeObjectURL(url); }
      if (generation !== this.generation) return;
      const w = image.naturalWidth, h = image.naturalHeight;
      if (w * h > 20_000_000 || Math.min(w, h) < 32 || Math.max(w, h) > 12000) throw new Error('pixels');
      const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h;
      const ctx = canvas.getContext('2d'); if (!ctx) throw new Error('runtime_error');
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h); ctx.drawImage(image, 0, 0);
      this.source = canvas;
      const small = document.createElement('canvas'), scale = Math.min(1, 1200 / Math.max(w, h));
      small.width = Math.round(w * scale); small.height = Math.round(h * scale);
      const smallCtx = small.getContext('2d'); if (!smallCtx) throw new Error('runtime_error');
      smallCtx.drawImage(canvas, 0, 0, small.width, small.height);
      const pixels = smallCtx.getImageData(0, 0, small.width, small.height).data;
      this.worker = new Worker(new URL('./worker.js', document.baseURI), { type: 'module' });
      await new Promise<void>((resolve, reject) => {
        this.abortAnalysis = () => reject(new Error('cancelled'));
        this.timer = setTimeout(() => reject(new Error('timeout')), 180000);
        this.worker!.onerror = () => reject(new Error('runtime_error'));
        this.worker!.onmessage = async ({ data }) => {
          if (data.stage) { this.announce(data.stage); return; }
          if (data.error) { reject(new Error(data.error)); return; }
          try {
            this.candidates = data.candidates; this.guides = true;
            const original = await this.blob(canvas);
            if (generation !== this.generation) return;
            this.original = URL.createObjectURL(original);
            this.drawGuides(ctx, data.candidates);
            const annotated = await this.blob(canvas);
            if (generation !== this.generation) return;
            this.annotated = URL.createObjectURL(annotated);
            this.source = undefined; canvas.width = canvas.height = 0;
            this.renderResults(true); this.announce('complete');
            this.expire = setTimeout(() => { this.clear(); this.announce('expired_notice'); }, 15 * 60 * 1000);
            resolve();
          } catch { reject(new Error('runtime_error')); }
        };
        this.worker!.postMessage({ pixels, width: small.width, height: small.height, originalWidth: w, originalHeight: h }, [pixels.buffer]);
      });
    } catch (error) {
      if (generation !== this.generation) return;
      this.clear();
      this.setBusy(false);
      const key = error instanceof Error && ['format', 'pixels', 'size', 'timeout'].includes(error.message) ? error.message : 'runtime_error';
      this.announce(key, true);
    } finally {
      if (generation === this.generation) {
        this.abortAnalysis = undefined;
        clearTimeout(this.timer); this.worker?.terminate(); this.worker = undefined; this.setBusy(false);
      }
    }
  }
  private drawGuides(ctx: CanvasRenderingContext2D, candidates: Candidate[]) {
    const width = Math.max(2, Math.round(Math.max(ctx.canvas.width, ctx.canvas.height) / 450));
    candidates.forEach((candidate, index) => {
      const points = candidate.points, color = candidate.kind === 'spiral' ? '#a4f4ce' : '#ffc865';
      const path = () => {
        ctx.beginPath(); points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
        if (candidate.kind !== 'spiral') ctx.closePath();
      };
      path(); ctx.strokeStyle = '#132923'; ctx.lineWidth = width + 3; ctx.stroke();
      path(); ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
      if (candidate.kind !== 'spiral' && points.length === 4) {
        let p = [...points];
        const distance = (a: number[], b: number[]) => Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (distance(p[1], p[0]) < distance(p[2], p[1])) p = [...p.slice(1), p[0]];
        for (const fraction of [.382, .618]) {
          ctx.beginPath(); ctx.moveTo(p[0][0] + (p[1][0] - p[0][0]) * fraction, p[0][1] + (p[1][1] - p[0][1]) * fraction);
          ctx.lineTo(p[3][0] + (p[2][0] - p[3][0]) * fraction, p[3][1] + (p[2][1] - p[3][1]) * fraction);
          ctx.lineWidth = Math.max(1, width / 2); ctx.stroke();
        }
      }
      const point = candidate.kind === 'spiral' ? points[Math.floor(points.length / 2)] : points[0];
      const x = Math.max(2, Math.min(point[0], ctx.canvas.width - 36)), y = Math.max(2, Math.min(point[1], ctx.canvas.height - 25));
      ctx.fillStyle = '#132923'; ctx.fillRect(x, y, 32, 23); ctx.fillStyle = color; ctx.font = '14px sans-serif'; ctx.fillText(String(index + 1), x + 6, y + 16);
    });
  }
  toggle(event: Event) { event.preventDefault(); this.guides = !this.guides; this.renderResults(false); }
  private renderResults(focus: boolean) {
    if (!this.candidates || !this.original || !this.annotated) return;
    // Static template is authored locally. Uploaded data only enters textContent.
    const template = document.querySelector<HTMLTemplateElement>('#pages-results')!;
    this.resultsTarget.replaceChildren(template.content.cloneNode(true)); this.resultsTarget.hidden = false;
    this.resultsTarget.querySelectorAll<HTMLElement>('[data-i18n]').forEach(e => e.textContent = this.text(e.dataset.i18n!));
    this.resultsTarget.querySelector('.result-count')!.textContent = String(this.candidates.length);
    const image = this.resultsTarget.querySelector<HTMLImageElement>('[data-result-image]')!;
    image.src = this.guides ? this.annotated : this.original; image.alt = this.text(this.guides ? 'annotated' : 'original');
    const toggle = this.resultsTarget.querySelector<HTMLButtonElement>('[data-guide-toggle]')!;
    toggle.textContent = this.text(this.guides ? 'hide' : 'show'); toggle.setAttribute('aria-pressed', String(this.guides));
    this.resultsTarget.querySelector<HTMLAnchorElement>('[download]')!.href = this.annotated;
    const body = this.resultsTarget.querySelector('tbody')!;
    this.candidates.forEach((candidate, index) => {
      const tr = document.createElement('tr');
      const cells = [String(index + 1), this.text(candidate.kind), candidate.kind === 'spiral' ? '—' : candidate.ratio.toFixed(4), `${candidate.error.toFixed(2)}% (${this.text(candidate.kind === 'spiral' ? candidate.metric : 'aspect_error')})`, candidate.growth?.toFixed(4) ?? '—', candidate.support == null ? '—' : `${candidate.support.toFixed(0)}%`];
      cells.forEach((value, i) => { const cell = document.createElement(i === 0 ? 'th' : 'td'); if (i === 0) cell.setAttribute('scope', 'row'); cell.textContent = value; tr.append(cell); }); body.append(tr);
    });
    this.resultsTarget.querySelector<HTMLElement>('[data-measurements]')!.hidden = !this.candidates.length;
    this.resultsTarget.querySelector<HTMLElement>('[data-empty]')!.hidden = !!this.candidates.length;
    this.resultsTarget.querySelector('[role="region"]')!.setAttribute('aria-label', this.text('measurements'));
    if (focus) this.resultsTarget.querySelector<HTMLElement>('h2')!.focus();
  }
}
const app = Application.start();
app.register('workspace', PagesController); app.register('image-input', ImageInputController);
