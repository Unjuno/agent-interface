# Independent raw audit — A04

## H / T / D / C / U

- **H:** The saved A01 red and green results correctly demonstrate that unknown outer adapter rows invalidate the affected V39 edge receipt, with the unique known pair preserved.
- **T:** Verify the immutable raw A01 run outputs, source/test/fixture/runner hashes, baseline and candidate inventories, preserved prior STOPs, and mutation controls. This is a new auditor run after A02/A03 auditor protocol STOPs; it does not rerun either red or green regression test.
- **D:** One constrained WSLc audit must return `PASS_SCOPED_RAW_AUDIT`, verify every frozen raw input and 15 checks, and reject all three deliberate report mutations. Any infrastructure or assertion failure is retained without another retry.
- **C:** An independent raw auditor catches provenance mismatch and false relabeling, but has no access to the game or live input and cannot independently establish GUI/application effect.
- **U:** Audit of saved synthetic projector evidence only. No live X-server key release, physical dwell, application consumption, useful task effect, recovery benefit, or MAP01 completion is established.

## Frozen execution bound

One WSLc invocation, image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never --network none --cpus 1 --memory 512M`; source and evidence mounts read-only, a dedicated audit output mount. There is one audit attempt, no red/green rerun, no network, model, game, GUI, GPU, input, package install, retry, or swap-bound claim. The preceding A01/A02/A03 audit protocol STOPs are preserved separately.
