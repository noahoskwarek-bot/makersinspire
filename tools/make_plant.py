#!/usr/bin/env python3
"""Draw brand/plant.svg: a potted olive/eucalyptus tree in a woven basket, used twice in the home-page hero
(one on each side of the slatted oak arch, standing on the jute rug). Pure vector, no fonts or images.
Run from the repo root:  python3 tools/make_plant.py   (no extra packages needed)
Leaves are placed with a fixed random seed, so the output is the same every run.
"""
import math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = random.Random(7)
GREENS = ['#4f5e45', '#5d6d50', '#6f7d5c', '#7f8f6a', '#93a17e', '#a7b393']
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



W, H, CX, BASE = 200, 380, 100, 322


def main():
    st, ls = olive_tree(CX, BASE, 290)
    body = f'<g fill="none">{st}</g>' + ''.join(''.join(l) for l in ls) + basket(CX, BASE, 86, 58)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="26 22 148 358" aria-hidden="true">{body}</svg>\n')
    open(os.path.join(ROOT, 'brand', 'plant.svg'), 'w').write(svg)
    print('brand/plant.svg', len(svg), 'bytes')


if __name__ == '__main__':
    main()
