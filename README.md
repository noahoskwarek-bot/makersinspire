# makersinspire.com

Static site for **Makers Inspire**, one-of-a-kind artisan jewelry. Hosted on GitHub Pages from `main` (repo root), custom domain `www.makersinspire.com` (see `CNAME`). No frameworks, trackers or third-party scripts.

## How it works
- **Edit the data**, never the generated HTML:
  - `site.json`: name, tagline, logo, price text, checkout, form endpoint, contact details.
  - `pieces.json`: the shop lineup (one entry per piece).
  - `services.json`: the Services section.
  - `src/style.css`, `src/site.js`: styles and the small first-party script (copied to `assets/`).
- **Build**: `python3 build.py`, then `python3 build.py --check` (must say "up to date"). Optional `BUILD_DATE=YYYY-MM-DD` pins the sitemap date.
- **Commit and push** the data plus the generated files. Pages deploys in about a minute.

Generated pages: `/`, `/shop/`, `/shop/<slug>/` (one per piece), `/about/`, `/commissions/`, `/services/`, `/contact/`, `/thanks/`, `404.html`, `sitemap.xml`, `robots.txt`, `site.webmanifest`, and placeholder images in `images/placeholders/`.

## Add a piece
1. Put close-up photos in `images/pieces/<slug>/` (JPEG or WebP, about 1600 px on the long edge, square crops look best in the grid).
2. Add an entry to `pieces.json`:
   ```json
   {
     "slug": "rose-quartz-drop-necklace",
     "name": "Rose Quartz Drop Necklace",
     "style": "Statement",
     "metals": ["Sterling silver"],
     "stones": ["Rose quartz"],
     "description": "A sentence or two in Erika's words.",
     "details": ["Length: 18 in", "Lobster clasp"],
     "price": 145,
     "stripe_link": "",
     "images": [
       {"src": "/images/pieces/rose-quartz-drop-necklace/1.jpg", "alt": "Rose quartz drop necklace, close-up of the stone"},
       {"src": "/images/pieces/rose-quartz-drop-necklace/2.jpg", "alt": "The necklace worn"}
     ],
     "featured": true,
     "show": true
   }
   ```
   - `slug`: lowercase, hyphens, unique. It becomes `/shop/<slug>/`.
   - `price`: a number in USD, or `null` to show `site.json` → `price_display` ("Price TBD").
   - `images`: any number of close-ups; the first is the grid photo. Write real alt text. With no images, numbered "Placeholder photo" SVGs are generated (`placeholder_images` sets how many).
   - `featured`: the first three featured pieces appear on the home page.
3. Run `python3 build.py && python3 build.py --check`, then commit and push.

## Remove or rotate a piece
- Take it out of the lineup: set `"show": false` (keeps the entry for later), or delete the entry.
- The build removes that piece's page and placeholders automatically.
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
- **`form_endpoint`**: currently `https://formsubmit.co/makersinspirellc@gmail.com` (approved by Noah). Both forms POST there with these hidden fields:
  - `_subject`: "Commission request", or on Contact "Question about <piece>" (set on submit from the Piece field; "Question from makersinspire.com" if empty);
  - `_template=table`;
  - `_captcha` (`site.json` → `form_captcha`; `true` keeps FormSubmit's captcha, `false` turns it off);
  - `_next=https://www.makersinspire.com/thanks/` (the thank-you page, `/thanks/`, noindex);
  - `_honey`: a hidden honeypot field for spam bots.

  Visible fields: name, email (FormSubmit uses it as reply-to), and idea / stone_or_metal / story (Commissions) or piece / message (Contact).
- **FormSubmit activation:** the very first submission to a new FormSubmit address sends an activation email to makersinspirellc@gmail.com. Someone must click it before messages are delivered. Nothing has been submitted yet, so expect that email on the first real (or deliberate test) submission. After activation, FormSubmit can also provide a random-string endpoint that hides the address; paste it into `form_endpoint` and rebuild.
- **`form_endpoint: null`** (fallback): submitting opens the visitor's email app with a prefilled message to `contact_email`. Subject as above; the body is the filled-in fields as labelled lines ("Name: …", "Email: …", "Idea: …", "Preferred stone or metal: …", "Story or occasion: …", "Piece: …", "Message: …"). A short note says the email app will open, with the address as a fallback.
- Browser validation (required fields, email format) runs before either path.
- **`contact_email`**: `makersinspirellc@gmail.com` (provided by Noah). Shown on the Contact page as a mailto link, and under both forms as "Prefer email?". **`instagram`**: shown on the Contact page once set.

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

## Placeholders still to replace
- Photos: generated SVGs marked "Placeholder photo".
- Copy: blocks tagged "Placeholder copy" (home welcome, Our Story) and the placeholder pieces in `pieces.json`.
- Prices: "Price TBD" until set.
