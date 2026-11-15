"""Generate our original mathematical illustration, without third-party artwork."""
import math
from pathlib import Path

points = []
for i in range(500):
    t = i / 499 * 3.5 * math.pi
    r = 5 * math.exp(2 * math.log((1 + math.sqrt(5)) / 2) / math.pi * t)
    points.append(f'{270 + r * math.cos(t):.2f},{225 + r * math.sin(t):.2f}')
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 440">
<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#b7c5ac" stroke-width=".5"/></pattern></defs>
<rect x="10" y="40" width="460" height="360" fill="url(#grid)"/>
<g fill="none" stroke="#8c9e7e"><path d="M35 88h410v253H35zM288 88v253M288 184h157M348 184v157M288 244h60"/><path d="M35 341 445 88M35 88l410 253" stroke-dasharray="4 6"/></g>
<polyline points="POINTS" fill="none" stroke="#155842" stroke-width="3"/>
<circle cx="270" cy="225" r="4" fill="#155842"/>
<g fill="#4f674b" font-family="Georgia,serif" font-size="13"><text x="30" y="77">a + b</text><text x="154" y="364">a</text><text x="365" y="364">b</text></g></svg>'''
Path('lab/static/lab/study.svg').write_text(svg.replace('POINTS', ' '.join(points)), encoding='utf-8')
