# V38/V39 per-key release-time identifiability — offline boundary construction

## Question

Do the retained input-owner state acknowledgement and outer hold-step completion
uniquely identify the physical key-up instant for one v39 hold step, or can
distinct release times satisfy the same explicit telemetry and declared hold?

This is a construction/boundary test of retained event observability, not an
X11 experiment and not a replacement for #5156's owner-thread key-up allocation.
The #5156 A07 allocation is STOP before candidate because resource ownership is
unresolved; no Docker/Xvfb/input, model, or game is invoked here.

## H / T / D / C / U

- **H:** For v39 `cover-1`, step 0 (`d`, declared 350 ms), the retained
  `keys_held.input_ack_ns` and `step_completed.completed_ns` permit more than
  one hypothetical key-up timestamp. If so, owner/event timestamps plus the
  outer completion timestamp do not identify exact per-key occupancy.
- **T:** Freeze current `main`, both v38/v39 raw event JSONL files, source code,
  tests and this plan by SHA-256. Parse the exact selected accepted command,
  held-state acknowledgement and step completion; enumerate two distinct
  release timestamps that satisfy the declared duration and precede outer
  completion. Pre-freeze tests cover fixture identity, missing records,
  impossible order and candidate multiplicity. Then run the frozen analyzer
  once. Standard-library host only; no candidate/runtime execution.
- **D:** `NON_IDENTIFIABLE_FROM_RETAINED_RELEASE_TELEMETRY` only if exact frozen
  source identities and selected row values match and at least two distinct
  hypothetical key-up times meet the declared minimum and fall before the
  recorded step completion. Source/identity/ordering mismatch is STOP. This
  does not infer which hypothetical time actually occurred.
- **C:** This compares explicit event timestamps and the declared hold contract.
  It does not prove the full image/game trajectory would be invariant under
  either counterfactual, and `step_completed` is only an outer boundary. Frames
  may indirectly constrain timing, but there is no calibrated independent
  visual-to-key-up model in this test.
- **U:** No physical key-up time, complete held-input occupancy, useful-feedback
  time, causal game effect, safety benefit, MAP01 completion or latency bound is
  established. The owner-thread timestamp/release experiment remains needed.

## Fixed fixture

- Base: current `main` `bcac9f7e5f7c49c44cd451a5331a510903097a9b`.
- v39 `cover-1` command step 0: key `d`, declared 350 ms.
- Held-state acknowledgement: `55511911802240 ns`.
- Outer step completion: `55512477276903 ns`.
- A possible key-up timestamp must be at/after the declared hold threshold and
  before outer completion. The construction does not treat either endpoint as
  the actual physical key-up time.

## Reproduction boundary

Run the source-pinned construction tests before freeze. After the freeze is
written, execute `python3 analyze.py` once. Preserve its exact `RESULT.json` and
all source/result checksums. Do not rerun or tune this allocation. The result
belongs in an additive evidence PR and is not a scientific/live PASS.
