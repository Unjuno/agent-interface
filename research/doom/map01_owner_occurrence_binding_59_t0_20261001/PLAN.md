# #59 input-owner occurrence-binding T0

## H / T / D / C / U

- **H:** The pinned #5630 `input_owner_v11.py` can admit two sequential presses of the same key under one owner/intent, but its returned admission and release records do not bind both halves with a per-occurrence identifier, and explicit `up` does not take a per-interval XQueryKeymap sample.
- **T:** Invoke the unchanged pinned `InputOwner` implementation on one fake Xlib transport for `W down → W up → W down → owner terminal release`, same lease/intent. Retain both admission replies, the owner records, fake-server key events and keymap-sample count. One candidate process, then a separate raw-only auditor; no retry.
- **D:** Confirm the boundary only if two admissions and two same-owner/keycode/intent release brackets appear in order; neither side carries an occurrence ID; explicit `up` has no keymap sample; only terminal cleanup yields a verified-empty snapshot. A mismatch is `FAIL_UNEXPECTED` or `FAIL_AUDIT`.
- **C:** Experiment main anchor `871c0aca73fae16552977975f584c7d3c6ed56a8`. Unchanged owner source pinned to PR #5630 head `288d0498d11cf16657e523a04616bf4f49cd94f4`, SHA-256 recorded before run. Windows host, CPython 3.12.10. Fake in-process Xlib protocol only; CPU-only.
- **U:** This tests the actual owner Python control path with a fake transport, not an X server. It does not establish real XTest/XSync timing, keymap behavior, physical occupancy, application delivery, useful effect, safety, latency, GUI, gameplay, Docker or MAP01 performance. No real input is emitted.

## Frozen trace and interpretation

The sequence is intentionally one explicit up followed by one owner-terminal cleanup release. This should yield two distinct release brackets but only a final empty sample, making clear which fields are owner-authored versus fabricated by a downstream adapter. The terminal cleanup record preserves keycode and intent but sets the key name to null. A successful boundary result means a live instrument needs a stable interval ID generated at down admission and carried through release, plus a sampled key-state witness appropriate to each interval; owner/intent/key alone repeat across intervals.

## Procedure

1. Run `python candidate.py` once; retain raw JSON.
2. Run `python audit.py` once in a separate process; retain audit JSON.
3. Do not repeat this allocation. A failed setup or unexpected first outcome stays immutable.
