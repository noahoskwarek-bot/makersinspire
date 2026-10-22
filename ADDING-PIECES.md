# Adding pieces to makersinspire.com

A plain-English guide for Erika and Noah. The easiest way is to [just email it](#just-email-it). To do it yourself, adding a piece takes three steps: **photos**, **one entry in `pieces.json`**, then **rebuild and publish**.

All example values below are made up. Anything marked `EXAMPLE` is not a real piece, price or link.

## Just email it

Erika, you don't need to touch any files. Email new pieces to **pieces@makersinspire.com** from your usual email address. Only approved senders are accepted, so emails from other addresses are ignored.

**To add a new piece**, put these in the email:
- **Photos** as attachments: several close-ups. The first one is the main photo.
- The **piece name**.
- The **price**.
- **A sentence or two about it**: the stones, the metals, the feeling or story behind it.
- Your **Stripe Payment Link**, if you have one (optional).

**To take a piece down**, email `Remove: <piece name>` (or `sold`). It's hidden from the shop, never marked "sold", and can come back later.

**To change something**, email `Update: <piece name>` and say what changed.

**Nothing goes live without the details you send.** If anything's missing, you'll get a question back. Once the piece is live, you'll get a reply with the link.

**Keep your original photos.** The website only stores resized copies, with location data removed.

Here's a sample email. Everything in it is fake:

```
To:      pieces@makersinspire.com
Subject: New piece: EXAMPLE Sample Necklace

Name: EXAMPLE Sample Necklace
Price: EXAMPLE-PRICE
About: EXAMPLE: one or two sentences about the stones, the metals
       and the story behind the piece.
Stripe link: (none yet)

Attachments: EXAMPLE-1.jpg (main photo), EXAMPLE-2.jpg, EXAMPLE-3.jpg
```

The rest of this guide is the do-it-yourself version.


---

## 1. Photos

### Where they go
Make a folder named after the piece's `slug` (see below) inside `photos/`, and put the original photos straight from the phone or camera in it:

```
photos/
  example-moonstone-pendant/
    1-front.jpg
    2-side.jpg
    3-worn.jpg
    4-clasp.jpg
```

- JPEG, PNG or WebP. iPhone HEIC photos need converting to JPEG first: AirDrop or email them to a Mac, or set the iPhone camera to "Most Compatible".
- Don't resize or crop for the web. The build makes small, medium and large copies (160 to 1600 px wide, WebP plus a JPEG fallback). Each visitor's phone or computer downloads only the size it needs.
- **Location and camera data is removed.** The website copies are re-saved without EXIF/GPS. The originals in `photos/` are never published, because that folder isn't uploaded (it's in `.gitignore`). Keep your own backup of the originals somewhere else.

### Recommended shots
1. **Front, on a plain background.** This is the shop-grid photo, so it matters most. Soft daylight works best, with no harsh flash and the piece filling most of the frame.
2. **Close-up of the stone or detail** (texture, setting, wire work).
3. **Worn**: on the neck, wrist, ear or hand, to show size and how it sits.
4. **Clasp, back or scale**, e.g. next to a coin or ruler, or held in the hand.

Square or close-to-square framing looks best. The grid shows a square crop from the centre, while the piece page and the enlarged view show the whole photo. Aim for at least 1600 px on the short side, which any recent phone does easily.

### Photo order
Photos appear in the order of their file names, so number them: `1-front.jpg`, `2-detail.jpg`, `3-worn.jpg`. To choose the order yourself, or to add alt text, list them in `images` (below). The list order then wins.

---

## 2. The `pieces.json` entry

Open `pieces.json` and copy an existing entry inside `"pieces": [ ... ]`. Mind the commas between entries. Here is a complete example with every field:

```json
{
  "slug": "example-moonstone-pendant",
  "name": "EXAMPLE Moonstone Pendant",
  "style": "Everyday",
  "metals": ["Sterling silver"],
  "stones": ["Moonstone"],
  "description": "EXAMPLE: one or two sentences in Erika's words about the piece and the feeling behind it.",
  "details": ["EXAMPLE length: 18 in", "EXAMPLE clasp: lobster"],
  "price": 99,
  "stripe_link": "",
  "images": [
    {"file": "1-front.jpg", "alt": "EXAMPLE: Round moonstone pendant on a fine silver chain, lying on white linen"},
    {"file": "3-worn.jpg", "alt": "EXAMPLE: The pendant worn, resting just below the collarbone"}
  ],
  "placeholder_images": 3,
  "featured": false,
  "show": true
}
```

| Field | What it does | Example |
|---|---|---|
| `slug` | The web address: `/shop/<slug>/`. Lowercase letters, numbers and hyphens, and unique. It's also the photo folder name. Try not to change it once the piece is live, because old links would break. | `"example-moonstone-pendant"` |
| `name` | The piece's name, shown everywhere. | `"EXAMPLE Moonstone Pendant"` |
| `style` | The small label above the name. Use `"Statement"` or `"Everyday"`, or any word you like. | `"Everyday"` |
| `metals` | List of metals, shown as "Sterling silver · Moonstone". | `["Sterling silver"]` or `["Gold-filled", "Copper"]` |
| `stones` | List of stones or beads. Use `[]` if none. | `["Moonstone"]` |
| `description` | The main paragraph on the piece page. | `"EXAMPLE: ..."` |
| `details` | Bullet list under the description (length, size, clasp, care). Use `[]` if none. | `["EXAMPLE length: 18 in"]` |
| `price` | Number in US dollars, no `$`, or `null` to show "Price TBD" (`site.json` → `price_display`). | `99` or `null` |
| `stripe_link` | The Stripe Payment Link for the Buy button, or `""` for none. See [Stripe](#3-stripe_link-the-buy-button). | `""` or `"https://buy.stripe.com/EXAMPLE"` |
| `images` | The photos, in order. Each entry has a `file` (name inside `photos/<slug>/`) and an `alt` (description for screen readers). If you leave it as `[]`, every photo in the folder is used in file-name order, with automatic alt text. | see above |
| `placeholder_images` | Only used while there are no photos: how many labelled "Placeholder photo" images to show. | `3` |
| `featured` | `true` puts it on the home page. The first three featured pieces are shown. | `true` / `false` |
| `show` | `false` takes it off the site without deleting the entry. | `true` / `false` |

### Alt text tips
Alt text is read aloud to blind and low-vision visitors, and it's shown if a photo can't load.
- Describe what's **in the photo**, the way you'd describe it over the phone: the piece, the metal, the stone's colour and shape, and how it's shown (on linen, worn, in the hand).
- Keep it to about one sentence (under ~150 characters). Don't start with "Image of" or "Photo of".
- Make each photo's alt different: "front view", "close-up of the clasp", "worn with a black top".
- No keyword lists, and don't repeat the price.
- If you skip `alt`, the site uses "<piece name>, photo 2 of 4". That's acceptable, but a real description is much better.

---

## 3. `stripe_link`: the Buy button

- **Empty (`""`)**: the piece shows **Ask about this piece**, which opens the contact form with the piece's name filled in. That's how every piece works right now.
- **Set**: the piece page shows **Buy** (it opens Stripe's secure checkout in a new tab) plus "Ask about this piece". The shop grid shows a small Buy button too. Only links starting with `https://buy.stripe.com/` are used; anything else is ignored, so a typo can't send people somewhere odd.

To make a Payment Link (in the Stripe Dashboard, once a Stripe account exists):
1. Open **Payment Links** and click **+ New** (or the **+** button → **Payment link**).
2. Choose an existing product or **+ Add a new product**: name, price and a photo. Click **Add product**.
3. Under options, turn on **Collect customer addresses** → **Billing and shipping addresses** and choose the countries you ship to. You can add shipping rates if you charge for shipping.
4. Optional: in **After payment**, keep Stripe's thank-you message or redirect back to `https://www.makersinspire.com/shop/`.
5. Click **Create link** and copy it (it looks like `https://buy.stripe.com/...`).
6. Paste it between the quotes of that piece's `"stripe_link"`, then rebuild and publish.

When a favourite is remade, the same link keeps working.

---

## 4. Rotation: show and hide, and why there's no "sold out"

- To take a piece off the site, set `"show": false`. Its page disappears from the shop, the home page and the sitemap, but the entry and its processed photos stay, so you can bring it back later by setting `"show": true`.
- To remove it for good, delete the entry (and its `photos/<slug>/` folder). The build then deletes its page and web photos.
- There is deliberately **no "sold" or "sold out" label**. Favourites can be remade, so a piece is either in the lineup or resting. If one sells and you won't remake it, just hide it. If you will remake it, leave it up; buyers can ask about timing.

---

## 5. Rebuild and publish

On a computer with the repo and Python 3 (plus Pillow for photos: `pip install pillow`):

```
python3 build.py            # makes the pages and the web-size photos
python3 build.py --check    # must say "up to date"
git add -A
git commit -m "Add EXAMPLE Moonstone Pendant"
git push
```

GitHub Pages publishes about a minute after the push. If the build stops with a message such as `missing photo` or a JSON error, the message names the file. The usual cause is a missing comma or quote in `pieces.json`, or a photo name that doesn't match.

### Hand it over
Prefer not to do any of that? Send Noah's assistant:
- the photos (originals, in order), and
- for each piece: name, metals, stones, description, details, price (or "TBD"), the Stripe link if there is one, a one-line description of each photo if you'd like to write the alt text yourself, and whether it should be featured on the home page.

It gets added, built, checked on a phone and published, and you'll get the link back.
