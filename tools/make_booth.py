#!/usr/bin/env python3
"""Draw brand/booth.svg: the home-page hero illustration of the Makers Inspire market booth.

Needs the same tools as make_brand.py (fonttools + the Jost TTF, for the sign's wordmark outlines).
Run from the repo root:  python3 tools/make_booth.py
Pure vector, no fonts or images: slatted light-oak arch with the round MI sign and a draped eucalyptus garland,
cream side arches, potted olive trees in woven baskets, a linen-draped table with neck busts, gold necklaces,
a gold bar rack with chains, wood trays of rings and earrings, a vase of white flowers, and a jute rug.
Leaves are placed with a fixed random seed, so the output is the same every run.
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_brand import MI_POLY, MI_W, MI_H, jost_font, text_path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 800, 560
R = random.Random(7)
GREENS = ['#4f5e45', '#5d6d50', '#6f7d5c', '#7f8f6a', '#93a17e', '#a7b393']
GOLD, GOLD_L, OAK, OAK_L, OAK_D, CREAM, LINEN, IVORY = '#b39256', '#d4b97c', '#d9bc93', '#e6cfab', '#c4a072', '#efe6d6', '#fbf8f2', '#f8f4ec'
f = lambda v: f'{v:.1f}'.rstrip('0').rstrip('.')


def leaf(x, y, ang, ln, wd, col, vein=False):
    """Almond leaf from (x, y) pointing at angle ang (deg)."""
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    P = lambda u, v: (x + u * c - v * s, y + u * s + v * c)
    tip, c1, c2, c3, c4 = P(ln, 0), P(ln * .3, wd), P(ln * .8, wd * .55), P(ln * .8, -wd * .55), P(ln * .3, -wd)
    i = lambda v: str(round(v))
    d = (f'M{i(x)} {i(y)}C{i(c1[0])} {i(c1[1])} {i(c2[0])} {i(c2[1])} {i(tip[0])} {i(tip[1])}'
         f'C{i(c3[0])} {i(c3[1])} {i(c4[0])} {i(c4[1])}Z')
    out = f'<path fill="{col}" d="{d}"/>'
    if vein:
        m = P(ln * .85, 0)
        out += f'<path d="M{i(x)} {i(y)}L{i(m[0])} {i(m[1])}" stroke="#fff" stroke-opacity=".3" stroke-width=".6"/>'
    return out


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def garland_strand(pts, n, size, spread, per=2, wr=(.36, .5)):
    """Leaves along a cubic bezier (list of 4 points). Returns (stem path, leaves by depth layer)."""
    layers = [[] for _ in range(3)]
    for i in range(n):
        t = i / (n - 1)
        x, y = bez(*pts, t)
        x2, y2 = bez(*pts, min(1, t + .01))
        tang = math.degrees(math.atan2(y2 - y, x2 - x))
        for side in (-1, 1):
            for k in range(per):
                layer = R.choice((0, 1, 1, 2))
                col = GREENS[[R.choice((0, 1, 2)), R.choice((1, 2, 3)), R.choice((3, 4, 5))][layer]]
                ang = tang + side * R.uniform(35, 80) + R.uniform(-12, 12)
                ln = size * R.uniform(.75, 1.25) * (1 - .25 * layer / 2)
                layers[layer].append(leaf(x + R.uniform(-spread, spread), y + R.uniform(-spread, spread), ang, ln, ln * R.uniform(*wr), col, layer == 2))
    p0, p1, p2, p3 = pts
    stem = f'<path d="M{f(p0[0])} {f(p0[1])}C{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])} {f(p3[0])} {f(p3[1])}" stroke="#5d6d50" stroke-width="1.4"/>'
    return stem, layers


def olive_tree(cx, base, height, flip=1):
    """Potted olive/eucalyptus: a few branches from the basket with small narrow leaves."""
    layers = [[] for _ in range(3)]; stems = []
    for b in range(9):
        top_x = cx + flip * R.uniform(-40, 40) + (b - 4) * 8
        top_y = base - height * R.uniform(.62, 1.0)
        p0 = (cx + R.uniform(-6, 6), base); p3 = (top_x, top_y)
        p1 = (cx + R.uniform(-10, 10), base - height * .35); p2 = (top_x + R.uniform(-15, 15), top_y + height * .25)
        stems.append(f'<path d="M{f(p0[0])} {f(p0[1])}C{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])} {f(p3[0])} {f(p3[1])}" stroke="#6b5a43" stroke-width="1.3"/>')
        for i in range(20):
            t = .25 + .75 * i / 19
            x, y = bez(p0, p1, p2, p3, t)
            for side in (-1, 1):
                layer = R.choice((0, 1, 1, 2))
                col = GREENS[[R.choice((0, 1)), R.choice((1, 2, 3)), R.choice((3, 4, 5))][layer]]
                ang = -90 + side * R.uniform(25, 75) + (top_x - cx) * .25
                ln = R.uniform(11, 17)
                layers[layer].append(leaf(x, y, ang, ln, ln * .27, col))
    return ''.join(stems), layers


def basket(cx, top, w, h):
    x0, x1 = cx - w / 2, cx + w / 2
    body = (f'<path d="M{f(x0)} {f(top)}H{f(x1)}L{f(x1 - w * .1)} {f(top + h)}H{f(x0 + w * .1)}Z" fill="#c9a979"/>')
    weave = ''.join(f'<path d="M{f(x0 + w * .1 * (k / h))} {f(top + k)}H{f(x1 - w * .1 * (k / h))}" stroke="#a88a5c" stroke-width="2" stroke-dasharray="5 3" stroke-dashoffset="{(k // 6) % 2 * 4}"/>'
                    for k in range(7, int(h) - 2, 6))
    rim = f'<rect x="{f(x0 - 3)}" y="{f(top - 5)}" width="{f(w + 6)}" height="9" rx="4" fill="#b8996a"/>'
    return body + weave + rim


def bust(cx, base, s=1.0):
    """Cream neck bust on a small oak base, with a delicate gold necklace and pendant."""
    h = 92 * s; nw = 13 * s; sw = 38 * s
    top = base - h
    shape = (f'<path fill="{LINEN}" stroke="#e0d4bf" stroke-width="1" d="M{f(cx - nw)} {f(top)}H{f(cx + nw)}V{f(top + h * .38)}'
             f'C{f(cx + nw + 4 * s)} {f(top + h * .46)} {f(cx + sw)} {f(top + h * .5)} {f(cx + sw)} {f(top + h * .64)}'
             f'C{f(cx + sw * .55)} {f(top + h * .8)} {f(cx + nw * .8)} {f(top + h * .86)} {f(cx + nw * .8)} {f(base - 10 * s)}'
             f'H{f(cx - nw * .8)}C{f(cx - nw * .8)} {f(top + h * .86)} {f(cx - sw * .55)} {f(top + h * .8)} {f(cx - sw)} {f(top + h * .64)}'
             f'C{f(cx - sw)} {f(top + h * .5)} {f(cx - nw - 4 * s)} {f(top + h * .46)} {f(cx - nw)} {f(top + h * .38)}Z"/>'
             f'<ellipse cx="{f(cx)}" cy="{f(top)}" rx="{f(nw)}" ry="{f(3 * s)}" fill="#f1e9da"/>')
    stand = f'<rect x="{f(cx - 20 * s)}" y="{f(base - 10 * s)}" width="{f(40 * s)}" height="{f(10 * s)}" rx="2" fill="{OAK}"/>'
    ny = top + h * .4
    neck = (f'<path d="M{f(cx - nw - 1)} {f(ny)}Q{f(cx)} {f(ny + 34 * s)} {f(cx + nw + 1)} {f(ny)}" stroke="{GOLD}" stroke-width="{f(1.1 * s)}" fill="none"/>'
            f'<path d="M{f(cx - nw - 2)} {f(ny - 4)}Q{f(cx)} {f(ny + 20 * s)} {f(cx + nw + 2)} {f(ny - 4)}" stroke="{GOLD_L}" stroke-width="{f(.9 * s)}" fill="none"/>'
            f'<path d="M{f(cx)} {f(ny + 17 * s)}l{f(-3.2 * s)} {f(4 * s)}l{f(3.2 * s)} {f(5 * s)}l{f(3.2 * s)} {f(-5 * s)}Z" fill="{GOLD}"/>'
            f'<circle cx="{f(cx)}" cy="{f(ny + 8 * s)}" r="{f(1.8 * s)}" fill="{GOLD}"/>')
    return shape + stand + neck


def rack(x0, x1, base, h):
    top = base - h
    posts = (f'<path d="M{f(x0)} {f(base)}V{f(top)}M{f(x1)} {f(base)}V{f(top)}M{f(x0 - 3)} {f(top)}H{f(x1 + 3)}" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
             f'<rect x="{f(x0 - 7)}" y="{f(base - 3)}" width="{f(x1 - x0 + 14)}" height="4" rx="2" fill="{OAK}"/>')
    chains = ''
    n = 5
    for i in range(n):
        x = x0 + (x1 - x0) * (i + .5) / n
        L = R.uniform(.45, .8) * h
        chains += f'<path d="M{f(x - 2.2)} {f(top + 1)}Q{f(x)} {f(top + L * 2)} {f(x + 2.2)} {f(top + 1)}" stroke="{GOLD_L if i % 2 else GOLD}" stroke-width="1" fill="none"/>'
        py = top + L
        chains += (f'<circle cx="{f(x)}" cy="{f(py + 2.6)}" r="2.6" fill="{GOLD}"/>' if i % 2 else
                   f'<path d="M{f(x)} {f(py)}l-2.6 3.4l2.6 4.2l2.6-4.2Z" fill="{GOLD}"/>')
    return posts + chains


def tray(x, y, w, kind):
    t = (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="9" rx="2" fill="{OAK}"/>'
         f'<rect x="{f(x + 3)}" y="{f(y + 2)}" width="{f(w - 6)}" height="4" rx="1" fill="{LINEN}"/>')
    if kind == 'rings':
        t += ''.join(f'<circle cx="{f(x + 8 + k * (w - 16) / 4)}" cy="{f(y - 2)}" r="4.4" fill="none" stroke="{GOLD if k % 2 else GOLD_L}" stroke-width="1.9"/>' for k in range(5))
        t += f'<circle cx="{f(x + 8 + 2 * (w - 16) / 4)}" cy="{f(y - 6.6)}" r="2" fill="#fff" stroke="#cfd6dc" stroke-width=".6"/>'
    else:  # earrings on a little card stand
        t += f'<rect x="{f(x + 6)}" y="{f(y - 18)}" width="{f(w - 12)}" height="18" rx="1.5" fill="#fff" stroke="#e5dccb" stroke-width=".8"/>'
        for k in range(3):
            ex = x + 12 + k * (w - 24) / 2
            t += (f'<path d="M{f(ex)} {f(y - 14)}v4" stroke="{GOLD}" stroke-width=".9"/><path d="M{f(ex)} {f(y - 10)}l-2.4 3.5l2.4 3.5l2.4-3.5Z" fill="{GOLD}"/>')
    return t


def flowers(cx, base, z=1.0):
    g0 = len('')
    vase = (f'<path d="M{f(cx - 11)} {f(base)}C{f(cx - 17)} {f(base - 14)} {f(cx - 13)} {f(base - 26)} {f(cx - 6)} {f(base - 30)}'
            f'H{f(cx + 6)}C{f(cx + 13)} {f(base - 26)} {f(cx + 17)} {f(base - 14)} {f(cx + 11)} {f(base)}Z" fill="#ece3d3" stroke="#dacdb6" stroke-width=".8"/>')
    out = ''
    for k in range(9):
        out += leaf(cx + R.uniform(-6, 6), base - 30, -90 + R.uniform(-70, 70), R.uniform(10, 15), 3.5, R.choice(GREENS[2:5]))
    blooms = ''
    for k in range(14):
        bx, by = cx + R.uniform(-22, 22), base - 38 - R.uniform(0, 24)
        r = R.uniform(4.5, 7)
        blooms += ''.join(f'<circle cx="{f(bx + math.cos(a) * r * .55)}" cy="{f(by + math.sin(a) * r * .55)}" r="{f(r * .55)}" fill="#fff" stroke="#e8e1d4" stroke-width=".5"/>'
                          for a in [i * 2 * math.pi / 5 + k for i in range(5)])
        blooms += f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(r * .3)}" fill="#efe4c4"/>'
    body = out + blooms + vase
    return f'<g transform="translate({f(cx)} {f(base)}) scale({z}) translate({f(-cx)} {f(-base)})">{body}</g>'


def main():
    o = []
    font = jost_font(300)
    d, tw, cap = text_path(font, 'MAKERS INSPIRE')
    # back: cream side arches + slatted oak arch
    o.append(f'<path fill="{CREAM}" d="M95 540V250A100 100 0 0 1 295 250V540Z"/><path fill="{CREAM}" d="M505 540V250A100 100 0 0 1 705 250V540Z"/>')
    o.append('<path fill="#000" fill-opacity=".03" d="M95 540V250A100 100 0 0 1 125 179V540Z"/>')
    o.append(f'<clipPath id="oak"><path d="M250 540V200A150 150 0 0 1 550 200V540Z"/></clipPath>')
    slats = ''.join(f'<rect x="{x}" y="40" width="5" height="440" fill="{OAK_D}" opacity=".55"/><rect x="{x + 5}" y="40" width="2" height="440" fill="{OAK_L}" opacity=".7"/>' for x in range(250, 552, 12))
    o.append(f'<g clip-path="url(#oak)"><rect x="240" y="40" width="320" height="440" fill="{OAK}"/>{slats}'
             f'<rect x="240" y="40" width="320" height="440" fill="url(#shade)"/></g>')
    # round sign
    sw = MI_W * 2.25; sh = MI_H + MI_H * .30 + cap * (sw / tw)
    lw = 120; s = lw / sw; lx, ly = 400 - lw / 2, 222 - sh * s / 2
    o.append(f'<circle cx="400" cy="222" r="84" fill="#000" fill-opacity=".06" transform="translate(2 6)"/><circle cx="400" cy="222" r="84" fill="#fff"/>'
             f'<circle cx="400" cy="222" r="77" fill="none" stroke="{GOLD}" stroke-width="1.2"/>'
             f'<g transform="translate({f(lx)} {f(ly)}) scale({s:.5f})" fill="#111"><path transform="translate({f((sw - MI_W) / 2)} 0)" d="{MI_POLY}"/>'
             f'<path transform="translate(0 {f(MI_H * 1.3)}) scale({sw / tw:.5f})" d="{d}"/></g>')
    # garland: over the arch top, trailing down both sides (three strands for fullness)
    strands = [((228, 300), (232, 150), (300, 40), (400, 48)), ((572, 300), (568, 150), (500, 40), (400, 48)),
               ((240, 232), (262, 120), (330, 70), (400, 72)), ((560, 232), (538, 120), (470, 70), (400, 72)),
               ((262, 156), (250, 230), (226, 300), (236, 350)), ((538, 156), (550, 230), (574, 300), (564, 350)),
               ((300, 96), (296, 130), (288, 170), (282, 210)), ((500, 96), (504, 130), (512, 170), (518, 210)),
               ((355, 62), (352, 82), (348, 100), (344, 118)), ((445, 62), (448, 82), (452, 100), (456, 118))]
    stems, layers = [], [[], [], []]
    for i, pts in enumerate(strands):
        st, ls = garland_strand(pts, 34 if i < 4 else (16 if i < 6 else 9), 18 if i < 4 else 14, 7 if i < 4 else 4, 3 if i < 4 else 2)
        stems.append(st); [layers[k].extend(ls[k]) for k in range(3)]
    # potted olive trees in woven baskets (behind the table edges)
    tree = []
    for cx, flip in ((70, 1), (730, -1)):
        st, ls = olive_tree(cx, 482, 290, flip)
        tree.append((st, ls, cx))
    for st, ls, cx in tree:
        o.append(f'<g fill="none">{st}</g>' + ''.join(''.join(l) for l in ls))
        o.append(basket(cx, 482, 86, 58))
    o.append(f'<g fill="none">{"".join(stems)}</g>' + ''.join(''.join(l) for l in layers))
    # jute rug
    o.append('<path fill="url(#jute)" d="M40 540H760L780 556H20Z"/><path fill="#c9b48e" d="M20 556H780V560H20Z"/>')
    # table with linen drape
    o.append(f'<path fill="{LINEN}" d="M178 398H622L632 540H168Z"/><path fill="#fff" d="M172 394H628V402H172Z"/>'
             + ''.join(f'<path d="M{x} 404Q{x + 3} 470 {x - 2 + (x - 400) * .03:.1f} 538" stroke="#e8dfcf" stroke-width="1.2" fill="none"/>' for x in range(200, 620, 34))
             + f'<rect x="352" y="440" width="96" height="62" fill="#fff" stroke="#ece4d6"/>'
             f'<path transform="translate(380 459) scale({40 / MI_W:.5f})" fill="#111" d="{MI_POLY}"/>')
    # jewelry on the table
    o.append(bust(222, 394, 1.42) + bust(580, 394, 1.3))
    o.append(rack(266, 330, 394, 84))
    o.append(tray(340, 384, 44, 'rings') + tray(428, 384, 52, 'rings') + tray(488, 384, 48, 'earrings'))
    o.append(flowers(400, 394, 1.25))
    defs = ('<defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".12"/>'
            '<stop offset="1" stop-color="#7a5a30" stop-opacity=".16"/></linearGradient>'
            '<pattern id="jute" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#d9c6a3"/>'
            '<path d="M0 6L6 0M-1 1L1 -1M5 7L7 5" stroke="#c4ad85" stroke-width="1.2"/></pattern></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Illustration of the Makers Inspire market booth">'
           f'<title>Illustration of the Makers Inspire market booth</title>{defs}{"".join(o)}</svg>\n')
    open(os.path.join(ROOT, 'brand', 'booth.svg'), 'w').write(svg)
    print('brand/booth.svg', len(svg), 'bytes')


if __name__ == '__main__':
    main()
