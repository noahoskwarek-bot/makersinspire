#!/usr/bin/env python3
"""Rebuild every logo / icon / share-image file from brand/logo-original.jpg.

Needs: pip install vtracer cairosvg pillow numpy   (e.g. in a venv; the site build itself doesn't need these)
Run from the repo root:  python3 tools/make_brand.py
Outputs (committed; build.py only references them):
  brand/logo-white.svg   silver-gradient MI mark + white wordmark, transparent (for dark areas)
  brand/logo-black.svg   all ink #111, transparent (for light areas: the header + footer)
  brand/mark-silver.svg, brand/mark-white.svg, brand/mark-black.svg   MI square only
  brand/*@2x.png, brand/*@3x.png   PNG fallbacks (1x = 48px tall)
  favicon.svg, favicon.ico (16/32/48), apple-touch-icon.png (180), icon-192.png, icon-512.png
  images/og-logo.png     1200x630 share image
How: the original is cropped, upscaled 3x (Lanczos), thresholded (mark and wordmark separately),
traced with vtracer (binary, spline), then near-straight curves are collapsed to lines.
The mark's silver is a measured linear gradient (#efefef top-left -> #989898 bottom-right; fit residual < 1 level).
"""
import io, json, os, re, sys, tempfile
import numpy as np, vtracer, cairosvg
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from _simplify import simp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'brand', 'logo-original.jpg')
S = 3                        # upscale factor before thresholding
CX, CY, CX1, CY1 = 180, 325, 2145, 815   # crop box in original px (inside the scan's thin grey border)
OX, OY = 197, 342            # artwork origin in original px -> (0,0) in the SVGs
W, H = 1930, 456             # artwork size (original px)
SPLIT = 690                  # x (original px) between the mark and the wordmark
INK, WHITE = '#111111', '#ffffff'
GRAD = ('<linearGradient id="mi-silver" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="192.1" y2="537.2">'
        '<stop offset="0" stop-color="#efefef"/><stop offset="1" stop-color="#989898"/></linearGradient>')


def trace():
    im = Image.open(SRC).convert('L').crop((CX, CY, CX1, CY1))
    im = im.resize((im.width * S, im.height * S), Image.LANCZOS)
    a = np.array(im).astype(float)
    split = (SPLIT - CX) * S
    out = {}
    with tempfile.TemporaryDirectory() as td:
        for name, sl, th in (('mark', slice(0, split), 95), ('word', slice(split, None), 128)):
            b = np.full(a.shape, 255, np.uint8)
            b[:, sl][a[:, sl] > th] = 0
            png, svg = os.path.join(td, name + '.png'), os.path.join(td, name + '.svg')
            Image.fromarray(b).save(png)
            vtracer.convert_image_to_svg_py(png, svg, colormode='binary', mode='spline', filter_speckle=8,
                                            corner_threshold=60, length_threshold=15.0, splice_threshold=45, path_precision=3)
            ds = []
            for d, tx, ty in re.findall(r'<path d="([^"]*)" fill="#000000" transform="translate\(([-\d.e]+),([-\d.e]+)\)"', open(svg).read()):
                tx, ty = float(tx), float(ty)
                fix = lambda m: f'{(float(m.group(1)) + tx) / S + CX - OX:.3f} {(float(m.group(2)) + ty) / S + CY - OY:.3f}'
                ds.append(simp(re.sub(r'\s*([MCZL])\s*', r'\1', re.sub(r'([-\d.e]+)[ ,]([-\d.e]+)', fix, d)).strip()))
            out[name] = ''.join(ds)
    return out


def svg_doc(vb, body, w=None, h=None, title='Makers Inspire'):
    size = f' width="{w}" height="{h}"' if w else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"{size} role="img" aria-label="{title}">'
            f'<title>{title}</title>{body}</svg>\n')


# 16px pixel-grid version of the MI square for the tab icon (favicon.svg + the 16px ICO frame):
# the traced mark's 1-2px strokes blur at 16px, so this redraws it on whole pixels (frame, top-left notch, M, I).
FAV16 = """
................
.##############.
.#............#.
..............#.
.#.##...##.##.#.
.#.###.###.##.#.
.#.#######.##.#.
.#.##.#.##.##.#.
.#.##...##.##.#.
.#.##...##.##.#.
.#.##...##.##.#.
.#.##...##.##.#.
.#............#.
.#............#.
.##############.
................""".split()


def fav16_svg():
    rects = ''
    for y, row in enumerate(FAV16):
        for m in re.finditer(r'#+', row):
            rects += f'<rect x="{m.start()}" y="{y}" width="{m.end() - m.start()}" height="1"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges">'
            '<defs><linearGradient id="s" gradientUnits="userSpaceOnUse" x1="1" y1="1" x2="6.8" y2="17.2">'
            '<stop offset="0" stop-color="#efefef"/><stop offset="1" stop-color="#9c9c9c"/></linearGradient></defs>'
            f'<rect width="16" height="16" rx="3" fill="#000" shape-rendering="auto"/><g fill="url(#s)">{rects}</g></svg>\n')


def main():
    p = trace()
    br = lambda *a: os.path.join(ROOT, 'brand', *a)
    LOGO_VB, MARK_VB = '-4 -6 1938 466', '-3 -4 455 455'
    mark = lambda fill: f'<path fill="{fill}" d="{p["mark"]}"/>'
    word = lambda fill: f'<path fill="{fill}" d="{p["word"]}"/>'
    files = {
        'logo-white': svg_doc(LOGO_VB, f'<defs>{GRAD}</defs>{mark("url(#mi-silver)")}{word(WHITE)}'),
        'logo-black': svg_doc(LOGO_VB, mark(INK) + word(INK)),
        'mark-silver': svg_doc(MARK_VB, f'<defs>{GRAD}</defs>{mark("url(#mi-silver)")}', title='MI'),
        'mark-white': svg_doc(MARK_VB, mark(WHITE), title='MI'),
        'mark-black': svg_doc(MARK_VB, mark(INK), title='MI'),
    }
    for n, s in files.items():
        open(br(n + '.svg'), 'w').write(s)
        vb = [float(x) for x in (LOGO_VB if n.startswith('logo') else MARK_VB).split()]
        for k in (2, 3):
            hh = 48 * k
            cairosvg.svg2png(bytestring=s.encode(), write_to=br(f'{n}@{k}x.png'), output_height=hh, output_width=round(hh * vb[2] / vb[3]))

    # Icons: silver mark on black. Mark spans 56% of the icon so it sits inside the maskable safe zone.
    def icon(size, frac=0.56, rx=0):
        m = size * frac; o = (size - m) / 2; sc = m / 449
        bg = f'<rect width="{size}" height="{size}" rx="{rx}" fill="#000"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}"><defs>{GRAD}</defs>{bg}'
                f'<g transform="translate({o:.2f} {o:.2f}) scale({sc:.5f})">{mark("url(#mi-silver)")}</g></svg>\n')
    fav = fav16_svg()                         # tab icon: pixel-grid mark, crisp at 16px (and 32/48 on hi-dpi)
    open(os.path.join(ROOT, 'favicon.svg'), 'w').write(fav)
    ico = [Image.open(io.BytesIO(cairosvg.svg2png(bytestring=(fav if s == 16 else icon(s, frac=0.78, rx=s * 0.19)).encode(),
                                                   output_width=s, output_height=s))).convert('RGBA') for s in (16, 32, 48)]
    ico[2].save(os.path.join(ROOT, 'favicon.ico'), format='ICO', sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    for name, s, fr in (('apple-touch-icon.png', 180, 0.62), ('icon-192.png', 192, 0.56), ('icon-512.png', 512, 0.56)):
        cairosvg.svg2png(bytestring=icon(s, fr).encode(), write_to=os.path.join(ROOT, name), output_width=s, output_height=s)

    # Share image: white/silver logo centred on black, with a thin stone-and-metal accent line.
    lw = 760; lh = lw * 466 / 1938
    og = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630"><defs>{GRAD}'
          '<linearGradient id="acc" x1="0" x2="1"><stop offset="0" stop-color="#f4ddd6"/><stop offset=".34" stop-color="#e6d6ee"/>'
          '<stop offset=".67" stop-color="#d5e8ea"/><stop offset="1" stop-color="#f1e3c4"/></linearGradient></defs>'
          '<rect width="1200" height="630" fill="#000"/>'
          f'<svg x="{(1200 - lw) / 2:.1f}" y="{(630 - lh) / 2 - 18:.1f}" width="{lw}" height="{lh:.1f}" viewBox="{LOGO_VB}">'
          f'{mark("url(#mi-silver)")}{word(WHITE)}</svg>'
          f'<rect x="420" y="{(630 + lh) / 2 + 26:.1f}" width="360" height="4" rx="2" fill="url(#acc)" opacity=".85"/></svg>')
    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=og.encode(), output_width=1200, output_height=630))).convert('RGB') \
        .save(os.path.join(ROOT, 'images', 'og-logo.png'), optimize=True)
    print('brand assets written')


if __name__ == '__main__':
    main()
