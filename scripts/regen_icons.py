"""Regeneriert alle Favicon- und PWA-Icon-Varianten aus dem Master-Logo.

Quelle (Default): app/static/img/logo-trans.png (transparenter Hintergrund)

Ausgabe:
  PWA-Icons     icon-192.png, icon-512.png  -> transparent (fuer maskable)
  Favicons      favicon-16/32/48/64/128.png, favicon.png, favicon.ico
                                            -> Hintergrund = Header-Rot (#b71921)
                                               damit sie im Tab + auf Desktop gut sichtbar sind
  Header-Logo   logo-trans.png wird zusaetzlich auf 512x512 verkleinert (in-place)
                damit es schneller geladen wird.

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
HEADER_BG = (183, 25, 33, 255)  # #b71921 = --topnav-bg
LOGO_MASTER_SIZE = 512


def square_pad(im: Image.Image) -> Image.Image:
    """Padded quadratisch (transparent) - verhindert Aspect-Ratio-Verzerrung."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    side = max(w, h)
    if w == h:
        return im
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas


def remove_light_background(im: Image.Image, threshold: int = 230) -> Image.Image:
    """Macht (fast) weisse Pixel transparent.

    Die Source-Datei `logo-trans.png` enthaelt trotz Namen einen hellgrauen
    Vollhintergrund (~(240,240,240)). Wir entfernen den per Color-Key.
    Pixel im Uebergang (Anti-Aliasing) erhalten reduziertes Alpha proportional
    zur Helligkeit -> weiche Kante statt harter Stair-Steps.
    """
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            # Min-Kanal als "Saettigung" - weisse/graue Pixel haben hohe min-Werte
            m = min(r, g, b)
            if m >= threshold:
                px[x, y] = (r, g, b, 0)
            elif m >= threshold - 30:
                # Weicher Uebergang: Alpha skaliert linear runter
                falloff = int(255 * (threshold - m) / 30)
                px[x, y] = (r, g, b, min(a, falloff))
    return im


def with_background(im: Image.Image, bg: tuple) -> Image.Image:
    """Legt das transparente Logo auf einen vollflaechigen Hintergrund."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    canvas = Image.new("RGBA", im.size, bg)
    canvas.paste(im, (0, 0), im)
    return canvas.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(IMG_DIR / "logo-trans.png"),
                    help="Pfad zum Master-Logo (Default: app/static/img/logo-trans.png)")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        raise SystemExit(f"Quelldatei nicht gefunden: {src}")

    print(f"[regen-icons] Quelle: {src}")
    master = Image.open(src)
    master = square_pad(master)

    # Master kleinrechnen, falls sehr gross (Performance + Vermeidung von
    # 1 MB+ Source-Files im Repo). Wir halten 512x512 als Arbeitsgrundlage.
    if max(master.size) > LOGO_MASTER_SIZE:
        master = master.resize((LOGO_MASTER_SIZE, LOGO_MASTER_SIZE), Image.LANCZOS)

    # Hellen Hintergrund per Color-Key in echte Transparenz wandeln
    # (logo-trans.png ist trotz Namen tatsaechlich vollopak mit ~weissem BG).
    master = remove_light_background(master)

    # Header-Quelle in-place neu schreiben (kleiner und optimiert).
    if src.name == "logo-trans.png":
        master.save(src, "PNG", optimize=True)
        print(f"  -> {src.relative_to(ROOT)} (verkleinert + Transparenz hergestellt)")

    # Favicons (PNG) - mit Header-Hintergrund
    for size in FAVICON_SIZES:
        out = IMG_DIR / f"favicon-{size}.png"
        sized = master.resize((size, size), Image.LANCZOS)
        with_background(sized, HEADER_BG).save(out, "PNG", optimize=True)
        print(f"  -> {out.relative_to(ROOT)}")

    # Default-Favicon (Alias auf 128er) - ebenfalls mit BG
    fav = IMG_DIR / "favicon.png"
    sized = master.resize((128, 128), Image.LANCZOS)
    with_background(sized, HEADER_BG).save(fav, "PNG", optimize=True)
    print(f"  -> {fav.relative_to(ROOT)}")

    # favicon.ico (Multi-Size) - ebenfalls mit BG
    ico = IMG_DIR / "favicon.ico"
    with_background(master, HEADER_BG).save(
        ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )
    print(f"  -> {ico.relative_to(ROOT)}")

    # PWA-Icons - transparent (fuer "any maskable" und Home-Screen-Komposition)
    for size in PWA_SIZES:
        out = IMG_DIR / f"icon-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(out, "PNG", optimize=True)
        print(f"  -> {out.relative_to(ROOT)}")

    print("[regen-icons] Fertig.")


if __name__ == "__main__":
    main()
