# Rescue qualification — Issue #5442 T4 mechanical boundary (2026-10-03)

This is a custody-only transfer from Draft PR #5650, source head
`117f493f95ffe07b9e657aeaf9a4e090af2a5e94`. All seven original package files
are retained byte-for-byte. The stale source-branch README snapshot is not
copied; current-main navigation/index content is updated additively.

## H / T / D / C / U

- **H:** The historical host-only probe found that the public kernel API could
  mechanically yield `stage=verified`, `effect_verified=true`, and
  `release_verified=true` without fields binding the receipt to goal intent,
  semantic target, pre/post state, or observer provenance. The source README
  explicitly limits this to mechanical evidence; it is not a kernel bug or
  semantic-success claim.
- **T:** From an isolated archive of the exact PR head, CPython 3.12.13 raw
  auditor tests pass 2/2 and all six entries in `SHA256SUMS.txt` verify. The
  current checkout is sparse and omits `runtime/kernel`; a direct test
  discovery there stopped with `ImportError`. I then extracted the exact
  frozen source commit `d00ffdd74cde6c7f113cb03382be853879d5cb65` into a
  temporary tree and reran its unchanged kernel suite: 18/18 passed. The
  historical PR's analysis-index, public-navigation, replay-gate, and
  research-workspace-index checks also passed.
- **D:** The immutable archived raw probe and audit match the retained SHA-256
  values. The source report describes two deterministic host-only invocations
  with the same mechanical outcome and four raw-auditor mutation controls.
  This recovery reran the audit tests, not the probe.
- **C:** No containerized simulator, GUI, model, application effect, live
  allocation, or backend dispatch was run in this recovery. The source report
  records that Docker was not started because no exclusive slot/owner could be
  established and unrelated clients appeared blocked; the fresh #5442
  JupyterLab experiment described in the Issue is a separate path and remains
  untouched. Formal experiment counts remain candidate=0, auditor=0,
  containerized-simulator=0.
- **U:** The probe does not authenticate evidence digests, establish observer
  fidelity, bind a real application intent/target to fresh pre/post-state, or
  prove end-to-end task correctness. The next application-backed JupyterLab
  work is distinct; it must retain its own freeze, actor plan, and outcome.

Issue #5442 remains open. Prior T0–T3 results and the merged T3 result are
unchanged. The initial runner/import/checksum invocation-location failures in
the source report remain intact; corrected historical checks do not erase
those failures or turn this host-only boundary into an integration result.
