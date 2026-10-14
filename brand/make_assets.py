"""
Builds app assets from the master logo (brand/MrsRomol.png):
  brand/logo.png               transparent, trimmed, full resolution
  miniapp/public/logo.webp     header logo (transparent, 600 px wide)
  miniapp/public/icon-512.png  square app icon (rose on cream)
  miniapp/public/favicon.png   64 px icon
Run:  uv run python brand/make_assets.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brand" / "MrsRomol.png"
BG = np.array([0xFA, 0xF9, 0xF5], dtype=np.float32)  # paper colour
CREAM = (0xFA, 0xF9, 0xF5, 255)


def color_to_alpha(rgb: np.ndarray) -> np.ndarray:
    """Remove the cream paper: alpha = how far a pixel is from the paper colour."""
    diff = np.clip((BG - rgb) / BG, 0, 1)
    alpha = diff.max(axis=2)
    alpha = np.clip((alpha - 0.05) / 0.95, 0, 1)  # paper texture noise → fully clear
    a = np.where(alpha > 0, alpha, 1)[..., None]
    color = np.clip((rgb - (1 - a) * BG) / a, 0, 255)
    return np.dstack([color, alpha * 255]).astype(np.uint8)


def trim(img: Image.Image, pad: int) -> Image.Image:
    box = img.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    l, t, r, b = box
    return img.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, img.width), min(b + pad, img.height)))


def main() -> None:
    rgb = np.asarray(Image.open(SRC).convert("RGB"), dtype=np.float32)
    h, w, _ = rgb.shape
    rgb[int(h * 0.85):, int(w * 0.92):] = BG  # drop the ✦ generator mark in the corner
    logo = trim(Image.fromarray(color_to_alpha(rgb), "RGBA"), pad=12)
    logo.save(ROOT / "brand" / "logo.png", optimize=True)

    public = ROOT / "miniapp" / "public"
    header = logo.copy()
    header.thumbnail((600, 600), Image.Resampling.LANCZOS)
    header.save(public / "logo.webp", "WEBP", quality=90, method=6)

    # Icon: the rose, centred on cream.
    rose = trim(Image.fromarray(color_to_alpha(rgb[194:283, 711:808]), "RGBA"), pad=0)
    icon = Image.new("RGBA", (512, 512), CREAM)
    rose = rose.resize((300, round(300 * rose.height / rose.width)), Image.Resampling.LANCZOS)
    icon.alpha_composite(rose, ((512 - rose.width) // 2, (512 - rose.height) // 2))
    icon.convert("RGB").save(public / "icon-512.png", optimize=True)
    icon.resize((64, 64), Image.Resampling.LANCZOS).convert("RGB").save(public / "favicon.png", optimize=True)

    for p in (ROOT / "brand" / "logo.png", public / "logo.webp", public / "icon-512.png", public / "favicon.png"):
        with Image.open(p) as im:
            print(f"{p.relative_to(ROOT)}: {im.size[0]}×{im.size[1]}, {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
