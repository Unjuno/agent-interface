# Writer UNO durable recovery v1 — retained first result

**Result ID:** `writer-uno-durable-recovery-v1-20260916-01`  
**Source/plan freeze:** `3dae0462c948e154d7d39910a7185dacc272e376`  
**Read-only upstream evidence:** PR #280 result/source head `86af75564997b8bb52a726ca956c94bc449d6b78`

## Disposition

**PASS_DURABLE_BOUND_RECOVERY / RETAIN_ODT_EFFECT_TRANSFER / HOLD_ATOMIC_AND_SAVE_UI_PROMOTION**.

Six fresh private Xvfb/Openbox/LibreOffice Writer sessions ran once each in fixed order `fresh`, `stale_uid`, `wrong_doc`, `focus_drift`, `stale_age`, `text_changed`. No arm reran and no model/provider/network call occurred.

| condition | recovery input | decision | in-memory A | post-exit ODT A | post-exit ODT B |
|---|---:|---|---|---|---|
| fresh | 28 events | accept | `bookkeeperoffice` | `bookkeeperoffice` | `bookk` |
| stale_uid | 0 | `STALE_DOCUMENT_ID` | `book` | `book` | `bookk` |
| wrong_doc | 0 | `WRONG_DOCUMENT` | `book` | `book` | `bookk` |
| focus_drift | 0 | `FOCUS_MISMATCH` | `book` | `book` | `bookk` |
| stale_age | 0 | `STALE_OBSERVATION` | `book` | `book` | `bookk` |
| text_changed | 0 | `STALE_TEXT` | `boox` | `boox` | `bookk` |

The fresh recovered text therefore survives durable native ODT serialization. Every bound fault refuses before recovery input and no recovery suffix appears in the durable artifact. The text-changed control deliberately preserves the injected `boox`; this is not counted as task success, only proof that refusal did not append `keeperoffice`.

## Independent durable scorer

After the measured recovery/refusal, the exact current UNO components are `store()`d strictly as fixture finalization. LibreOffice is then terminated. A separate regular-Python process that does not import or connect to UNO opens each ODT ZIP, runs ZIP CRC verification, parses `content.xml`, and compares paragraph text to the predeclared expected state. All 12 ODT reads pass.

UNO `store()` is **not** the text delivery route and this result does not claim safe X11 `Ctrl+S` targeting. It answers the narrower missing question from PR #280: whether the measured application state can be observed as the same durable document content after Writer exits.

## Controls

- frozen source readback: 10/10 exact Git blobs;
- unit tests: 5/5 PASS;
- formal sessions: 6/6 gates PASS;
- all sessions end with empty physical key/button state;
- B remains `bookk` in memory and on disk in all six sessions;
- every ODT ZIP CRC check passes;
- formal reruns: 0.

## Limits

This does not close the post-guard TOCTOU race retained by PR #282. The concurrent server-grab study addresses a different serialization boundary and is untouched. `store()` is fixture persistence, not evidence for save-keystroke routing. Private Linux/X11 Writer and lowercase ASCII only; no Unicode/IME, Wayland, Windows/macOS, broad Office reliability, model/token or end-to-end product claim.

## H/T/D/C/U

**H:** retained bound recovery/refusal state survives durable Writer serialization without adding a suffix on rejected arms.  
**T:** six source-frozen sessions; exact URL/RuntimeUID/text/age/XID/focus guards; independent non-UNO post-exit ODT scorer.  
**D:** scoped PASS because fresh is exact both in memory and on disk, all five faults emit zero recovery input and durable files match their expected preexisting/injected state.  
**C:** explicit UNO store is a fixture finalizer and could differ from user save workflows; termination and ODT serialization are application-specific.  
**U:** no atomicity, natural-race frequency or save-UI result; one private X11 environment.

## Successor

Do not repeat this persistence test. The next durable discriminator is transaction scope: determine whether application-internal mutation can be serialized/locked with a document-native mechanism, or otherwise require a fresh post-input effect observation before any durable commit/publish action. Keep the active X11 server-grab lane independent.
