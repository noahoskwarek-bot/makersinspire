#!/usr/bin/env python3
"""Render the 1200x630 share image (og:image / twitter:image) from the real home-page hero booth.

Needs: pip install playwright pillow, plus Chromium (`playwright install chromium`, or set CHROME=/path/to/chrome).
Run from the repo root after `python3 build.py`:  python3 tools/make_og.py
It serves the repo locally, lays out the same .booth markup with the site's own CSS (taken from index.html) on an
ivory 1200x630 canvas, screenshots it at 2x and downsamples for crisp edges. Output: images/og-booth-v2.png.
When the hero changes, bump the file name (and OG_IMAGE in build.py) so iMessage / Facebook / X fetch it again.
"""
import asyncio, functools, http.server, io, os, re, threading
from PIL import Image
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'images', 'og-booth-v2.png')


def page_html():
    idx = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    css = re.search(r'<style>(.*?)</style>', idx, re.S).group(1)
    booth = re.search(r'<div class="booth".*?</div>', idx, re.S).group(0)
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{background:linear-gradient(180deg,var(--ivory),var(--white))}}
.og{{position:absolute;inset:0;display:flex;align-items:flex-end;justify-content:center;padding-bottom:34px}}
.og .booth{{width:720px;max-width:none;margin:0}}
</style></head><body><div class="og">{booth}</div></body></html>'''


async def shoot(port):
    async with async_playwright() as p:
        kw = {'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}
        b = await p.chromium.launch(args=['--no-sandbox'], **kw)
        pg = await b.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=2)
        await pg.goto(f'http://127.0.0.1:{port}/_og.html', wait_until='networkidle')
        await pg.wait_for_timeout(300)
        png = await pg.screenshot()
        await b.close()
    return png


def main():
    tmp = os.path.join(ROOT, '_og.html')
    open(tmp, 'w', encoding='utf-8').write(page_html())
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        png = asyncio.run(shoot(srv.server_address[1]))
    finally:
        srv.shutdown(); os.remove(tmp)
    Image.open(io.BytesIO(png)).convert('RGB').resize((1200, 630), Image.LANCZOS).save(OUT, optimize=True)
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
