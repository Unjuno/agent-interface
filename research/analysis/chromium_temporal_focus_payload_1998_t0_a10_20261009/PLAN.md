# T0 A10 prospective allocation — temporal focused evidence payload

**Allocation:** `LABEL-CONTROL-AMBIGUITY-1998-T0-A10-20261009`

**Parent:** Issue [#1998](https://github.com/Unjuno/agent-interface/issues/1998)

**Base:** A09 branch head `42daaae224f558731c3cf69ba4ffb8052d2c7f2a`, stacked on the open A04 evidence PR.

## H/T/D/C/U

**H — Hypothesis.** On the three retained Chromium frames in sequence 7–9, encoding the same fixed 140×17 input-field region at `[65,236]` as a temporal sequence preserves each region's exact source pixels and all three distinct observed pixel states, while reducing the total canonical JSON payload bytes versus one full-frame PNG per sample, including the additional focus metadata.

**T — Test.** Read only the three SHA-pinned original RGB PNGs. In one network-denied, read-only-root OrbStack container, independently crop the fixed ROI, encode each crop as RGB PNG, and record full-frame versus focused canonical-JSON byte counts. A separately implemented standard-library auditor checks source/crop identities, exact pixel reconstruction, chronological identity, payload accounting, and six in-memory mutation controls. Candidate once; auditor once only after candidate exit 0; no retries.

**D — Decision.** `PASS_METHOD_SCOPED` only if all three cropped pixel arrays exactly equal their source ROI, all three ROI pixel hashes are distinct, every focused payload is strictly smaller after metadata, and the independent raw-only audit has zero errors and rejects all six mutations. Otherwise retain the exact `FAIL`, `HOLD`, or `STOP` outcome.

**C — Competing explanation.** The apparent state sequence may depend on application-specific UI timing, and pixel changes alone do not establish token semantics or action completion. A focused ROI may also discard surrounding context needed for correct control.

**U — Uncertainty.** One archived successful Chromium trace; post-hoc selected fixed ROI; no new GUI run, task replay, OCR, model, user input, latency measurement, action policy, or runtime change. This tests temporal evidence preservation and payload bytes only. It does not establish that a controller can identify semantic completion or safely decide when to act.

## Frozen inputs and execution boundary

Input frames are original retained frames 7, 8, and 9 from `research/observation_gating/results/baseline-screen-02/chromium-1101-O0/frames/`. The action and observation ledgers and task oracle are read-only provenance. The ROI was selected post-hoc from A09's pixel-only diagnostic and is explicitly not an automatic ROI-selection result. The candidate uses the locally available Node image by digest with `--pull=never`, `--network=none`, a read-only root, read-only input/source mounts, a dedicated output mount, one CPU, 256 MiB memory, and 32 PIDs. The host auditor uses Python standard library under network denial. No container build, image pull, GUI, network access, OCR, or task replay is allowed after freeze.

Results are written only below this allocation directory. No A04/A09 result artifact is reused as a candidate output. The source screenshot bytes are reused only as immutable inputs for this distinct temporal-payload hypothesis.
