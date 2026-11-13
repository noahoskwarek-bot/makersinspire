#!/usr/bin/env python3
"""Rebuild every logo / icon / share-image file for the MI monogram brand (Nov 2026 booth redesign).

Needs: pip install cairosvg pillow numpy fonttools   (e.g. in a venv; the site build itself doesn't need these)
Also needs Jost (variable TTF, OFL) on disk: set JOST_TTF=/path/to/Jost-VariableFont_wght.ttf if it isn't found.
Run from the repo root:  python3 tools/make_brand.py

Source: brand/mi-monogram-source.png (Noah's black "MI" on white, 1254 px). The monogram is pure geometry
(three stems + two diagonals), so instead of tracing it, MI_POLY below redraws it as exact polygons measured
from the source (stems 49 units, artwork 558 x 346 units). The "MAKERS INSPIRE" wordmark is Jost Light (Regular in the small
header lockup), widely tracked, converted to outlines so the SVGs need no font.

Outputs (committed; build.py only references them):
  brand/logo-black.svg / logo-white.svg     horizontal lockup (MI + wordmark), transparent: header + footer / dark areas
  brand/logo-stacked-black.svg / -white.svg stacked lockup (MI over wordmark), as on the booth banner
  brand/mark-black.svg / mark-white.svg     MI alone
  brand/*@2x.png, brand/*@3x.png            PNG fallbacks (1x = 48 px tall), transparent
  brand/sprig.svg                           line-art leaf sprig (decorative, like the booth banner)
  favicon.svg, favicon.ico (16/32/48), apple-touch-icon.png (180), icon-192.png, icon-512.png
  (the 1200x630 share image is rendered from the live hero by tools/make_og.py)
"""
import glob, io, os
import cairosvg
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INK, WHITE, IVORY, CREAM, OAK, OAK_D, GOLD, LEAF = '#111111', '#ffffff', '#f8f4ec', '#efe6d6', '#d9bc93', '#c7a476', '#b39256', '#6f7d5c'

# MI monogram, 558 x 346 units (measured from brand/mi-monogram-source.png, symmetrised).
MI_W, MI_H = 558, 346
MI_POLY = ('M0 0H56L229 207L402 0H458V346H409V65L229 279L49 65V346H0Z'   # M
           'M510 0H558V346H510Z')                                         # I


def mi(fill, x=0, y=0, h=MI_H):
    s = h / MI_H
    return f'<path transform="translate({x:.2f} {y:.2f}) scale({s:.5f})" fill="{fill}" d="{MI_POLY}"/>'


def jost_font(wght=300):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    cands = [os.environ.get('JOST_TTF', '')] + glob.glob('/usr/share/fonts/**/Jost-VariableFont_wght.ttf', recursive=True) \
        + glob.glob(os.path.expanduser('~/.fonts/**/Jost*wght*.ttf'), recursive=True)
    path = next((c for c in cands if c and os.path.exists(c)), None)
    if not path:
        raise SystemExit('Jost variable TTF not found: set JOST_TTF')
    f = TTFont(path)
    return instancer.instantiateVariableFont(f, {'wght': wght}) if 'fvar' in f else f


def text_path(font, text, tracking=0.34):
    """Outline `text` in `font`. Returns (d, width, cap_height) in font units with y down, baseline at cap height."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    gs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm
    cap = font['OS/2'].sCapHeight or int(upm * 0.7)
    x, ds, n = 0, [], len(text)
    for i, ch in enumerate(text):
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (1, 0, 0, -1, x, cap)))
        ds.append(pen.getCommands())
        x += gs[g].width + (tracking * upm if i < n - 1 else 0)
    return ''.join(ds), x, cap


def svg_doc(w, h, body, title='Makers Inspire'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{body}</svg>\n')


def lockups(font, font_small):
    d, tw, cap = text_path(font, 'MAKERS INSPIRE')
    hd, htw, hcap = text_path(font_small, 'MAKERS INSPIRE', 0.30)  # header size: a touch heavier so it stays legible
    # horizontal: MI 346 tall; wordmark caps 0.30 x MI height, vertically centred; gap 0.42 x MI height
    hc = MI_H * 0.30; ts = hc / hcap; gap = MI_H * 0.42
    hw = MI_W + gap + htw * ts
    horiz = lambda c: svg_doc(hw, MI_H, mi(c) + f'<path transform="translate({MI_W + gap:.2f} {(MI_H - hc) / 2:.2f}) scale({ts:.5f})" fill="{c}" d="{hd}"/>')
    # stacked (booth banner): wordmark 2.25 x MI width, gap 0.30 x MI height
    sw = MI_W * 2.25; ss = sw / tw; sc = cap * ss; sg = MI_H * 0.30
    sh = MI_H + sg + sc
    stacked = lambda c: svg_doc(sw, sh, mi(c, (sw - MI_W) / 2, 0) + f'<path transform="translate(0 {MI_H + sg:.2f}) scale({ss:.5f})" fill="{c}" d="{d}"/>')
    mark = lambda c: svg_doc(MI_W, MI_H, mi(c), 'MI')
    return dict(horiz=horiz, stacked=stacked, mark=mark, sizes=dict(horiz=(hw, MI_H), stacked=(sw, sh), mark=(MI_W, MI_H)),
                word=(d, tw, cap))


SPRIG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M22 108C44 82 62 58 98 14"/>'
         '<path d="M44 82C30 80 22 70 20 58C34 58 44 68 44 82Z"/><path d="M44 82C56 76 62 64 60 52C48 58 42 70 44 82Z"/>'
         '<path d="M60 62C48 58 42 48 42 36C54 38 62 48 60 62Z"/><path d="M60 62C72 58 78 46 78 34C66 38 58 50 60 62Z"/>'
         '<path d="M76 42C66 36 62 26 64 16C74 20 80 30 76 42Z"/><path d="M76 42C88 40 96 32 98 22C86 22 78 30 76 42Z"/>'
         '<path d="M32 96C20 98 10 92 6 82C18 80 28 86 32 96Z"/></svg>\n')


def main():
    L = lockups(jost_font(300), jost_font(400))
    b = lambda *p: os.path.join(ROOT, 'brand', *p)
    files = {'logo-black': L['horiz'](INK), 'logo-white': L['horiz'](WHITE),
             'logo-stacked-black': L['stacked'](INK), 'logo-stacked-white': L['stacked'](WHITE),
             'mark-black': L['mark'](INK), 'mark-white': L['mark'](WHITE)}
    for name, svg in files.items():
        open(b(name + '.svg'), 'w').write(svg)
        kind = 'horiz' if name.startswith('logo-') and 'stacked' not in name else ('stacked' if 'stacked' in name else 'mark')
        w, h = L['sizes'][kind]
        for k in (2, 3):
            ph = 48 * k
            cairosvg.svg2png(bytestring=svg.encode(), write_to=b(f'{name}@{k}x.png'), output_height=ph, output_width=round(ph * w / h))
    open(b('sprig.svg'), 'w').write(SPRIG.format(c=LEAF))

    # Icons: black MI centred on an ivory rounded square (reads in light and dark browser tabs).
    def icon(s, frac, radius=0.22, square=False):
        mh = s * frac * MI_H / MI_W
        r = 0 if square else s * radius
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}"><rect width="{s}" height="{s}" rx="{r:.1f}" fill="{IVORY}"/>'
                f'{mi(INK, (s - s * frac) / 2, (s - mh) / 2, mh)}</svg>')
    open(os.path.join(ROOT, 'favicon.svg'), 'w').write(icon(64, 0.74, 0.2) + '\n')
    # 16 px frame on whole pixels: 1px stems (I'd blur otherwise)
    fav16 = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges"><rect width="16" height="16" rx="3" fill="{IVORY}"/>'
             f'<g fill="{INK}"><rect x="2" y="4" width="2" height="8"/><rect x="9" y="4" width="2" height="8"/><rect x="12" y="4" width="2" height="8"/>'
             '<rect x="4" y="5" width="1" height="2"/><rect x="5" y="6" width="1" height="2"/><rect x="6" y="7" width="1" height="2"/>'
             '<rect x="7" y="6" width="1" height="2"/><rect x="8" y="5" width="1" height="2"/></g></svg>')
    ico = [Image.open(io.BytesIO(cairosvg.svg2png(bytestring=fav16.encode(), output_width=16, output_height=16))).convert('RGBA')]
    ico += [Image.open(io.BytesIO(cairosvg.svg2png(bytestring=icon(s, 0.74, 0.2).encode(), output_width=s, output_height=s))).convert('RGBA') for s in (32, 48)]
    ico[2].save(os.path.join(ROOT, 'favicon.ico'), format='ICO', sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    for name, s, fr in (('apple-touch-icon.png', 180, 0.62), ('icon-192.png', 192, 0.56), ('icon-512.png', 512, 0.56)):
        cairosvg.svg2png(bytestring=icon(s, fr, square=True).encode(), write_to=os.path.join(ROOT, name), output_width=s, output_height=s)

    print('brand assets written')


if __name__ == '__main__':
    main()
