# V39 per-key cleanup bridge A05: out-of-order context retention

## H / T / D / C / U

- **H:** A cleanup bridge keyed only by the most recent program/step context will misattribute a delayed release when two keys admitted by different steps are cleaned up in reverse order; the A04 actuation-ID map should preserve both original contexts.
- **T:** One frozen in-memory candidate invocation against the immutable A04 bridge source. Two distinct keys receive distinct actuation IDs and program/step contexts; owner cleanup records arrive in reverse admission order. Compare with a deliberately weaker last-context baseline. No owner thread, display, OS input, game, or model is used.
- **D:** PASS only if the baseline misattributes the older cleanup, while A04 emits exactly two confirmed release measurements in observed cleanup order with each original program/step and identity, then retires both contexts/actuations and held keys. Any cross-binding, duplicate, unscoped mismatch, or remaining state fails.
- **C:** In-memory, deterministic source-composition evidence for two admitted keys. It does not establish an actual owner schedule, production deployment, real X11 behavior, application consumption, threat response, recovery benefit, or live runtime performance.
- **U:** No GUI, game, physical input, model, task effect, or latency benefit is measured.

The candidate is a single one-shot process in the pinned Python container. The independent auditor reads only its retained raw/result and frozen inputs; it does not invoke the candidate.

## Result

**PASS_OUT_OF_ORDER_CONTEXT_SCOPED.** In the one retained candidate run, cleanup arrived `act-b` then `act-a`. The last-context comparator misbound the older `act-a` release. Frozen A04 emitted both releases in observed order with their original distinct program/step contexts, confirmed up edges, and no authority; held keys, active actuations, and contexts were empty afterward. The independent audit reports `baseline_misbound_releases=1` and `a04_correctly_bound_releases=2`.

The tested source is a byte-for-byte copy of [`map01_v39_perkey_bridge_a04_cleanup_identity_guard_20261005/bridge_a04.py`](../map01_v39_perkey_bridge_a04_cleanup_identity_guard_20261005/bridge_a04.py), pinned at base commit `794fca066ce9fecc52c26cdc0b536eef9ae4abf8` with Git blob `f20d0cde1c62a419a8ceee3b2ecda743e2351be9`.

Raw output SHA-256: `26ab7024cffae727e6959073b7b9d90adf2c3f57524a19086a352cbb9db69d67`. Independent audit: `results/a05/AUDIT.json`. Freeze SHA-256: `4facf215f8c8cee393f3d69714d69e91191b28f8053e4c7c96491ec48232adab`. The separate mount-path STOP is preserved at `results/preflight-stop-01/`; it failed before any candidate case and is not included as a scientific outcome.

This result only demonstrates the two-key in-memory composition. It does not establish owner-thread scheduling, production integration, X11 behavior, application effect, threat response, recovery benefit, live correctness, or latency. The bridge still needs current-source deployment and end-to-end evaluation under a separately authorized allocation.

## Reproduction

From this directory, run `python3 build_freeze.py`, then run the frozen `candidate_command` in `FREEZE.json` in the pinned image, mounting this source directory at `/src:ro` and `results/` at `/results:rw`. Finally run `python3 audit.py --out results/a05` on the host. The preflight path error is retained under `results/preflight-stop-01/`; it executed zero candidate cases. Do not reuse the candidate result directory or rerun it after a retained outcome.
