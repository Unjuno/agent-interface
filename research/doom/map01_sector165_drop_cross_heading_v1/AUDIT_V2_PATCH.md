# Audit v2 correction

The original source-first `audit.py` failed after all 8 formal cases completed because it referenced a non-existent `plan['heading_groups_deg']` field. No live case was rerun.

Only this enumeration changes in audit v2:

```diff
- for heading in plan['heading_groups_deg']:
+ for heading in sorted({c['heading'] for c in plan['cases'] if c.get('heading') is not None}):
```

Everything else is inherited unchanged from source-first audit blob `76467293a9429e374c8a2fd210fe4616172b9dba`: source hashes, pixel metric, threshold, retained PNG evidence, release checks, heading tolerance/diversity checks and PASS/HOLD/FAIL semantics.

Local corrected auditor SHA-256: `c290eaab02d4cb39ad367a7fdceea3b72de0246b2d6312859914b9c77c4f967d`; Git blob identity in the retained archive: `8d0a39f9de691cd81ad8c2575e4b44375919a33f`.

Corrected read-only audit result: `PASS_AUDIT / HOLD_PIXEL_DROP_VIEW_DEPENDENT`, 4 positive misses, 0 wall false positives, heading span 31.640625deg.