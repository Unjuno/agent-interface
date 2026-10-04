# Scorer feedback attribution construction T0 A01

## H / T / D / C / U

**H:** A positive independent scorer event can be associated with one input intent only when a conservative per-key interval from input admission (before the side effect) through verified release/XSync completion covers the entire interval between the preceding scorer sample and the event sample, and no other intent may overlap that interval. Partial timing, a missing bracket, or unverified release evidence must remain unresolved; overlap across intents must remain ambiguous. Even a unique temporal association does not establish that the intent caused the outcome.

**T:** Run six fixed synthetic cases through the standalone candidate: complete one-intent coverage (including contiguous keys under one intent), partial coverage, two-intent overlap, missing coverage, an unverified old release that may persist, and a gap between keys. Unit tests also reject a timestamp not present in the scorer samples and a duplicated per-key interval.

**D:** `PASS_SCOPED` only when every fixed expected disposition matches and no case promotes temporal association to causation. Any unresolved/ambiguous case receiving an intent token is a failure.

**C:** The interval join may be too conservative to produce useful labels; that is preferable to claiming identity from sample proximity. A fresh integrated run may have richer producer-side action IDs and may not need this posthoc join.

**U:** Synthetic mechanics only. No retained live outcomes were reprocessed; no current controller/session integration, game, model, GUI, input, or resource allocation was used. The assay says nothing about scorer accuracy, useful task effect, effect latency, safety, survival, recovery, or MAP01 completion.

## Result

The candidate emits `TEMPORALLY_UNIQUE` only for complete, verified coverage by one intent. Partial or absent coverage is `UNRESOLVED`; intersecting intents are `AMBIGUOUS`; an unverified release cannot be treated as an endpoint. Every row includes `causal_attribution: NOT_ESTABLISHED`.

The first test run failed as expected because the implementation module did not exist (6 failing tests). After implementation, the exact suite passed 9/9. See `RESULT.json` and `AUDIT.json`; source identities and dispositions are fixed in `FREEZE.json`.

## Reproduction

From this directory:

```powershell
python -m unittest discover -s . -v
python run_t0.py
python audit.py
```

This is a reusable construction contract for the prospective #59 measurement path, not a live-control result. The live lane remains unassigned and this T0 does not consume it.
