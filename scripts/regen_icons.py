"""Regeneriert alle Favicon- und PWA-Icon-Varianten aus dem Master-Logo.

Quelle: app/static/img/logo.png  (das einsatzleiter.cloud-Markenlogo)

Ausgabe: favicon-16/32/48/64/128.png, favicon.png, favicon.ico,
         icon-192.png, icon-512.png  — alle quadratisch, alpha-Channel erhalten.

Verwendung:
    python scripts/regen_icons.py
    python scripts/regen_icons.py --src path/to/logo.png
"""
from __future__ import annotations
import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "app" / "static" / "img"

FAVICON_SIZES = (16, 32, 48, 64, 128)
PWA_SIZES = (192, 512)


def square_pad(im: Image.Image) -> Image.Image:
    """Padded quadratisch (transparent) — verhindert Aspect-Ratio-Verzerrung."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    side = max(w, h)
    if w == h:
        return im
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(IMG_DIR / "logo.png"),
                    help="Pfad zum Master-Logo (Default: app/static/img/logo.png)")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        raise SystemExit(f"Quelldatei nicht gefunden: {src}")

    print(f"[regen-icons] Quelle: {src}")
    master = Image.open(src)
    master = square_pad(master)

    # Favicons (PNG)
    for size in FAVICON_SIZES:
        out = IMG_DIR / f"favicon-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(out, "PNG", optimize=True)
        print(f"  ->{out.relative_to(ROOT)}")

    # Default-Favicon (Alias auf 128er)
    fav = IMG_DIR / "favicon.png"
    master.resize((128, 128), Image.LANCZOS).save(fav, "PNG", optimize=True)
    print(f"  ->{fav.relative_to(ROOT)}")

    # favicon.ico (Multi-Size)
    ico = IMG_DIR / "favicon.ico"
    master.save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"  ->{ico.relative_to(ROOT)}")

    # PWA-Icons
    for size in PWA_SIZES:
        out = IMG_DIR / f"icon-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(out, "PNG", optimize=True)
        print(f"  ->{out.relative_to(ROOT)}")

    print("[regen-icons] Fertig.")


if __name__ == "__main__":
    main()
