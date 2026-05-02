# Version Control Guide

Use this format when adding new features:

## Version naming
- `v1.2.0` = feature update
- `v1.2.1` = bug fix only
- `v1.3.0` = next new feature

## Branch naming examples
- `feature/simple-costing-discount`
- `feature/manual-sheet-override`
- `fix/packaging-capacity-calculation`

## Commit message examples
- `feat: add discount input to simple costing`
- `feat: add manual print sheet override`
- `fix: use full sheet qty when cricut cut is unchecked`
- `fix: calculate packaging cost using capacity`

## Recommended workflow
1. Create a new branch for each feature.
2. Make only one feature per branch.
3. Test the Quote Calculator and Simple Costing before merging.
4. Update `CHANGELOG.md` and `VERSION` before creating a new zip.

## Current version
Current version: `v1.2.0`

Included features:
- Cricut cut toggle in Simple Costing
- Full Sheet Qty vs Cricut Safe Qty logic
- Capacity (stickers per package) in Simple Costing
- Packaging cost based on capacity
