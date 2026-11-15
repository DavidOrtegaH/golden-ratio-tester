from io import BytesIO
import warnings
import numpy as np
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 20_000_000


def decode(upload):
    if upload.size > 10 * 1024 * 1024:
        raise ValueError('size')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(upload) as source:
                if source.format not in ('JPEG', 'PNG', 'WEBP') or getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('format')
                if source.width * source.height > 20_000_000 or min(source.size) < 32:
                    raise ValueError('pixels')
                source.load()
                normalized = ImageOps.exif_transpose(source).convert('RGBA')
                background = Image.new('RGBA', normalized.size, 'white')
                background.alpha_composite(normalized)
                # New pixel-only image has no EXIF, ICC, filename or textual metadata.
                return Image.frombytes('RGB', background.size, background.convert('RGB').tobytes())
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('format') from None


def png(image):
    output = BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()


def overlay(image, candidates):
    result = image.copy()
    draw = ImageDraw.Draw(result)
    width = max(2, round(max(image.size) / 450))
    for index, candidate in enumerate(candidates, 1):
        points = [tuple(p) for p in candidate.points]
        color = '#a4f4ce' if candidate.kind == 'spiral' else '#ffc865'
        path = points if candidate.kind == 'spiral' else points + [points[0]]
        draw.line(path, fill='#132923', width=width + 3)
        draw.line(path, fill=color, width=width)
        if candidate.kind != 'spiral':
            p = np.asarray(points)
            if np.linalg.norm(p[1] - p[0]) < np.linalg.norm(p[2] - p[1]):
                p = np.roll(p, -1, axis=0)
            for fraction in (0.382, 0.618):
                a = p[0] + (p[1] - p[0]) * fraction
                b = p[3] + (p[2] - p[3]) * fraction
                draw.line([tuple(a), tuple(b)], fill=color, width=max(1, width // 2))
        x, y = points[len(points) // 2] if candidate.kind == 'spiral' else points[0]
        x, y = max(2, min(x, image.width - 36)), max(2, min(y, image.height - 25))
        draw.rectangle((x, y, x + 32, y + 23), fill='#132923')
        draw.text((x + 6, y + 4), str(index), fill=color)
    return result
