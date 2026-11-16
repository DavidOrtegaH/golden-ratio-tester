// All runtime and detector resources are served from the Pages origin.
interface PythonRuntime {
  loadPackage(names: string[]): Promise<void>;
  unpackArchive(data: ArrayBuffer, format: string, options: { extractDir: string }): void;
  globals: { set(name: string, value: unknown): void; delete(name: string): void };
  runPythonAsync(code: string): Promise<string>;
}
const runtimeUrl = new URL('./runtime/pyodide.mjs', location.href).href;
let ready: Promise<PythonRuntime> | undefined;
async function runtime() {
  if (!ready) ready = (async () => {
    const { loadPyodide } = await import(/* @vite-ignore */ runtimeUrl);
    const py: PythonRuntime = await loadPyodide({ indexURL: new URL('./runtime/', location.href).href });
    await py.loadPackage(['numpy', 'scipy', 'scikit-image', 'opencv-python']);
    const response = await fetch(new URL('./detector.zip', location.href));
    if (!response.ok) throw new Error('runtime_error');
    py.unpackArchive(await response.arrayBuffer(), 'zip', { extractDir: '/home/pyodide' });
    return py;
  })();
  return ready;
}
const python = `
import json, gc
from dataclasses import asdict
import numpy as np
from lab.geometry import analyze_rgb
def _run_browser_detector():
    pixels = np.asarray(_pixels.to_py(), dtype=np.uint8).reshape((_height, _width, 4))
    candidates = analyze_rgb(pixels[:, :, :3].copy(), (_original_width, _original_height))
    return json.dumps([asdict(candidate) for candidate in candidates], allow_nan=False)
try:
    _answer = _run_browser_detector()
finally:
    gc.collect()
_answer
`;
let running = false;
self.onmessage = async event => {
  if (running) return;
  running = true;
  try {
    self.postMessage({ stage: 'loading_runtime' });
    const py = await runtime();
    self.postMessage({ stage: 'processing' });
    const { pixels, width, height, originalWidth, originalHeight } = event.data;
    py.globals.set('_pixels', pixels);
    py.globals.set('_width', width); py.globals.set('_height', height);
    py.globals.set('_original_width', originalWidth); py.globals.set('_original_height', originalHeight);
    try { self.postMessage({ candidates: JSON.parse(await py.runPythonAsync(python)) }); }
    finally {
      for (const name of ['_pixels', '_width', '_height', '_original_width', '_original_height', '_answer']) {
        py.globals.delete(name);
      }
    }
  } catch { ready = undefined; self.postMessage({ error: 'runtime_error' }); }
  finally { running = false; }
};
