# Issue #5970 T5 — X event target and mask-ownership diagnostic

## H / T / D / C / U

- **H:** The T3/T4 selected-window observer missed events because the focused Tk event recipient is an internal child/ancestor different from the Entry XID; additionally, the app client's existing core KeyPress selection may prevent a second client from selecting the actual recipient.
- **T:** Reconstruct the Tk window tree from the exact T3-derived app on private Xvfb without dispatching input. Independently query each window's `all_event_masks`, locate the Entry and any window with KeyPress selected, then from a second X client attempt a KeyPress selection on the Entry and on the app-selected target. Preserve IDs, parent relations, masks, and exact X errors. No XTest calls or physical input.
- **D:** `PASS_TARGET_AND_MASK_CONFLICT` only if the selected Entry differs from the focused app target, an app-selected target has KeyPress in `all_event_masks`, Entry selection succeeds from the observer connection, and selection on that target fails with BadAccess. `HOLD` if no unique target or masks; `FAIL` if observations contradict the frozen explanation. This is a mechanism diagnosis, not a recovery/effect claim.
- **C:** One Tk app, one isolated Xvfb, read-only tree/mask queries plus two observer event-mask selection requests. No key events are generated. Docker Desktop is preferred but the current engine has remained unavailable; use isolated WSL2/Xvfb and retain that deviation.
- **U:** Whether this exact source-derived fixture behavior transfers to deployed #4135 environments; whether a different capture architecture (RECORD, same-client instrumentation, or explicit XSendEvent routing) would provide useful/authorized provenance; whether this changes any recovery outcome or task effect.

## Frozen safety and one-shot rule

The only candidate runs are the no-input construction described above and it may run once after hashes/gates are frozen. No T3/T4 candidate is repeated. No action events, key state changes, formal allocation, or user desktop access. Retain all outcomes and an independent audit of the raw window/mask evidence.
