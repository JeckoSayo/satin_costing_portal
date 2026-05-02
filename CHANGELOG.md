# Changelog

## v1.2.0 - Combined Simple Costing Update

### Added
- Added **Cricut cut?** checkbox in Simple Costing Product Setup.
- Added dynamic sheet calculation:
  - Checked = uses **Cricut Safe Qty**.
  - Unchecked = uses **Full Sheet Qty**.
- Added **Capacity (stickers per package)** in Simple Costing packaging section.
- Added packaging calculation using capacity:
  - `Packages Needed = CEILING(Quantity Ordered / Capacity)`
  - `Packaging Cost = Packages Needed × Packaging Unit Cost`
- Added **Costing Mode** and **Costing Qty / Sheet** display in Simple Costing Result.

### Notes
- This version combines the earlier capacity update and the Cricut toggle update into one clean package.

## Suggested next version
- v1.3.0: Add discount input in Simple Costing.
- v1.4.0: Add manual sheet override.
- v1.5.0: Add packaging/manual stock deduction improvements.
