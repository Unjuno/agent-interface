# Scorer feedback attribution construction A04

## H / T / D / C / U

**H:** The positive useful event boundary must reject a missing, null, empty, or non-string `kind`; otherwise malformed event identity can pass the temporal candidate path and be copied to output.

**T:** Apply five malformed-kind inputs (missing, null, empty, whitespace-only, non-string) and one valid control to the A03 helper and A04 successor. Run the existing A03 boundary/envelope suite unchanged, with new negative cases added before implementation.

**D:** A03 accepts each malformed case as a possible envelope; A04 rejects all five with `ValueError`. The valid event retains A03's possible-envelope disposition. The full A04 local suite passes and its saved-result audit independently checks the serialized dispositions.

**C:** The source vocabulary includes event kinds such as `KILL_COUNT_INCREASE` and `MAP_EXIT`; this construction validates a nonempty string, not membership in an authoritative enum. Unknown but well-formed names remain accepted for forward compatibility.

**U:** Synthetic schema-boundary construction only. No live session, game, model, GUI, input, or allocation was used. A04 does not establish event provenance, producer/session identity, freshness, causal attribution, task effect, or recovery.

## Outcome

Test-first red: five malformed-kind subcases failed to raise under the A03 helper. A04 added a fail-closed nonempty-string check for positive useful events. Green: 15 local unit tests pass. The separate result comparison and saved-result audit are recorded in `RESULT.json`, `audit.stdout.txt`, and `FILES.sha256`. A03 remains unchanged in its own package.

Run from this directory with `python -m unittest discover -s . -v`, `python run_a04.py`, and `python audit.py`.
