# A12: explicit focus recovery with an ordinary file effect

First allocation: `5260-a12-wslc-private-gui-file-recovery01-20261004`.
Successor research for Issue #5260, extending A11 without modifying its evidence.

The first six fresh private Tk applications and first independent frozen audit
returned METHOD_PASS_FINITE_FIXTURE_ONLY / H_PASS_FINITE_FIXTURE_ONLY.
Both stable and both recovery cells saved exact target text (hmt/hns); decoy
remained empty. Both observed-drift refusal cells emitted zero keys/Save and
created no task file. Recovery retains the original refusal and requires one
explicit recovery click and a new bound ACK; old admission is not reused.

## Evidence and reconstruction

`FREEZE.json` is the prospective 46-file source freeze; source commit
bdab824dc95c637cc8fdf9045cc6996f6cff8bae. Frozen source is not modified by delivery.
`INHERITED.json` identifies 18 byte-identical A11 source files.
`retained/` contains 42 original files copied without byte changes from the
first candidate and independent auditor, including XWD frames, ordinary task
files, process/pipe traces, exact launch streams, attempts and UTC receipts.
`SHA256SUMS` covers all delivery files except itself.
`verify_packet.py` is post-run data-only verification, not the first audit.

Run from this directory:
```sh
python -B -m unittest discover -v
python -B verify_packet.py
```
These commands do not re-run the formal candidate or emit desktop input.
The real-Tk construction test requires a private Linux DISPLAY; Windows/no
DISPLAY explicitly skips that test. Synthetic construction tests are not GUI
evidence. Retained verification reconstructs the first audit and checks nine
copied-record corruptions, manifest, receipts, source binding and warning bytes.

## Scope

Finite private instrumented fixture only. No same-model/heldout task quality,
recovery token cost, public focus oracle, physical desktop release, natural
drift rate, human tempo, optimal delay, population or performance claim.
No atomic focus-and-key guarantee or crash-durability claim. CPU/memory flags
are requested, not proven enforced; the original WSL swap-limit warning is
retained. No claim that this improved OOM or iteration speed. No runtime default
is changed. #5260, #59 and the full roadmap remain open.

