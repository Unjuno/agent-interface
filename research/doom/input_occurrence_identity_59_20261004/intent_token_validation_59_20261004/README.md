# Reject missing intent identity in the occurrence reducer

## H/T/D/C/U

- **H:** The reducer accepts an admission/release pair whose matching `intent_token` is `null`, absent, empty, or whitespace. A positive event can then be reported as covered by one possible intent despite having no non-empty semantic identity.
- **T:** Run a regression against PR #7546's exact head, then run the focused reducer suite and its independent finite detection-bracket oracle after validating the token before interval construction.
- **D:** Baseline must fail the malformed-identity regression. The corrected reducer must reject missing, null, empty, and whitespace-only tokens; valid string tokens keep existing behavior. All 260 finite bracket cases must continue matching the independent oracle.
- **C:** This validates source-contract handling with synthetic records; it does not establish runtime producer integration or causal attribution.
- **U:** No game, model, GUI, input allocation, or live scorer rows were used. WSLc reported swap-limit support unavailable; requested memory enforcement is not claimed.

## Result

The exact baseline source is PR #7546 head `5f1e8ca5ddfae92c68530fd86668b811e65d2a12`. The new test failed there for null, empty, whitespace, and missing tokens: null/empty/whitespace were accepted, and missing identity raised an incidental `KeyError` instead of a schema `ValueError`. Raw output and exit status are in `out/red.txt` and `out/red-exit.txt`.

The repair requires a non-empty string `intent_token` before interval construction. The focused reducer suite passed 9/9 in cached WSLc; the existing independent oracle passed all 260 finite bracket cases. Results are in `out/green.txt` and `out/oracle-audit.txt`. The parent branch also added a regression confirming that a bracket after `admitted_ns` but before `input_ack_ns` remains possible, because the ACK follows the key event and XSync. This fixes malformed identity handling only and preserves the possible-envelope/no-causation limit.
