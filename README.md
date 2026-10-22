# makersinspire.com

Static site for **Makers Inspire**, one-of-a-kind artisan jewelry. Hosted on GitHub Pages from `main` (repo root), custom domain `www.makersinspire.com` (see `CNAME`). No frameworks, trackers or third-party scripts.

## How it works
- **Edit the data**, never the generated HTML:
  - `site.json`: name, tagline, logo, price text, checkout, form endpoint, contact details.
  - `pieces.json`: the shop lineup (one entry per piece).
  - `services.json`: the Services section.
  - `src/style.css` (inlined into every page) and `src/site.js` (copied to `assets/`): styles and the small first-party script.
  - `photos/<slug>/`: original piece photos (not published; see [ADDING-PIECES.md](ADDING-PIECES.md)).
- **Build**: `python3 build.py`, then `python3 build.py --check` (must say "up to date"). Optional `BUILD_DATE=YYYY-MM-DD` pins the sitemap date.
- **Commit and push** the data plus the generated files. Pages deploys in about a minute.

Generated pages: `/`, `/shop/`, `/shop/<slug>/` (one per piece), `/about/`, `/commissions/`, `/services/`, `/contact/`, `/thanks/`, `404.html`, `sitemap.xml`, `robots.txt`, `site.webmanifest`, and placeholder images in `images/placeholders/`.

## Add a piece
**See [ADDING-PIECES.md](ADDING-PIECES.md)**, the plain-English guide covering photos, every `pieces.json` field, alt text, Stripe links, rotation and publishing.

In short: put the original photos in `photos/<slug>/`, add an entry to `pieces.json`, then run `python3 build.py && python3 build.py --check`, commit and push.

## Photos and speed
- `photos/` holds the originals and is **gitignored**: they're large and can carry GPS/EXIF, and anything in the repo is public on Pages. Keep a backup elsewhere.
- `build.py` (with Pillow) turns each photo into `images/pieces/<slug>/<name>-<width>.webp` and `.jpg` at 160, 320, 480, 800, 1200 and 1600 px wide (never upscaled). It applies EXIF rotation, converts to sRGB and drops all metadata (EXIF, GPS, XMP).
- `images/pieces/manifest.json` records each original's hash and size. A rebuild only re-encodes changed photos, and the site still builds on a computer without the originals. `--check` reports photos that need processing.
- Markup is `<picture>` with a WebP `srcset` plus a JPEG fallback, `sizes`, and `width`/`height` (no layout shift).
  - The first gallery photo and the first shop card get `fetchpriority="high"`.
  - Above-the-fold cards load eagerly; everything else uses `loading="lazy"`.
  - The lightbox loads the largest size.
- CSS is inlined into each page (it's small), so there's no render-blocking stylesheet request.
- `site.js` is the only script.

## Remove or rotate a piece
- Take it out of the lineup: set `"show": false` (keeps the entry for later), or delete the entry.
- The build removes that piece's page and placeholders (and, for deleted photos, the web-size copies) automatically.
- There are deliberately **no sold / sold-out states**: favorites can be remade.

## Checkout: Stripe Payment Links
`site.json` → `"checkout_provider": "stripe_payment_links"`. Each piece has an optional `stripe_link`.
- **Link set**: the piece page shows a **Buy** button that opens the link in a new tab (`target="_blank" rel="noopener"`), plus "Ask about this piece". The shop grid shows a small Buy button too.
- **Link empty (`""`)**: the piece shows an **Ask about this piece** button that opens the contact form with the piece name filled in.
- Only `https://buy.stripe.com/...` links are used; anything else is ignored.

To paste in a Payment Link:
1. In the Stripe Dashboard, go to **Product catalog** and create the product (name, price, photo). Then **Payment Links → New**, select the product, and set quantity, shipping and tax options as needed.
2. Copy the link (it looks like `https://buy.stripe.com/...`).
3. Paste it into that piece's `"stripe_link"` in `pieces.json`, run the build, commit, push.
4. Optional: in the Payment Link's settings, set the after-payment confirmation or redirect (e.g. back to `https://www.makersinspire.com/shop/`).

A remade favorite can keep using the same link.

## Forms (commissions + contact)
Both forms are configured from `site.json`:
- **`form_endpoints`**: one [Formspree](https://formspree.io) endpoint per form (free plan, account on the shared lessons login in Noah's vault):
  - `contact` (Contact page): `https://formspree.io/f/xkjjwygg`
  - `commission` (Commissions page): `https://formspree.io/f/xvkkplgz`

  Submissions are emailed to Erika's Makers Inspire Gmail (set in Formspree, not in this repo, so no address appears in the page source). Formspree sends her a one-time verification email that must be clicked before messages are delivered. Each form sends these hidden fields:
  - `_subject`: "New commission request - Makers Inspire", or on Contact "Question about <piece> - Makers Inspire" (set on submit from the Piece field; "New message - Makers Inspire" if empty);
  - `_gotcha`: Formspree's hidden honeypot field for spam bots.

  Visible fields: name, email (Formspree uses it as reply-to), and idea / stone_or_metal / story (Commissions) or piece / message (Contact).
- **Thank-you flow:** with JavaScript, `site.js` sends the form with `fetch` (`Accept: application/json`). On success it goes to `/thanks/` (noindex); on an error it shows an inline "didn't send, please try again" message. Without JavaScript the form posts normally and Formspree shows its own thank-you page (the free plan doesn't allow a custom redirect, so `_next` isn't used).
- **No endpoint** (remove a key from `form_endpoints`, or set it to `null`): that form opens the visitor's email app with a prefilled message to `contact_email`. Subject as above; the body is the filled-in fields as labelled lines ("Name: …", "Email: …", "Idea: …", "Preferred stone or metal: …", "Story or occasion: …", "Piece: …", "Message: …"). A short note says the email app will open, with the address as a fallback. (This puts the address in the page source.) A single shared `form_endpoint` string also still works.
- Validation runs before either path: required fields are marked *, and errors appear under each field (linked with `aria-describedby`, `aria-invalid`), with focus moving to the first problem. Without JavaScript, the browser's own validation runs.
- **`contact_email`**: Erika's address (provided by Noah). Used only by the mailto fallback above. **`show_contact_email`**: `false` (current) keeps it off every page; `true` shows it on the Contact page as a mailto link and under both forms as "Prefer email?". **`instagram`**: shown on the Contact page once set.

## Services
Add entries to `services.json`. `status` is `"available"` or `"coming_soon"` (shows a "Coming soon" tag). `link` and `link_label` are optional (e.g. `/commissions/`).

## Logo, icons and share image
Noah's logo file is kept as `brand/logo-original.jpg`. `tools/make_brand.py` traces it to clean SVGs and writes every derived file (run it only if the original changes; it needs `pip install vtracer cairosvg pillow numpy`, e.g. in a venv):

| File | Use |
|---|---|
| `brand/logo-black.svg` | Black (#111) lockup, transparent. **Header** (40px tall, 46px on desktop) and **footer** (34px), both light. `site.json` → `logo`. |
| `brand/logo-white.svg` | Silver-gradient MI mark + white wordmark, transparent, for **dark areas**. `site.json` → `logo_dark` (used in the share image; there is no dark section on the site yet). |
| `brand/mark-black.svg`, `brand/mark-white.svg`, `brand/mark-silver.svg` | The MI square alone. |
| `brand/*@2x.png`, `brand/*@3x.png` | PNG fallbacks of each (1x = 48px tall). |
| `favicon.svg`, `favicon.ico` (16/32/48) | Tab icon: silver MI on black. The 16px version is redrawn on whole pixels so it stays legible. |
| `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png` + `site.webmanifest` | Home-screen / app icons: silver MI on black (maskable-safe). |
| `images/og-logo.png` | 1200x630 share image (og:image / twitter:image): logo centred on black with a thin stone-and-metal accent line. Piece pages use their own first photo once real photos exist. |

The trace matches the original closely (letter shapes and spacing overlap ~99%). The silver is a measured linear gradient (#efefef → #989898). Alt text is "Makers Inspire". Set `logo` to `null` to go back to the text wordmark.

## Accessibility
The site is checked with axe-core (WCAG 2.2 A/AA plus best practices) and Lighthouse.
- **Navigation:** skip link, landmarks (header, main navigation, main, footer navigation), and a 3px focus ring with a white halo.
- **Menu:** the button reports open or closed (`aria-expanded`); Escape closes it and returns focus to the button.
- **Gallery:** an arrow-key gallery with `aria-current` thumbnails.
- **Lightbox:** a modal dialog with Previous/Next buttons, arrow keys, a live photo count and focus kept inside; Escape closes it and returns focus to the photo.
- **Motion and touch:** reduced-motion is respected; tap targets are at least 44px; text and form-field borders meet AA contrast.

## Placeholders still to replace
- Photos: generated SVGs marked "Placeholder photo".
- Copy: blocks tagged "Placeholder copy" (home welcome, Our Story) and the placeholder pieces in `pieces.json`.
- Prices: "Price TBD" until set.
