# Construction checks (not formal allocation evidence)

These checks occurred before the frozen source commit and are not counted as candidate/auditor formal invocations.

- An early writer-coverage mutation test cleared the listed external writer but initially left the completeness flag false. That only exercised the safe fallback, not a forged-complete manifest. The test was corrected to mutate both fields; the independent full-state auditor then detects the false-clean result.
- An early event audit required event writes to equal state deltas exactly. The delayed-save fixture contains a same-value write to `persisted:value`, so this was too strict. The final audit instead requires every changed cell to be explained by an event and every event value to agree with the observed snapshot; valid no-op writes remain in the frozen event bytes.
- After those corrections, the frozen fixture has 11 cases / 44 rows; all 9 construction tests pass, Python compilation and `bash -n` pass, and a host-only candidate/auditor smoke check independently reconstructs all 44 rows. The host smoke output is not a formal result and is not used as one.

No change to the hypothesis, scenarios, cost gate, or outcome thresholds was made after inspecting construction outcomes. The candidate/auditor one-shot allocation remains pending until the frozen source commit is posted on Issue #6533.
