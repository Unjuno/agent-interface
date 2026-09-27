# Real Writer UNO prefix recovery v1 — retained first result

**Result ID:** `writer-uno-prefix-recovery-v1-20260916-01`  
**Source/plan freeze:** `45c4c2f35bb9189fca3139a714b49bda7a3f499b`

## Disposition

**PASS_REAL_WRITER_BOUND_PREFIX_RECOVERY / REJECT_TEXT_ONLY_RECOVERY_AUTHORITY / REQUIRE_INSERTION_POINT_REACQUISITION / HOLD_PRODUCT_PROMOTION**.

Twelve fresh private Xvfb/Openbox/LibreOffice Writer sessions executed once: six conditions (`fresh`, `stale_uid`, `wrong_doc`, `focus_drift`, `stale_age`, `text_changed`) × weak text-only versus bound recovery. A began as `book`, B as `bookk`, desired A was `bookkeeperoffice`. Post-effect A/B text was independently read by a separate `/usr/bin/python3` UNO process.

| policy | fresh exact | fault accepts | fault zero-input refusals |
|---|---:|---:|---:|
| weak text-only | 1/1 | 5/5 | 0/5 |
| bound | 1/1 | 0/5 | 5/5 |

Bound refusal reasons were: stale same-URL reopened document → `STALE_DOCUMENT_ID`; wrong document observation → `WRONG_DOCUMENT`; focus drift → `FOCUS_MISMATCH`; expired observation → `STALE_OBSERVATION`; changed target text → `STALE_TEXT`. Every refusal injected zero recovery events.

Weak text-only accepted every fault. Wrong-document produced A=`bookeeperoffice`; focus drift sent the suffix into B, producing B=`bookkkeeperoffice`; changed text produced A=`booxkeeperoffice`. Same-URL reopen and stale-age happened to end with exact desired A, but still used invalid/stale authority and therefore remain unsafe comparator outcomes rather than successes.

## New mechanism boundary found before freeze

Correct document RuntimeUID/URL/XID binding was not enough: UNO Frame activation did not preserve an end-of-document caret, and development initially produced `keeperofficebook`. The frozen Writer-specific candidate therefore reacquires insertion position with `Ctrl+End` only after document/XID/focus guards, then sends the suffix. This is backend/application transport policy, not a common semantic-text rule.

## Controls

- GitHub source readback matched the 8 frozen source blobs before formal execution;
- local source hash check 8/8;
- candidate unit tests 5/5;
- 12/12 formal arm exit codes zero and predeclared gates pass;
- physical input empty after every arm;
- formal arm reruns: 0; model/provider/network calls: 0;
- canonical raw formal rows: 13,378 bytes, SHA-256 `757c2d9315ed169ef9d9fde6aa8cd32c39009a3ff75b4b5e2a4259cb2f940178`.

## Limits

UNO is a research application oracle/control plane here, not a product dependency decision. There is still no atomic observation-to-input transaction after the final guard. This is private Xvfb/Openbox/Writer, lowercase ASCII suffix recovery only; no durable-save result, Unicode/IME, Wayland, Windows/macOS, general Office, model/token or reliability claim.

## Decision

Application-reflected text alone is insufficient recovery authority. The observed prefix must remain tied to the same document instance and current input target, and the application insertion point must be reacquired before a Writer suffix is delivered. Sender telemetry is not used as the committed-effect oracle.
