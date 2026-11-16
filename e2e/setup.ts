import { execFileSync } from 'node:child_process';

export default function setup() {
  execFileSync(process.env.E2E_PYTHON ?? (process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python'), ['-c', `
from pathlib import Path
from PIL import Image, ImageDraw
root=Path('artifacts/e2e-fixtures'); root.mkdir(parents=True,exist_ok=True)
image=Image.new('RGB',(320,240),'#f8f7f2')
ImageDraw.Draw(image).rectangle((30,40,289,200),fill='#e4eddc',outline='#155842',width=4)
image.save(root/'rectangle.png')
(root/'replacement.png').write_bytes((root/'rectangle.png').read_bytes())
(root/'invalid.png').write_bytes(b'not an image')
`]);
}
