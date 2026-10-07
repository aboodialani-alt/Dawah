# Dawah Study Library

Source for the published "Dawah Study Library" artifact.

- `site/` the published pages (index and Parts I to IX). This is the source of truth after the fact-check pass; edit these.
- `content/` the original JSON for Parts VIII and IX (before fact-check corrections), and `tools/build_part.py` which turned it into pages. Corrections were applied to `site/` afterwards, so regenerating from `content/` would lose them.
- `tools/` build, extraction and correction scripts (`extract_args.py`, `apply_fixes.py`, `apply_proofread.py`, `integrate.py`).
- `factcheck/` per-part findings (`results/`), what was applied or skipped (`report/`), and the proofreading pass (`proofread/`). `report/skipped.json` lists the 176 findings still needing a human look.

Fact-check limits: sunnah.com and Wikipedia were blocked, so most hadith numbers and gradings were not checked against the source.
