# Satin Creative Studio Costing Calculator V3.2

This version keeps the original dashboard/design and adds a V3 product catalog for a small Canon G670 + Cricut print/craft business.

## What V3 Adds

- Sticker/custom costing dashboard remains available
- Product Catalog V3 for:
  - Waterproof sticker bundles
  - Small-batch logo stickers
  - Photo prints
  - Invitations/cards
  - Cricut crafts
  - Event packages
- Product Quote page with:
  - bundle pricing such as 4 for ₱100
  - small-batch logo tiers
  - capacity warnings for Canon G670/Cricut workflow
  - true cost, selling price, profit, margin, and price per piece
- Saved craft/product quotes
- Admin support for product categories, presets, and tiers


## What V3.2 Adds

- Smart minimum pricing by product type:
  - Sticker / Label
  - Photo Print
  - Invitation / Card
  - Cricut Craft
  - Event Package
  - Other Custom
- Size-based minimum prices so one small sticker does not always become ₱149
- Cricut / cut complexity selector:
  - Simple
  - Standard contour
  - Detailed / fine cuts
  - Layered craft / assembly
- Automatic setup fee and complexity fee in the costing formula
- Pricing Rule indicator in the Overview panel, showing when a minimum was applied
- Cleaner checkbox behavior for “Use Cricut safe area / Print then cut”

## V3.2 Smart Minimum Logic

Typical starting rules:

- Small stickers: ₱49+
- Medium stickers: ₱79+
- Large stickers: ₱99–₱149+
- Photo prints: ₱35–₱99+
- Invitation/card samples: ₱99+
- Cricut crafts: ₱149+
- Event packages: ₱299+

These are starting rules only. Tune them based on your real cost, local market, and turnaround time.

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py seed_v3_catalog
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Recommended Workflow

Use the original dashboard for detailed sticker sheet costing.
Use **Product Catalog V3** and **Product Quote** for real selling menu prices like:

- 4 for ₱100 waterproof stickers
- small-batch logo stickers
- photo prints
- invitations/cards
- Cricut cake toppers/custom names
- birthday/wedding starter packages

## Notes

The V3 product prices are starting presets. Tune them using your real materials, ink usage, customer demand, and daily machine capacity.

For Canon G670/Cricut, avoid blindly matching 500-piece wholesale competitors. V3 includes manual quote warnings for high quantities so you do not overload your printer/cutter.


## V3.3 Operations Edition

This build adds practical daily-operation features on top of V3.2 Smart Pricing:

- Quick Quote Presets for common products: 4-for-₱100 stickers, logo labels, product labels, 4R photos, invitations, and cake toppers.
- Chat Quote Generator for Messenger/Instagram/marketplace replies.
- Operations Snapshot with today orders, today revenue, today profit, and estimated lead time.
- Low Stock Alerts on the dashboard using each material's reorder level.
- Repeat Customer summary based on logged sales.
- Manual Override Price and Override Reason for repeat customers, promos, and fixed bundles.
- Preserved V3.2 features: smart minimum pricing, Cricut complexity pricing, custom dimensions, safe-area toggle, stock deduction, and sales logging.

Run locally:

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py seed_v3_catalog
python manage.py runserver
```


## V3.4 Daily Operations Edition

This build adds daily shop-management tools around the existing costing calculator:

- Order Queue / Job Board
- Due dates and rush orders
- Deposit and balance tracking
- Customer history and reorder
- Expense tracker and cashflow dashboard
- Stock purchase / stock-in log
- Printable job ticket
- Shop tasks / follow-ups

After migrating, use the sidebar links: **Order Queue**, **Cashflow**, **Expenses**, **Stock In**, and **Tasks**.


## V3.5 Analytics Dashboard Edition

Open `/analytics/` or click **Analytics V3.5** in the sidebar to view the modern shop analytics dashboard. No extra migration is required beyond the existing V3.4 migrations.


## V4 Modern Bootstrap Tour

This version includes a guided onboarding tour. It starts automatically on first visit and can be restarted from **Guided Tour V4** in the sidebar or the floating help button.

## V5 Smart Paste Edition

V5 adds Smart Paste: paste customer chat messages and convert them into quote-ready fields.

Run migrations:

```bash
python manage.py migrate
```

Then visit `/smart-paste/`.
