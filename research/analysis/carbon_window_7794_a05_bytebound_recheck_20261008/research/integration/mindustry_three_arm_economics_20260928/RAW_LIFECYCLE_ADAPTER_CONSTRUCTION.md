# Private lifecycle → independent raw auditor adapter

Date: 2026-09-29 JST. Parent economics H/T/D/C/U and allocation remain frozen
in #5130/#1679. This is an additional local construction rung; not a formal or
live Mindustry result.

## H / T / D / C / U

- **H:** The actual host `PrivateBenchmarkChannel` can export its private reset
  snapshots, monotonic score/reset witness times, and A3→B1 geometry receipt in
  exactly the lifecycle shapes consumed by the independent v2 raw auditor.
- **T:** Run the frozen `ArmCoordinator` route and locator checks in lockstep
  with the private file-marker protocol across six tasks for each of three arms
  against an isolated fake mod worker. Capture host event times and full 112-tile
  snapshots; bind those lifecycle records to the existing task event fixture via
  `attach_private_lifecycle`; run `raw_allocation_audit_v2.audit` on the
  resulting JSON bytes and retain raw plus audit response. Model outputs and
  task traces remain synthetic. No Docker, Java game, real model, socket, real
  input, or formal allocation.
- **D:** PASS construction only if all 18 resets and 3 transitions are captured,
  strict score < request < witness < next-start ordering holds, and independent
  v2 reconstruction passes without adapter-generated timestamps or omitted
  evidence. Incomplete lifecycle input must refuse before producing a result.
- **C:** Frozen synthetic task events, route schedule and identity sentinels are
  held fixed; only lifecycle records are sourced from the separately exercised
  file-channel handshakes. The fake engine writes the exact protocol markers and
  snapshots but is not Mindustry.
- **U:** Demonstrates host adapter/protocol/auditor composition only. It does not
  prove the Mindustry Java mod emits these records correctly, that task/model
  events are truthful, that source bytes are pinned, or that any placement/game
  task occurred. Formal outcome remains unmeasured.

## Retained result

Run from this package directory:

```powershell
python -m unittest discover -s . -p test_private_benchmark_channel.py -v
python run_raw_lifecycle_adapter_construction.py raw_lifecycle_adapter_20260929_03
```

The immutable synthetic captures are in
`construction/raw_lifecycle_adapter_20260929_01/`, `_02/`, and `_03/`; `_01`
is the first adapter-contract capture, `_02` follows strict adapter guards, and
`_03` composes `ArmCoordinator` routes/locators with all three private-channel
handshakes and the auditor. `_03` raw SHA-256 is
`7ba248560ad0b837a7c47cc07fa76c2de9c6b4873da30360c40a6864713a9a24`; audit is
`PASS_CONSTRUCTION_ONLY`, hypothetical evaluator disposition `RETAIN`,
break-even task 2, with 18 reset projections and 3 geometry transitions. The
raw includes sentinels for source/model/game/container identities. Each runner
capture requires a new, unused directory basename.

The first channel timing test exposed equal consecutive `monotonic_ns()` values
on this host; the channel now emits strictly increasing monotonic event stamps
(advancing by 1 ns only when the clock repeats). Follow-up construction runs
found only fixture timeline mismatches and one assertion comparing a normalized
model-call list to an integer; those test defects were corrected. The final
six-task route coordinator + fake-channel handshake + v2 raw reconstruction
passes, including one refusal control for incomplete adapter input. The
persistent fake arm dispatches two model callbacks; plain and ephemeral dispatch
six each, and each task requires a newer locator observation before advancing.

The full integration package is 86/86 on the host; inherited evaluator probe is
`passed=true` / `RETAIN` / 10 controls; receipt no-GUI probe and Node syntax
pass. A py_compile check twice failed to create its transient `.pyc.<pid>` file
under the repository's `__pycache__`; test imports exercised the modified
modules successfully. One initial package-wide command was also launched from
the non-repository parent directory and ran zero tests; rerun from the worktree
passed 86/86 after the coordinator was added to the integrated channel test.
These are setup/tooling failures, not research outcomes.

No Docker was used because the #5130 exact container gate remains active under
#5085 arbitration. All verification was local; automated workflow results were
not used.
