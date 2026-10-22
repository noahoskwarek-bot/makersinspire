#!/usr/bin/env python3
"""Static site generator for makersinspire.com (GitHub Pages, main branch root).

Edit site.json, pieces.json, services.json (or src/style.css, src/site.js), then:
    python3 build.py            # write all generated files
    python3 build.py --check    # exit 1 if anything is out of date (run before committing)
BUILD_DATE=YYYY-MM-DD pins the sitemap date (default: today). See README.md.
"""
import datetime
import html
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DATE = os.environ.get('BUILD_DATE') or datetime.date.today().isoformat()
e = lambda t: html.escape(str(t), quote=True)

# Soft accent palette drawn from stones and metals: rose quartz, amethyst, aquamarine, citrine, gold-fill.
PALETTES = [('#f4ddd6', '#e6d6ee', '#d5e8ea'), ('#e9e0f1', '#f3e3c7', '#f4dcd9'), ('#d9ebe6', '#e4dcef', '#f2e6cc'),
            ('#f1e4cc', '#f2d9d9', '#dde4f0'), ('#f0dccb', '#e7d5c4', '#f5e9dc'), ('#e4e7ea', '#e9dff0', '#f3e7d3')]


def load(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return json.load(f)


def load_all():
    site = load('site.json')
    pieces = [p for p in load('pieces.json')['pieces'] if p.get('show', True)]
    services = load('services.json')['services']
    slugs = [p['slug'] for p in pieces]
    assert len(set(slugs)) == len(slugs), 'duplicate piece slugs in pieces.json'
    man = load_manifest()
    for i, p in enumerate(pieces):
        p['_pal'] = PALETTES[i % len(PALETTES)]
        entries = photo_entries(p)
        n = len(entries)
        imgs = []
        for k, ent in enumerate(entries):
            alt = (ent.get('alt') or '').strip() or f'{p["name"]}, photo {k + 1} of {n}'
            if ent.get('file'):
                m = man.get(f'{p["slug"]}/{ent["file"]}')
                if not m:
                    sys.exit(f'photo {p["slug"]}/{ent["file"]} has not been processed yet: run python3 build.py (without --check) where photos/ exists')
                imgs.append(dict(m, alt=alt, placeholder=False, key=f'{p["slug"]}/{ent["file"]}'))
            else:  # an already-hosted image path or URL, used as-is
                imgs.append({'src': ent['src'], 'alt': alt, 'placeholder': False, 'w': ent.get('width'), 'h': ent.get('height')})
        if not imgs:
            n = max(1, int(p.get('placeholder_images') or 1))
            imgs = [{'src': f'/images/placeholders/{p["slug"]}-{k + 1}.svg', 'placeholder': True, 'w': 800, 'h': 800,
                     'alt': f'Placeholder photo {k + 1} of {n} for {p["name"]}'} for k in range(n)]
        p['_imgs'] = imgs
    return site, pieces, services


# ---------- real photos: photos/<slug>/<file> -> images/pieces/<slug>/<name>-<width>.webp/.jpg ----------
PHOTO_DIR = os.path.join(ROOT, 'photos')            # originals (gitignored: they can carry GPS/EXIF and are large)
OUT_DIR = os.path.join(ROOT, 'images', 'pieces')    # generated, committed, published
MANIFEST = os.path.join(OUT_DIR, 'manifest.json')   # source hash + sizes, so builds work without the originals
WIDTHS = (160, 320, 480, 800, 1200, 1600)  # 160/320 serve thumbnails and phone grid cards
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.webp')


def photo_entries(p):
    """The piece's photos in order: pieces.json "images" if given, else every photo in photos/<slug>/ sorted by file name."""
    listed = [im for im in p.get('images', []) if im.get('file') or im.get('src')]
    if listed:
        return listed
    d = os.path.join(PHOTO_DIR, p['slug'])
    if os.path.isdir(d):
        return [{'file': f} for f in sorted(os.listdir(d), key=str.lower) if f.lower().endswith(PHOTO_EXT) and not f.startswith('.')]
    man = load_manifest()  # originals not on this computer: fall back to what was processed before
    return [{'file': k.split('/', 1)[1]} for k in sorted(man, key=str.lower) if k.startswith(p['slug'] + '/')]


def load_manifest():
    return json.load(open(MANIFEST, encoding='utf-8')) if os.path.exists(MANIFEST) else {}


def photo_variants(slug, file, w, h):
    stem = re.sub(r'[^a-z0-9]+', '-', os.path.splitext(file)[0].lower()).strip('-') or 'photo'
    ws = sorted(set([x for x in WIDTHS if x < w] + [min(w, WIDTHS[-1])]))
    return [(x, round(h * x / w), f'/images/pieces/{slug}/{stem}-{x}') for x in ws]


def encode_photo(src, slug, file):
    """Resize one original into every width as WebP + JPEG. EXIF/GPS and other metadata are dropped (the pixels are
    re-encoded with no exif/xmp), orientation is applied first, and colours are converted to sRGB."""
    from PIL import Image, ImageOps, ImageCms
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    icc = im.info.get('icc_profile')
    if icc:
        try:
            im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), outputMode='RGB')
        except Exception:
            pass
    if im.mode not in ('RGB',):
        bg = Image.new('RGB', im.size, (255, 255, 255))
        im = im.convert('RGBA'); bg.paste(im, mask=im.split()[3]); im = bg
    w, h = im.size
    out = []
    for x, y, base in photo_variants(slug, file, w, h):
        r = im if x == w else im.resize((x, y), Image.LANCZOS)
        path = os.path.join(ROOT, base.lstrip('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        r.save(path + '.webp', 'WEBP', quality=80, method=6)
        r.save(path + '.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
        out.append(base)
    return w, h


def process_photos(pieces_all, check):
    """Make/refresh responsive images for every photo. Returns (manifest, stale list)."""
    import hashlib
    man, stale, want = load_manifest(), [], set()
    for p in pieces_all:
        for ent in photo_entries(p):
            if not ent.get('file'):
                continue
            key = f'{p["slug"]}/{ent["file"]}'
            want.add(key)
            src = os.path.join(PHOTO_DIR, p['slug'], ent['file'])
            if not os.path.exists(src):
                if key not in man:
                    sys.exit(f'missing photo: photos/{key}')
                continue  # original not on this computer; keep the processed copy
            sha = hashlib.sha1(open(src, 'rb').read()).hexdigest()
            m = man.get(key)
            if m and m['sha1'] == sha and m['bases'] == [b for _, _, b in photo_variants(p['slug'], ent['file'], m['w'], m['h'])] and all(os.path.exists(os.path.join(ROOT, b.lstrip('/') + ext)) for b in m['bases'] for ext in ('.webp', '.jpg')):
                continue
            if check:
                stale.append(f'images/pieces/{key} (photo)'); continue
            w, h = encode_photo(src, p['slug'], ent['file'])
            man[key] = {'sha1': sha, 'w': w, 'h': h, 'bases': [b for _, _, b in photo_variants(p['slug'], ent['file'], w, h)]}
            print('processed photo', key)
    for k in [k for k in man if k not in want]:
        if check:
            stale.append(f'images/pieces/{k} (removed photo)'); continue
        for b in man.pop(k)['bases']:
            for ext in ('.webp', '.jpg'):
                f = os.path.join(ROOT, b.lstrip('/') + ext)
                if os.path.exists(f):
                    os.remove(f)
        print('removed photo', k)
    if not check:
        data = json.dumps(dict(sorted(man.items())), indent=1) + '\n'
        if man or os.path.exists(MANIFEST):
            os.makedirs(OUT_DIR, exist_ok=True)
            if not os.path.exists(MANIFEST) or open(MANIFEST, encoding='utf-8').read() != data:
                open(MANIFEST, 'w', encoding='utf-8').write(data)
        for dirpath, dirs, names in os.walk(OUT_DIR, topdown=False):
            if dirpath != OUT_DIR and not os.listdir(dirpath):
                os.rmdir(dirpath)
    return stale


def img_html(im, sizes, eager=False, priority=False, cls=''):
    """<picture> (WebP + JPEG srcset) for a processed photo, or a plain <img> for placeholders / hosted images.
    width/height are always set so nothing shifts while loading; below-the-fold images are lazy."""
    attrs = f' alt="{e(im["alt"])}"'
    if im.get('w') and im.get('h'):
        w = min(im['w'], WIDTHS[-1]) if 'bases' in im else im['w']  # the largest generated size (same shape as the original)
        attrs += f' width="{w}" height="{round(im["h"] * w / im["w"])}"'
    attrs += (' fetchpriority="high"' if priority else '') + ('' if eager else ' loading="lazy"') + ' decoding="async"'
    attrs += f' class="{cls}"' if cls else ''
    if 'bases' not in im:
        return f'<img src="{e(im["src"])}"{attrs}>'
    ws = [int(b.rsplit('-', 1)[1]) for b in im['bases']]
    jpg = ', '.join(f'{b}.jpg {w}w' for b, w in zip(im['bases'], ws))
    webp = ', '.join(f'{b}.webp {w}w' for b, w in zip(im['bases'], ws))
    dflt = next((b for b, w in zip(im['bases'], ws) if w >= 800), im['bases'][-1])
    return (f'<picture><source type="image/webp" srcset="{webp}" sizes="{sizes}">'
            f'<img src="{dflt}.jpg" srcset="{jpg}" sizes="{sizes}"{attrs}></picture>')


def full_src(im):
    """Largest version for the lightbox: (jpg src, webp srcset)."""
    if 'bases' not in im:
        return im['src'], ''
    ws = [int(b.rsplit('-', 1)[1]) for b in im['bases']]
    return im['bases'][-1] + '.jpg', ', '.join(f'{b}.webp {w}w' for b, w in zip(im['bases'], ws))


# ---------- placeholder images (clearly labelled) ----------
SHAPES = [
    # necklace curve + drop
    '<path d="M150 170 C 230 420, 570 420, 650 170" fill="none" stroke="#8a7f75" stroke-width="5" stroke-linecap="round" opacity=".55"/>'
    '<circle cx="400" cy="402" r="34" fill="#ffffff" opacity=".55"/><circle cx="400" cy="402" r="34" fill="none" stroke="#8a7f75" stroke-width="4" opacity=".55"/>',
    # pair of drops
    '<circle cx="330" cy="230" r="10" fill="#8a7f75" opacity=".5"/><path d="M330 240 L330 330" stroke="#8a7f75" stroke-width="4" opacity=".5"/>'
    '<ellipse cx="330" cy="380" rx="34" ry="50" fill="#fff" opacity=".55"/><circle cx="470" cy="230" r="10" fill="#8a7f75" opacity=".5"/>'
    '<path d="M470 240 L470 330" stroke="#8a7f75" stroke-width="4" opacity=".5"/><ellipse cx="470" cy="380" rx="34" ry="50" fill="#fff" opacity=".55"/>',
    # ring
    '<circle cx="400" cy="330" r="110" fill="none" stroke="#8a7f75" stroke-width="14" opacity=".45"/><circle cx="400" cy="214" r="34" fill="#fff" opacity=".6"/>',
    # beads
    ''.join(f'<circle cx="{170 + k * 66}" cy="{300 + int(60 * ((k - 3.5) ** 2) / 12)}" r="24" fill="#fff" opacity=".55"/>' for k in range(8)),
]


def placeholder_svg(p, k, n):
    a, b, c = p['_pal']
    shape = SHAPES[(k + len(p['slug'])) % len(SHAPES)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" role="img" aria-label="Placeholder photo">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset=".55" stop-color="{b}"/><stop offset="1" stop-color="{c}"/></linearGradient></defs>
<rect width="800" height="800" fill="url(#g)"/>{shape}
<rect x="250" y="640" width="300" height="56" rx="28" fill="#ffffff" opacity=".8"/>
<text x="400" y="676" text-anchor="middle" font-family="-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="24" letter-spacing="2" fill="#3b3631">PLACEHOLDER PHOTO</text>
<text x="400" y="112" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="#3b3631" opacity=".7">{k + 1} / {n}</text>
</svg>
'''


# ---------- page shell ----------
NAV = [('/shop/', 'Shop'), ('/about/', 'Our Story'), ('/commissions/', 'Commissions'), ('/services/', 'Services'), ('/contact/', 'Contact')]


def logo_img(site, key, cls, height):
    """<img> for a logo file from site.json (key "logo" = for light areas, "logo_dark" = for dark areas), or None.
    width/height come from the SVG viewBox so the header doesn't shift while it loads."""
    src = site.get(key)
    if not src:
        return None
    w = round(height * 4.16)
    path = os.path.join(ROOT, src.lstrip('/'))
    if src.endswith('.svg') and os.path.exists(path):
        m = re.search(r'viewBox="([-\d. ]+)"', open(path, encoding='utf-8').read())
        if m:
            vb = [float(x) for x in m.group(1).split()]
            w = round(height * vb[2] / vb[3])
    return f'<img class="{cls}" src="/{e(src.lstrip("/"))}" alt="{e(site["name"])}" width="{w}" height="{height}">'


def wordmark(site):
    # LOGO SLOT: site.json "logo" (black logo, light header). null = text wordmark.
    return logo_img(site, 'logo', 'logo', 40) or f'<span class="wordmark">{e(site["name"])}</span>'


def foot_brand(site):
    # The footer is light, so it uses the black logo too. (Use logo_img(site, 'logo_dark', ...) on a dark background.)
    img = logo_img(site, 'logo', 'foot-logo', 34)
    return f'<p class="foot-brand">{img}</p>' if img else f'<p class="foot-brand">{e(site["name"])}</p>'


def webmanifest(site):
    return json.dumps({
        'name': site['name'], 'short_name': site['name'], 'start_url': '/', 'display': 'standalone',
        'background_color': '#000000', 'theme_color': '#ffffff',
        'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'},
                  {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'}],
    }, indent=2) + '\n'


_CSS = None


def css():
    """src/style.css, lightly minified and inlined into every page (it's small; this saves a render-blocking request)."""
    global _CSS
    if _CSS is None:
        t = open(os.path.join(ROOT, 'src', 'style.css'), encoding='utf-8').read()
        t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
        t = re.sub(r'\s*\n\s*', '', t)
        _CSS = t.strip()
    return _CSS


def page(site, path, title, desc, body, og_image='/images/og-logo.png', extra_head=''):
    url = site['base_url'] + path
    full_title = title if title == site['name'] else f'{title} · {site["name"]}'
    nav = ''.join(f'<li><a href="{h}"{" aria-current=\"page\"" if path.startswith(h) else ""}>{e(t)}</a></li>' for h, t in NAV)
    img = site['base_url'] + og_image
    is_logo = og_image == '/images/og-logo.png'
    og_size = '\n  <meta property="og:image:width" content="1200">\n  <meta property="og:image:height" content="630">' if is_logo else ''
    img_alt = site['name'] + (' logo' if is_logo else '')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{e(full_title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="canonical" href="{e(url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{e(site["name"])}">
  <meta property="og:url" content="{e(url)}">
  <meta property="og:title" content="{e(full_title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:image" content="{e(img)}">{og_size}
  <meta property="og:image:alt" content="{e(img_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(full_title)}">
  <meta name="twitter:description" content="{e(desc)}">
  <meta name="twitter:image" content="{e(img)}">
  <meta name="twitter:image:alt" content="{e(img_alt)}">
  <meta name="theme-color" content="#ffffff">
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <style>{css()}</style>{extra_head}
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-head">
    <a class="brand" href="/" aria-label="{e(site["name"])} home">{wordmark(site)}</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav"><span class="bars" aria-hidden="true"></span>Menu</button>
    <nav id="site-nav" aria-label="Main"><ul>{nav}</ul></nav>
  </header>
  <main id="main" tabindex="-1">
{body}
  </main>
  <footer class="site-foot">
    <div class="accent-bar" aria-hidden="true"></div>
    {foot_brand(site)}
    <p>One-of-a-kind artisan jewelry.</p>
    <nav aria-label="Footer"><ul class="foot-nav">{nav.replace(' aria-current="page"', '')}</ul></nav>
    <p class="fine">© {BUILD_DATE[:4]} {e(site["name"])}</p>
  </footer>
  <script src="/assets/site.js" defer></script>
</body>
</html>
'''


def ph_note(text='Placeholder copy'):
    return f'<span class="ph-tag">{e(text)}</span>'


def materials(p):
    return ' · '.join(p.get('metals', []) + p.get('stones', []))


CARD_SIZES = '(min-width: 1120px) 347px, (min-width: 760px) calc((100vw - 76px) / 3), calc((100vw - 48px) / 2)'
GALLERY_SIZES = '(min-width: 1120px) 580px, (min-width: 860px) 52vw, calc(100vw - 36px)'


def card(p, site, eager=False, priority=False):
    im = p['_imgs'][0]
    return (f'<li class="card"><a href="/shop/{e(p["slug"])}/">'
            f'<span class="card-img">{img_html(im, CARD_SIZES, eager, priority)}</span>'
            f'<span class="card-name">{e(p["name"])}</span>'
            f'<span class="card-meta">{e(materials(p))}</span>'
            f'<span class="card-price">{e(price(p, site))}</span></a>'
            + (f'<a class="card-buy" href="{e(stripe_link(p, site))}" target="_blank" rel="noopener">Buy<span class="sr-only"> {e(p["name"])}</span></a>' if stripe_link(p, site) else '')
            + '</li>')


def price(p, site):
    if p.get('price') not in (None, ''):
        v = p['price']
        return f'${v:,.0f}' if isinstance(v, (int, float)) and site.get('currency', 'USD') == 'USD' else str(v)
    return site.get('price_display', 'Price TBD')


def home(site, pieces, services):
    feat = [p for p in pieces if p.get('featured')][:3] or pieces[:3]
    svc = ''.join(f'<li><strong>{e(s["name"])}</strong>{" <span class=\"soon\">Coming soon</span>" if s["status"] == "coming_soon" else ""}</li>' for s in services)
    body = f'''    <section class="hero">
      <p class="eyebrow">One-of-a-kind artisan jewelry</p>
      <h1>{e(site["tagline"])}</h1>
      <p class="lede">Sterling silver and gold-filled pieces with gemstone beads and stones. Statement pieces and everyday favorites, each one made to be yours.</p>
      <div class="actions"><a class="btn primary" href="/shop/">Shop the collection</a><a class="btn" href="/commissions/">Commission a piece</a></div>
    </section>
    <section class="block">
      <div class="block-head"><h2>Current pieces</h2><a class="more" href="/shop/">View all</a></div>
      <ul class="grid">{"".join(card(p, site, eager=k < 2) for k, p in enumerate(feat))}</ul>
      <p class="note">The lineup changes over time, and favorites can be remade.</p>
    </section>
    <section class="block split">
      <div class="soft-panel">
        <h2>The story</h2>
        <p>Jewelry holds emotion and memory. Every piece is made by hand to feel sentimental and timeless, with a little glamour for the nights out.</p>
        <p class="ph">{ph_note()} A short welcome from {e(site.get("maker_name") or "the maker")} goes here.</p>
        <a class="more" href="/about/">Read our story</a>
      </div>
      <div class="soft-panel">
        <h2>Made for your story</h2>
        <p>Have an idea, a favorite stone, or an occasion to mark? Commission a one-of-a-kind piece.</p>
        <a class="btn" href="/commissions/">Start a commission</a>
      </div>
    </section>
    <section class="block">
      <div class="block-head"><h2>Services</h2><a class="more" href="/services/">See services</a></div>
      <ul class="svc-mini">{svc}</ul>
    </section>'''
    return page(site, '/', site['name'], 'One-of-a-kind artisan jewelry in sterling silver and gold-filled, with gemstones and stones. Heirloom meets a night out.', body)


def shop(site, pieces):
    body = f'''    <section class="page-head">
      <h1>Shop</h1>
      <p class="lede">A rotating lineup of one-of-a-kind pieces. Favorites can be remade, so if you love something, just ask.</p>
    </section>
    <ul class="grid">{"".join(card(p, site, eager=k < 4, priority=k == 0) for k, p in enumerate(pieces))}</ul>'''
    return page(site, '/shop/', 'Shop', 'Shop one-of-a-kind artisan jewelry: statement pieces and everyday favorites in sterling silver, gold-filled and copper.', body)


def stripe_link(p, site):
    """The piece's Stripe Payment Link, or '' (only https://buy.stripe.com/... links are used)."""
    if site.get('checkout_provider') != 'stripe_payment_links':
        return ''
    u = (p.get('stripe_link') or '').strip()
    return u if u.startswith('https://buy.stripe.com/') else ''


def ask_url(p):
    from urllib.parse import quote
    return f'/contact/?piece={quote(p["name"])}'


def buy_box(p, site):
    u = stripe_link(p, site)
    if u:
        return (f'<div class="buy"><a class="btn primary wide" href="{e(u)}" target="_blank" rel="noopener">Buy<span class="sr-only"> {e(p["name"])} (opens secure checkout)</span></a>'
                f'<a class="btn wide" href="{e(ask_url(p))}">Ask about this piece</a></div>')
    return f'<div class="buy"><a class="btn primary wide" href="{e(ask_url(p))}">Ask about this piece</a></div>'


def piece_page(site, p, pieces):
    imgs = p['_imgs']
    n = len(imgs)
    slides = []
    for k, im in enumerate(imgs):
        full, full_set = full_src(im)
        slides.append(
            f'<div class="slide" id="{e(p["slug"])}-{k + 1}" role="group" aria-roledescription="slide" aria-label="{k + 1} of {n}">'
            f'<button type="button" class="zoom" data-i="{k}" data-full="{e(full)}" data-srcset="{e(full_set)}" data-alt="{e(im["alt"])}" aria-haspopup="dialog">'
            f'{img_html(im, GALLERY_SIZES, eager=k == 0, priority=k == 0)}<span class="sr-only">Enlarge photo {k + 1} of {n}</span></button></div>')
    slides = ''.join(slides)
    thumbs = ''.join(
        f'<li><a href="#{e(p["slug"])}-{k + 1}" data-go="{k}"{" aria-current=\"true\"" if k == 0 else ""}><span class="sr-only">Show photo {k + 1} of {n}</span>'
        f'{img_html(dict(im, alt=""), "64px", cls="thumb-img")}</a></li>'
        for k, im in enumerate(imgs)) if n > 1 else ''
    dets = ''.join(f'<li>{e(d)}</li>' for d in p.get('details', []))
    others = [o for o in pieces if o is not p][:3]
    ph = any(im['placeholder'] for im in imgs)
    body = f'''    <nav class="crumbs" aria-label="Breadcrumb"><a href="/shop/">Shop</a> <span aria-hidden="true">›</span> {e(p["name"])}</nav>
    <article class="piece">
      <section class="gallery" data-gallery aria-roledescription="carousel" aria-label="Photos of {e(p["name"])}">
        <div class="slides" role="group" tabindex="0" aria-label="Photos of {e(p["name"])}. Swipe, use the arrow keys or the thumbnails.">{slides}</div>
        {f'<ul class="thumbs" aria-label="Choose a photo">{thumbs}</ul>' if thumbs else ''}
        <p class="gal-hint" aria-hidden="true">{"Swipe for more photos · " if n > 1 else ""}Tap a photo to enlarge</p>
        {f'<p class="ph">{ph_note("Placeholder photos")} Close-up photos of this piece go here.</p>' if ph else ''}
      </section>
      <div class="piece-info">
        <p class="eyebrow">{e(p.get("style", ""))}</p>
        <h1>{e(p["name"])}</h1>
        <p class="piece-mat">{e(materials(p))}</p>
        <p class="piece-price">{e(price(p, site))}</p>
        {buy_box(p, site)}
        <p class="piece-desc">{e(p.get("description", ""))}</p>
        {f'<ul class="piece-det">{dets}</ul>' if dets else ''}
        <p class="note">Each piece is one of a kind and handmade. Favorites can be remade, so the next one will be yours alone.</p>
      </div>
    </article>
    <dialog class="lightbox" aria-label="Enlarged photo">
      <img alt="">
      <p class="lb-count" aria-live="polite"></p>
      <div class="lb-bar">{'<button type="button" class="lb-prev"><span aria-hidden="true">‹</span> Previous</button><button type="button" class="lb-next">Next <span aria-hidden="true">›</span></button>' if n > 1 else ''}<button type="button" class="lb-close">Close</button></div>
    </dialog>
    <section class="block">
      <div class="block-head"><h2>More pieces</h2><a class="more" href="/shop/">View all</a></div>
      <ul class="grid">{"".join(card(o, site) for o in others)}</ul>
    </section>'''
    first = imgs[0]
    if 'bases' in first:
        og = next((b for b in first['bases'] if int(b.rsplit('-', 1)[1]) >= 1200), first['bases'][-1]) + '.jpg'
    elif not first['placeholder'] and first['src'].startswith('/') and first['src'].lower().endswith(('.jpg', '.jpeg', '.png')):
        og = first['src']
    else:
        og = '/images/og-logo.png'
    return page(site, f'/shop/{p["slug"]}/', p['name'], f'{p["name"]}: one-of-a-kind artisan jewelry. {materials(p)}.', body, og_image=og)


def about(site):
    m = e(site.get('maker_name') or 'the maker')
    body = f'''    <section class="page-head">
      <h1>Our Story</h1>
      <p class="lede">Heirloom meets a night out.</p>
    </section>
    <div class="prose">
      <figure class="portrait"><img src="/images/placeholders/portrait.svg" alt="Placeholder photo for a portrait of {m} at work" width="800" height="800" fetchpriority="high"></figure>
      <p>Makers Inspire is one-of-a-kind artisan jewelry by {m}: mostly sterling silver and gold-filled, with gemstone beads and other stones, and now a little copper and stainless steel.</p>
      <p>The pieces are made for women who want to feel even more beautiful. Each one is unique and becomes yours, because jewelry carries emotion and memory. The look is sentimental and timeless, and also glamorous and fun.</p>
      <div class="ph-block">{ph_note()}<p>{m}'s story in her own words: how she started, why she makes jewelry, and what inspires each piece.</p></div>
      <div class="actions"><a class="btn primary" href="/shop/">Shop the collection</a><a class="btn" href="/contact/">Get in touch</a></div>
    </div>'''
    return page(site, '/about/', 'Our Story', f'The story behind Makers Inspire: one-of-a-kind artisan jewelry by {site.get("maker_name") or "the maker"}, made to carry emotion and memory.', body)


def form_open(site, kind, subject):
    """<form> start tag + hidden fields. With form_endpoint: POST (FormSubmit-style fields). Without: mailto fallback in site.js."""
    if site.get('form_endpoint'):
        cap = 'true' if site.get('form_captcha', True) else 'false'
        return (f'<form class="form" action="{e(site["form_endpoint"])}" method="POST" data-kind="{kind}" data-subject="{e(subject)}">'
                f'<input type="hidden" name="_subject" value="{e(subject)}">'
                f'<input type="hidden" name="_template" value="table">'
                f'<input type="hidden" name="_captcha" value="{cap}">'
                f'<input type="hidden" name="_next" value="{e(site["base_url"])}/thanks/">'
                f'<div class="hp" aria-hidden="true"><label for="{kind}-hp">Leave this field empty</label>'
                f'<input id="{kind}-hp" type="text" name="_honey" tabindex="-1" autocomplete="off" style="display:none"></div>')
    to = site.get('contact_email') or ''
    return f'<form class="form" action="#" method="POST" data-kind="{kind}" data-subject="{e(subject)}" data-mailto="{e(to)}">'


def form_status(site):
    if not site.get('contact_email'):
        return ''
    if site.get('form_endpoint'):
        m = e(site['contact_email'])
        return f'<p class="form-alt">Prefer email? Write to <a href="mailto:{m}">{m}</a>.</p>'
    m = e(site['contact_email'])
    return (f'<p class="form-status" role="status" tabindex="-1" hidden>Your email app should open with your message ready to send. '
            f'If it doesn’t, email <a href="mailto:{m}">{m}</a>.</p>')


def commissions(site):
    body = f'''    <section class="page-head">
      <h1>Commissions</h1>
      <p class="lede">A one-of-a-kind piece made around your idea, your favorite stone or metal, and the story behind it.</p>
    </section>
    {form_open(site, "commission", "Commission request")}
      <p class="form-note">Required fields are marked *</p>
      <div class="field"><label for="c-name">Your name <span class="req" aria-hidden="true">*</span></label><input id="c-name" name="name" data-label="Name" autocomplete="name" required data-err="Please enter your name."></div>
      <div class="field"><label for="c-email">Email <span class="req" aria-hidden="true">*</span></label><input id="c-email" name="email" data-label="Email" type="email" autocomplete="email" inputmode="email" required data-err="Please enter your email address." data-err-type="Please enter a valid email address, like name@example.com."></div>
      <div class="field"><label for="c-idea">Your idea <span class="req" aria-hidden="true">*</span></label><textarea id="c-idea" name="idea" data-label="Idea" rows="4" required data-err="Please describe your idea." placeholder="A necklace, earrings, a ring… anything you have in mind"></textarea></div>
      <div class="field"><label for="c-material">Preferred stone or metal <span class="opt">(optional)</span></label><input id="c-material" name="stone_or_metal" data-label="Preferred stone or metal" placeholder="e.g. sterling silver with a favorite stone"></div>
      <div class="field"><label for="c-story">The story or occasion <span class="opt">(optional)</span></label><textarea id="c-story" name="story" data-label="Story or occasion" rows="4" placeholder="A birthday, an anniversary, a memory you want to keep close"></textarea></div>
      <button class="btn primary wide" type="submit">Send commission request</button>
      {form_status(site)}
    </form>'''
    return page(site, '/commissions/', 'Commissions', 'Commission a one-of-a-kind piece of jewelry around your idea, your stone or metal, and the story behind it.', body)


def services_page(site, services):
    rows = []
    for s in services:
        soon = s['status'] == 'coming_soon'
        link = f'<a class="more" href="{e(s["link"])}">{e(s.get("link_label") or "Learn more")}</a>' if s.get('link') else ''
        rows.append(f'<li class="svc{" is-soon" if soon else ""}" id="{e(s["slug"])}"><h2>{e(s["name"])}{" <span class=\"soon\">Coming soon</span>" if soon else ""}</h2>'
                    f'<p>{e(s.get("summary", ""))}</p>{link}</li>')
    body = f'''    <section class="page-head">
      <h1>Services</h1>
      <p class="lede">Ways to work together beyond the shop. More to come.</p>
    </section>
    <ul class="svc-list">{"".join(rows)}</ul>'''
    return page(site, '/services/', 'Services', 'Jewelry services from Makers Inspire, including custom commissions. Stone setting coming soon.', body)


def contact(site):
    direct = []
    if site.get('contact_email'):
        m = e(site['contact_email'])
        direct.append(f'<p class="direct">Email <a href="mailto:{m}">{m}</a></p>')
    if site.get('instagram'):
        direct.append(f'<p class="direct">Instagram <a href="https://www.instagram.com/{e(site["instagram"])}/" rel="noopener">@{e(site["instagram"])}</a></p>')
    if not direct:
        direct.append(f'<div class="ph-block">{ph_note("Placeholder")}<p>Direct contact details will be added here.</p></div>')
    body = f'''    <section class="page-head">
      <h1>Contact</h1>
      <p class="lede">Questions about a piece, buying, or a custom idea? Send a note.</p>
    </section>
    {"".join(direct)}
    {form_open(site, "contact", "Question from makersinspire.com")}
      <p class="form-note">Required fields are marked *</p>
      <div class="field"><label for="m-name">Your name <span class="req" aria-hidden="true">*</span></label><input id="m-name" name="name" data-label="Name" autocomplete="name" required data-err="Please enter your name."></div>
      <div class="field"><label for="m-email">Email <span class="req" aria-hidden="true">*</span></label><input id="m-email" name="email" data-label="Email" type="email" autocomplete="email" inputmode="email" required data-err="Please enter your email address." data-err-type="Please enter a valid email address, like name@example.com."></div>
      <div class="field"><label for="m-piece">Piece <span class="opt">(optional)</span></label><input id="m-piece" name="piece" data-label="Piece" data-piece-field></div>
      <div class="field"><label for="m-msg">Message <span class="req" aria-hidden="true">*</span></label><textarea id="m-msg" name="message" data-label="Message" rows="5" required data-err="Please write your message."></textarea></div>
      <button class="btn primary wide" type="submit">Send message</button>
      {form_status(site)}
    </form>'''
    return page(site, '/contact/', 'Contact', 'Contact Makers Inspire about a piece, a purchase or a custom commission.', body)


def thanks(site):
    body = '''    <section class="page-head center">
      <h1>Thank you</h1>
      <p class="lede">Your message is on its way. We’ll be in touch soon.</p>
      <div class="actions"><a class="btn primary" href="/shop/">Back to the shop</a><a class="btn" href="/">Home</a></div>
    </section>'''
    return page(site, '/thanks/', 'Thank you', 'Thank you for your message.', body).replace('<meta name="theme-color"', '<meta name="robots" content="noindex">\n  <meta name="theme-color"', 1)


def not_found(site):
    body = '''    <section class="page-head center">
      <h1>Page not found</h1>
      <p class="lede">This page doesn’t exist, or the piece has rotated out of the lineup.</p>
      <div class="actions"><a class="btn primary" href="/shop/">Visit the shop</a><a class="btn" href="/">Home</a></div>
    </section>'''
    return page(site, '/404.html', 'Page not found', 'Page not found.', body).replace('<meta name="theme-color"', '<meta name="robots" content="noindex">\n  <meta name="theme-color"', 1)


def sitemap(site, pieces):
    paths = ['/', '/shop/', '/about/', '/commissions/', '/services/', '/contact/'] + [f'/shop/{p["slug"]}/' for p in pieces]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + ''.join(f'  <url><loc>{site["base_url"]}{x}</loc><lastmod>{BUILD_DATE}</lastmod></url>\n' for x in paths) + '</urlset>\n')


def outputs():
    site, pieces, services = load_all()
    files = {
        'index.html': home(site, pieces, services), 'shop/index.html': shop(site, pieces), 'about/index.html': about(site),
        'commissions/index.html': commissions(site), 'services/index.html': services_page(site, services),
        'contact/index.html': contact(site), 'thanks/index.html': thanks(site), '404.html': not_found(site), 'sitemap.xml': sitemap(site, pieces),
        'robots.txt': f'User-agent: *\nAllow: /\n\nSitemap: {site["base_url"]}/sitemap.xml\n',
        'assets/site.js': open(os.path.join(ROOT, 'src', 'site.js'), encoding='utf-8').read(),
        'images/placeholders/portrait.svg': placeholder_svg({'slug': 'portrait', '_pal': PALETTES[1]}, 0, 1).replace('<text x="400" y="112"', '<text display="none" x="400" y="112"'),
    }
    for p in pieces:
        files[f'shop/{p["slug"]}/index.html'] = piece_page(site, p, pieces)
        n = len(p['_imgs'])
        for k, im in enumerate(p['_imgs']):
            if im['placeholder']:
                files[im['src'].lstrip('/')] = placeholder_svg(p, k, n)
    files['site.webmanifest'] = webmanifest(site)
    bins = {}  # logo, icons and images/og-logo.png are made by tools/make_brand.py (committed files)
    return files, bins


def main():
    check = '--check' in sys.argv
    stale = process_photos(load('pieces.json')['pieces'], check)
    files, bins = outputs()
    for rel, content in list(files.items()) + list(bins.items()):
        path = os.path.join(ROOT, rel)
        data = content if isinstance(content, bytes) else content.encode('utf-8')
        old = open(path, 'rb').read() if os.path.exists(path) else None
        if old == data:
            continue
        if check:
            stale.append(rel)
            continue
        os.makedirs(os.path.dirname(path) or ROOT, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        print('wrote', rel)
    # Remove generated piece pages / placeholders for pieces no longer in the lineup.
    keep = set(files) | set(bins)
    for base in ('shop', 'images/placeholders'):
        d = os.path.join(ROOT, base)
        for dirpath, _, names in os.walk(d):
            for n in names:
                rel = os.path.relpath(os.path.join(dirpath, n), ROOT)
                if rel not in keep and (n == 'index.html' or n.endswith('.svg')):
                    if check:
                        stale.append(rel + ' (orphan)')
                    else:
                        os.remove(os.path.join(ROOT, rel)); print('removed', rel)
            if not check and dirpath != d and not os.listdir(dirpath):
                os.rmdir(dirpath)
    if check:
        if stale:
            print('out of date:', ', '.join(stale)); sys.exit(1)
        print('up to date')


if __name__ == '__main__':
    main()
