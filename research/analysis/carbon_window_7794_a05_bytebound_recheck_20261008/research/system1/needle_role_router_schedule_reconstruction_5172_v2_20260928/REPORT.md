# #5172 Stage-0 v2 — digest-consistent schedule reconstruction controls

## H / T / D / C / U

**H.** The #5172 Stage-0 raw auditor should reject an altered base or per-arm schedule even when a mutator also recomputes the corresponding SHA-256 digest. This discriminates deterministic schedule reconstruction from a check that only catches a stale digest.

**T.** Fresh allocation `needle-role-router-audit-schedule-reconstruct-v2-20260928`; frozen intake main `5670372e20065d3d8286105ed4ea9615952b116f`. Test the exact merged auditor blob `be347a5315d204590b4e7c1d15be5c740e21bbb0` against the unchanged v1 synthetic fixture blob `480f0292b67ff49c5697dc2531584d40ceabb370` / SHA-256 `0bb775af12795bf812eec1b978a924223c149786267b982f485796abfc60cb71`. Deep-copy mutations alter and re-digest base indices, reorder and re-digest base indices, alter and re-digest an arm batch row, and reorder/re-digest arm batches. Positive control uses the unchanged raw. One host suite in Python 3.12.10; no model, optimizer, formal seed, Docker, network, or GUI.

**D.** `PASS_SCHEDULE_RECONSTRUCTION_MUTATION_SCOPED` requires unchanged fixture acceptance and rejection of all four digest-consistent corruptions with the specific reconstructed schedule mismatch reported (not merely a parse/canonical/digest-shape rejection). Any acceptance or positive-control refusal is `FAIL_RECONSTRUCTION_CONTROL`; identity or invocation mismatch is `STOP_PROVENANCE`. Zero fit/update calls are required.

**C.** The exact prior raw is held constant; only one schedule field changes in each deep copy, followed by independent canonical digest recomputation. The unchanged v1 result remains immutable. This tests the Stage-0 auditor against synthetic contract evidence and does not reproduce a PyTorch training trajectory. Docker remains unlaunched because the shared CPU/Docker lane has no exact lease and OrbStack inventory is unobservable.

**U.** A scoped auditor mutation result only. It does not establish model quality, training reproducibility, the online LoRA hypothesis, Docker portability, or formal allocation readiness. No formal seeds are allocated by this follow-up.

## Result

Status: **`PASS_SCHEDULE_RECONSTRUCTION_MUTATION_SCOPED`**.

- Exact v1 raw fixture accepted unchanged; all frozen input/auditor/test identities and the freeze sidecar verified.
- `python -B -m unittest -v test_schedule_reconstruction.py`: **6/6 passed**, exit 0.
- All four digest-consistent tampering controls were rejected with their specific deterministic schedule mismatch: changed/reordered base indices and changed/reordered arm batches. Each mutation recomputed the digest to match the mutated data, so stale-digest detection alone cannot explain the rejection.
- The auditor and its baseline raw fixture are byte-identical to the already-merged main artifacts. The prior Stage-0 package and result were not edited.
- No Docker, model, optimizer, training seed, `fit`, `run_seed`, or formal allocation was invoked.

Exact summaries and hashes are retained in `RESULT.json`. This follow-up improves the demonstrated audit boundary; it does not change the narrower claim or status of the prior Stage-0 report.
