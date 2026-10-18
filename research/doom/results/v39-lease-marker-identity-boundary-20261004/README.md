# V39 lease-marker identity boundary construction

This construction check found a false-positive release receipt in the current
v39 telemetry wrapper. Its admission table was keyed by `id(lease)` and key,
but retained no reference to the lease object. After an admission, a distinct
lease reuses the same Python object ID, its unmatched `up` consumes the old
marker and can report `ordinary_release_candidate=true`.

## H / T / D / C / U

- **H:** An admission marker keyed by a recyclable integer object ID can be
  consumed by a different lease and incorrectly authorize an ordinary-release
  candidate.
- **T:** Run two distinct lease objects through the exact wrapper, force their
  IDs to collide, admit key `w` only under the first, then issue `up` under the
  second. Separately probe whether this CPython runtime naturally reuses an
  object ID within 10,000 small-object allocations.
- **D:** The pre-fix wrapper fails if the second lease receives an ordinary
  release candidate without its own admission. The corrected wrapper passes if
  both history-complete and ordinary-candidate fields are false. The added
  cleanup regression checks that bulk owner release discards retained lease
  references.
- **C:** Forced ID collision is a deterministic boundary construction, not a
  claim that a particular application schedule will trigger reuse. The initial
  standalone allocator probe observed reuse, but the retained combined runner
  did not reproduce it in its own 10,000 attempts. Natural reuse is therefore
  not used as a result claim; the forced-collision case establishes wrapper
  behavior if that legal identity collision occurs.
- **U:** No actual X11 state, physical key state, GUI, game, model, container,
  latency distribution, or formal allocation was exercised. This verifies only
  a telemetry provenance boundary in a deterministic fake owner.

## Result

Current pre-fix source is pinned to parent PR #7376 commit
`cf4904c678830ebe1de84ec34c07df01f8be8b34` and blob
`99dfc7c9907b018e7473bc2ba8a7393a5b221f51`. The regression first returned red
against source blob `0ae95b4e901aa47f8ccd1cb033eea11989ea0cc2` at commit
`92b1c5f1c1a3f9565d88bd7ab0536811ac678d1c`; the intervening parent change
pruned completed markers and ordered cleanup by timestamps, but retained the
same recyclable `id(lease)` key. The deterministic
counterexample returned `owner_release_history_complete=true` and
`ordinary_release_candidate=true` for the distinct, non-admitting lease. The
first standalone CPython probe observed natural object-ID reuse, while the
retained reproduction's later bounded probe did not; this inconsistent auxiliary
observation is preserved and not promoted. The patch keeps the admitted lease
object in the marker, requires object identity at `up`, and discards that lease's
markers when bulk owner release is reported.

The corrected wrapper's focused tests pass **15/15**, including the new forced
collision and marker-cleanup regressions. The forced-collision regression fails
on current parent commit `cf4904c6` (`owner_release_history_complete=true`)
and passes on this patch; `RED_CURRENT.txt` retains that latest RED output.
`RED.txt` retains the earlier first RED. The retained real owner-queue
cancellation/expiry interleaving tests pass **5/5**. `py_compile` and
`git diff --check` pass.
This is a local construction result only; #59's live threat-control,
physical release, independently useful feedback, bounded recovery, and MAP01
exit gates remain open.

## Reproduction

From a checkout containing the pinned Git object, run the pre-fix counterexample
and the corrected candidate:

```powershell
python -B research/doom/results/v39-lease-marker-identity-boundary-20261004/reproduce.py
python -B research/doom/results/v39-lease-marker-identity-boundary-20261004/reproduce.py --source-file research/live_control/input_transition_owner_v3.py
python -B -m unittest research.live_control.test_input_transition_owner_v3 -v
```

`INITIAL_ATTEMPT.json`, `BEFORE.json`, `AFTER.json`, `RED.txt`, and
`RED_CURRENT.txt` preserve the first counterexample, latest RED, and later
reproduction outputs. `FREEZE.json`
pins the pre-fix source and environment. The change is stacked on PR #7376 and
does not modify its branch.
