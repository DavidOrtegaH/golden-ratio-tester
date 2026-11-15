"""Reproduce development measurements without network access.

python scripts/evaluate_detector.py --photos artifacts/photo-validation
Optional external photos are never treated as mathematically labeled ground truth.
"""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from PIL import Image, ImageDraw
from skimage import data
from lab.geometry import analyze, GROWTH
from lab.imaging import overlay


def fixtures():
    rng = np.random.default_rng(23)
    image = Image.fromarray(rng.normal(180, 15, (600, 600, 3)).clip(0, 255).astype('uint8'))
    t = np.linspace(0, 3 * math.pi, 1200)
    r = 12 * np.exp(GROWTH * t)
    points = np.column_stack((300 + r * np.cos(t), 300 + r * np.sin(t)))
    draw = ImageDraw.Draw(image)
    draw.line([tuple(p) for p in points], fill=(35, 40, 30), width=5)
    draw.line((50, 350, 550, 350), fill=(100, 100, 100), width=2)
    yield 'textured-crossing', image, 'synthetic-positive'
    for name in ('camera', 'coffee', 'astronaut', 'chelsea'):
        yield name, Image.fromarray(getattr(data, name)()).convert('RGB'), 'photo-control-unlabeled'
    image = Image.fromarray(data.coffee()).resize((700, 700))
    t = np.linspace(0, 3 * math.pi, 1400)
    r = 12 * np.exp(GROWTH * t)
    points = np.column_stack((350 + r * np.cos(t), 350 + r * np.sin(t)))
    ImageDraw.Draw(image).line([tuple(p) for p in points], fill='white', width=6)
    yield 'coffee-composite', image, 'synthetic-curve-on-photo'


SOURCES = {
    'ontario.jpg': ('https://commons.wikimedia.org/wiki/File:Golden_Spiral.jpg', 'Ian Muttoo', 'CC BY-SA 2.0'),
    'hammonds.jpg': ('https://commons.wikimedia.org/wiki/File:Golden_Spiral_by_Brad_Hammonds.jpg', 'Brad Hammonds', 'CC BY 2.0'),
    'shell.jpg': ('https://commons.wikimedia.org/wiki/File:Golden_spiral_on_a_shell.jpg', 'Suyothami', 'CC BY-SA 4.0'),
    'light-art.jpg': ('https://commons.wikimedia.org/wiki/File:Goldene_Spirale_Rotgelb.jpg', 'Marinelli; artwork Martina Schettina', 'CC BY-SA 3.0'),
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--photos', type=Path)
    parser.add_argument('--output', type=Path, default=Path('artifacts/evaluation'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(fixtures())
    if args.photos:
        for name in SOURCES:
            if (args.photos / name).exists():
                cases.append((name, Image.open(args.photos / name).convert('RGB'), 'external-photo-unlabeled'))
    report = []
    for name, image, category in cases:
        started = time.perf_counter()
        candidates = analyze(image)
        elapsed = time.perf_counter() - started
        rows = [{key: value for key, value in asdict(c).items() if key not in ('points', 'model')} for c in candidates]
        entry = {'name': name, 'category': category, 'seconds': round(elapsed, 3),
                 'candidates': rows, 'source': SOURCES.get(name)}
        report.append(entry)
        # Own generated cases may be shared as fixtures; external photos retain
        # their own licenses and are not added to the source repository.
        image.save(args.output / (name + '.input.png'))
        annotated = overlay(image, candidates)
        annotated.thumbnail((1200, 1200))
        annotated.save(args.output / (name + '.overlay.png'))
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    (args.output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
