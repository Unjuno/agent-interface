# Writer UNO compare-replace v1 plan

H: exact whole-document `replaceAll(^book$ -> bookkeeperoffice)` narrows stale precondition + mutation into one UNO RPC and avoids the demonstrable lost update of a two-RPC `read book -> later set desired` baseline when another UNO client appends `x`.

T: after development calibration, freeze source and run four fresh private Xvfb/Openbox/Writer blocks. Each block runs fixed conditions: `baseline_gap`, `append_then_replace`, `replace_then_append`, `race_simultaneous`, `race_candidate_delayed`, `race_append_delayed`, `stale_uid`. Each helper uses an independent `/usr/bin/python3` UNO connection. Baseline observes `book`, then a competing append completes before its unconditional set. `append_then_replace` waits for the competing append to complete before invoking one `replaceAll`; `replace_then_append` completes the replace before starting append. Three barrier races vary client delay but do not infer server order from delay or timestamps; either serializable outcome is accepted. A fresh third UNO client reads final text. No XTest text input, model, provider, or network.

D: retain candidate only if baseline reproduces lost completed append in all four blocks, `append_then_replace` preserves `bookx` with count=0 in all four, `replace_then_append` -> count=1/`bookkeeperofficex`, all three concurrent races are always one of those two serializable outcomes, and stale RuntimeUID refuses without mutation. No hybrid or completed-append loss is allowed in candidate arms. This is not proof of a general UNO transaction guarantee.

C: Writer search regex scope and UNO server request serialization are implementation-specific; a mutation after replace can still change final state. `replaceAll` searches the document container and can replace multiple matches outside this one-paragraph fixture.

U: one Writer document shape, one host, four blocks. No OS-input equivalence, general atomicity, other Office apps, Wayland/Windows/macOS, model/token claim.
