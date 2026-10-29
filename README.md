# DermaLens (Milestones 1-7: backend, website, Analyzer, concerns, Compare, Dupes, Routine and Accounts)

A cosmetic ingredient classifier. Milestone 1 is the Flask + SQLite backend, a seeded
database (187 ingredients, 27 demo products, per-category ingredient tables) and tests.

## Run (Windows / Mac / Linux, Python 3.11+)
```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m seed.load             # creates dermalens.db with sample data
python -m pytest -q             # should show 78 passed (the OCR test is skipped if Tesseract is missing)
python -m app.main              # API on http://127.0.0.1:8000
```
Open the WEBSITE at http://127.0.0.1:8000/  (keep the terminal open; Ctrl+C stops it).
Raw API examples: /api/search?q=serum , /api/categories/lipstick , /api/ingredients?q=glycerin

## What the website has now (milestone 2)
Header with name + search (autocomplete), home page with product-type tiles, category pages
(basic ingredients with typical min/max %), product pages (label-order ingredients, clickable
ingredient details, what's-inside tags, basic safety summary, where-to-buy table), ingredient
encyclopedia. Accounts are added in milestone 7.

## Ingredient Analyzer (milestone 3)
Open http://127.0.0.1:8000/#/analyze . Paste a list, click "Try an example", upload or drop a photo of a
label, or use the camera. Each ingredient gets categories, a green/yellow/red rating and a reason;
you also get an overall verdict, flags, "what it does", clashing pairs, and a list of unrecognised ingredients.

How it works (good viva material):
1. Split the text (handles label line-wraps) and normalise names (lowercase, strip accents/punctuation).
2. Match against ingredient names and aliases: exact first, then fuzzy (difflib, cutoff 0.88) to fix typos and
   OCR slips. Fuzzy matches are shown as "matched approximately". The cutoff is strict on purpose: for a safety
   tool, "not recognised" is better than a wrong match.
3. Rate each ingredient and build the verdict with fixed rules over the ingredient table (irritancy,
   flags, comedogenic score, clashes). Same input always gives the same output, and every point has a reason.
4. Unknown ingredients get a SUGGESTED category from keyword rules, else a small ML model (TF-IDF character
   n-grams + logistic regression), always shown with a confidence.

Evaluate the ML part: `python -m eval.evaluate_classifier` (leave-one-out cross-validation).
On the sample table it scores about 46% accuracy from names alone. That is low because a name is weak
evidence for many categories, which is exactly why the app labels it a suggestion with a confidence
and prefers keyword rules when one applies. Say this honestly in your viva; adding real data would help.

### Reading photos (OCR)
Photo reading needs the free Tesseract program on your computer, in addition to `pip install -r requirements.txt`:
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki (tick "Add to PATH"), then restart the terminal.
- Mac: `brew install tesseract`.  Linux: `sudo apt install tesseract-ocr`.
Without it, the site shows a clear message and you can still paste text. OCR makes mistakes, so the text
box is editable before you analyse. Camera access needs http://127.0.0.1 or https (browsers block it elsewhere).

## Skin-concern recommendations (milestone 4)
Open http://127.0.0.1:8000/#/concerns . Pick a skin type and up to 4 concerns (pigmentation, acne, dryness,
fine lines, dark circles, redness, oily skin, dullness, large pores, sensitive skin). Optionally say what you
avoid (fragrance, parabens, nut oils, any ingredient names) or that you are pregnant, and filter products
by type, price and fragrance-free.

You get: the best ingredients per concern (first-line / good option / supporting) with why they help,
how to use them and cautions; what to avoid; combined tips (sunscreen reminder, ingredients that clash);
then products from the database that contain them, ranked by a score you can open and read.

How the score works (rule-based, so it is explainable):
- Ingredient weight = sum of its priority (3, 2 or 1) over your chosen concerns; lowered by 1 for sensitive
  skin when the ingredient is a known irritant.
- Position factor = 1.0 if in the first 5 on the label, 0.7 if 6 to 10, else 0.4 (earlier = more of it).
- Product score = sum(weight x position factor), minus 1.0 per irritant it contains that was not recommended
  (sensitive users only). Products with anything you avoid, or pregnancy-flagged ingredients if you tick
  pregnant, are removed.
The concern guidance in `seed/concerns_data.py` is general educational guidance written for this project,
not a clinical guideline. Say so in your viva and cite real sources (dermatology textbooks, AAD pages,
review papers) in your report; the app also shows a "not medical advice" note.

## Compare two products (milestone 5)
Open http://127.0.0.1:8000/#/compare (or click Compare on any product page). For each side choose a product
from the database or paste an ingredient list. You get a verdict ("Better overall: X" or "Too close to call"),
the reasons, an at-a-glance table, which skin types and concerns each suits, shared vs unique ingredients and a
category breakdown.

The scores are fixed rules, so every number can be explained:
- Safety (0-100) = 100 minus one penalty per ingredient, using the biggest that applies: 12 high irritation,
  7 can irritate, 6 fragrance/essential oil, 5 drying alcohol / pore-clogging / pregnancy caution, 4 sulfate /
  common allergen, 3 paraben. Position on the label is ignored, since allergens act at low amounts.
- Benefit (0-100) = 2 x points for useful groups present (barrier lipids 10, UV filters 10, humectants 8,
  antioxidants 8, soothing 8, peptides 6, brightening 6, exfoliants 6, retinoids 6, emollients 4), capped at 100.
- Overall = 0.6 x safety + 0.4 x benefit; a gap under 4 points is a tie.
- Skin-type suitability uses simple rules (e.g. sensitive = no fragrance, drying alcohol or strong irritants).
Limits to mention honestly: ingredients we do not recognise are not scored (the page says how many), and
comparing different product types (a serum vs a cleanser) is only a rough guide.

## Dupe finder (milestone 5)
Open http://127.0.0.1:8000/#/dupes (or "Find dupes" on a product page). Similarity = 60% ingredient match
(shared / all ingredients, water ignored) + 40% attribute match (key-ingredient-group overlap and agreement on
fragrance, sulfates, parabens, silicones, alcohol, essential oils). Only products of the same type are
compared; results show price difference, shared ingredients and what is missing, with a "Cheaper only" filter.
A high match means similar ingredients, not an identical formula.

Seeding again (`python -m seed.load`) now restarts product ids at 1, so product links stay stable.

## Routine builder (milestone 6)
Open http://127.0.0.1:8000/#/routine , or click "Add to routine" on any product page (sunscreen goes to AM,
serums to PM, cleansers and moisturisers to both). Build AM and PM routines, set how often each product is used,
and reorder or remove steps. You can also paste the ingredients of a product that is not in the database.
Your routine is saved in this browser (localStorage), no login needed.

The check runs automatically and uses the same `incompatible_with` data as the Analyzer:
- Clash: two products in the SAME slot with incompatible ingredients (e.g. retinol with glycolic acid).
  In different slots (vitamin C in the morning, retinol at night) it shows a "good" note instead.
- Weekly schedule: products used less than daily are placed on days that avoid clashing partners
  (e.g. retinol Mon/Wed/Fri, acid Tue/Thu). A clash is only a warning if the schedule cannot avoid it.
- Also checked: no sunscreen in the morning when acids, retinoids or brightening actives are used; a retinoid
  in the morning; two or more strong exfoliants used daily; the same active in several products.
- Suggested order: cleanser, serums, moisturiser, sunscreen last in the morning.

"Create share link" saves the routine (product ids, frequencies and the routine name only) and gives a link
anyone can open read-only, with a button to edit their own copy. Shared routines are kept when you re-seed.
"Download as image" draws the routine to a PNG in your browser.

## Accounts, profile and contributions (milestone 7)
- Sign up / log in at `#/login`. Passwords are stored only as salted hashes; sessions use a signed token
  (set `DERMALENS_SECRET` to keep logins valid across restarts, otherwise a random secret is made).
- `#/me`: skin profile (skin type, up to 4 concerns, ingredients to avoid, pregnancy toggle), shelves
  (I own this / Want to try / Used before), liked and avoided ingredients, saved Analyzer history,
  your contributions, and "Delete my account".
- Product pages show a "match for you" score once your profile is saved, and have shelf buttons.
- `#/submit`: add a missing product (name, brand, type, full ingredient list). It stays pending until an admin approves it.
- "Suggest edit" on a product sends a correction to the admin queue.
- Admin: sign up on the site first, then run `python -m app.make_admin you@example.com` in `backend`.
  Admins see the review queue at `#/admin` (approve or reject products and edit suggestions).
- Navigation: a Home link in the menu and a "Back to home" button on every inner page.

## Deployment
See `DEPLOY.md` (GitHub + Render, Dockerfile included, free-tier limits explained).

## Frontend note
The website is plain HTML/CSS/JavaScript in `backend/static/` (no Node or npm needed). The original
prompt asked for React + Tailwind; the build workspace could not install them, so this version has
no build step. It can be ported to React later.

## Honesty notes (explain these in your viva)
- All products, brands, prices and retailer links are FICTIONAL sample data (`is_sample_data`).
- Ingredient min/max values are approximate TYPICAL RANGES, never exact amounts in a product,
  because a label only shows ingredient order.
- Irritancy / comedogenic scores are rough educational estimates, not medical ratings.
- Only 187 ingredients are seeded (the prompt asked for 300+); add lines to
  `seed/ingredients_data.py` or write a loader for real data (Open Beauty Facts, EU CosIng).

## Stack change
The original prompt asked for FastAPI + SQLAlchemy. The build workspace could not install them,
so this version uses Flask + sqlite3 (standard library). The API shape is the same.
