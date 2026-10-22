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

Generated pages: `/`, `/shop/`, `/shop/<slug>/` (one per piece), `/about/`, `/commissions/`, `/services/`, `/contact/`, `404.html`, `sitemap.xml`, `robots.txt`, `images/og.png`, and placeholder images in `images/placeholders/`.

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
- `site.json` → `form_endpoint`: a POST endpoint from a form service (for example Formspree or Basin). Set it and rebuild, and both forms post there (fields: name, email, idea / stone_or_metal / story, or piece / message).
- While it's `null`, the forms don't send anything; on submit they show a friendly "not connected yet" note.
- `contact_email` and `instagram` are shown on the Contact page only once set. Only use confirmed details.

## Services
Add entries to `services.json`. `status` is `"available"` or `"coming_soon"` (shows a "Coming soon" tag). `link` and `link_label` are optional (e.g. `/commissions/`).

## Logo
The header uses a text wordmark until the black-and-white logo is ready. Add it as `assets/logo.svg` (or PNG) and set `site.json` → `"logo": "assets/logo.svg"`.

## Placeholders still to replace
- Photos: generated SVGs marked "Placeholder photo".
- Copy: blocks tagged "Placeholder copy" (home welcome, Our Story) and the placeholder pieces in `pieces.json`.
- Prices: "Price TBD" until set.
