"""Demo product photos (soft draped-fabric gradients) for the local demo stack."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PALETTE = {
    "black": (40, 36, 38), "beige": (214, 190, 160), "rose": (214, 160, 150), "white": (238, 234, 228),
    "olive": (120, 124, 92), "navy": (44, 56, 92), "mocha": (130, 96, 78), "lilac": (184, 164, 196),
}

out = Path(sys.argv[1]) / "product-images" / "demo"
out.mkdir(parents=True, exist_ok=True)
for name, (r, g, b) in PALETTE.items():
    for n in range(2):
        W, H = 1200, 1600
        im = Image.new("RGB", (W, H), (246, 242, 236))
        d = ImageDraw.Draw(im)
        for x in range(0, W, 4):
            shade = 0.82 + 0.18 * math.sin(x / (60 + 25 * n) + n)
            top = 180 + int(60 * math.sin(x / 140))
            d.line([(x, top), (x + int(80 * math.sin(x / 300)), H)],
                   fill=(int(r * shade), int(g * shade), int(b * shade)), width=5)
        im = im.filter(ImageFilter.GaussianBlur(2))
        for suffix, size in (("", 1600), ("_thumb", 600)):
            c = im.copy()
            c.thumbnail((size, size))
            c.save(out / f"{name}{n}{suffix}.webp", "WEBP", quality=80)
