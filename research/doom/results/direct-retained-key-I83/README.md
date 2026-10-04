# Missing-key admission fail-closed repair — I83

**Disposition: `PASS_UNKEYED_ADMISSION_FAIL_CLOSED_CONSTRUCTION`; live telemetry remains gated.**

## H / T / D / C / U

**H.** Every recognized `input_admission` row must carry a key. If an admission row has an absent or null key, the trace must not be called measurement-ready, even when another valid admission/release pair exists.

**T.** On PR #7356 head `43fbe68ca60acc6c81c310db823528d417ad1a10`, test a valid pair alone and the same trace plus an admission with absent or null key. Preserve the failing first run, change only admission classification, then rerun the full parser suite and an independent before/after audit.

**D.** The valid control remains ready; each malformed-admission trace becomes not ready, with one invalid admission counted and the valid hold preserved.

**C.** This follows the live gate requirement that every admitted normal hold have a verified release and the analyzer contract that each pair carries a key. Malformed/unrecognized event schemas remain otherwise out of scope.

**U.** Construction only: no producer, X11, game, input dispatch, model, useful-feedback, recovery, or formal allocation ran.

## Result

The untouched analyzer returned `measurement_ready=true` for both traces containing a valid pair plus an admission row whose key was absent/null; it silently ignored the extra admission. The two regression subcases failed before the repair. The admission branch now records missing/null-key rows as invalid admissions. The full focused suite passes **10/10**, `py_compile` passes, and the independent raw-only audit reports `PASS_UNKEYED_ADMISSION_FAIL_CLOSED`: both false accepts repaired, valid control preserved, zero errors.

Commands from repository root:

```powershell
python -m unittest -v research.doom.test_analyze_map01_direct_retained_input_v1
python -m py_compile research/doom/analyze_map01_direct_retained_input_v1.py research/doom/test_analyze_map01_direct_retained_input_v1.py
python research/doom/results/direct-retained-key-I83/audit_key_boundary.py
```

