# V15 source integration and aliased release cleanup

This candidate brings the execution-facing source and focused tests from
[#8094](https://github.com/Unjuno/agent-interface/pull/8094) onto main
`decc1896e3e85ab2fdbb7ec4678f958eb6561d0f`, following
[#8243](https://github.com/Unjuno/agent-interface/pull/8243)'s source-only
integration recommendation. It also fixes the inherited resolved-keycode
collision demonstrated at a native excerpt boundary by
[#8250](https://github.com/Unjuno/agent-interface/pull/8250).

The original 1,467-file PR and its history remain intact. This change takes
11 source/prompt paths and 14 targeted test paths from exact head
`d0aa8463a10abf04d1b40cb4f498fc0a659fb827`, adds one alias regression module,
and keeps this evidence record separate. The old Python text is unchanged
except for the four-line alias guard (two comment lines and two executable
lines). Existing main line endings are retained for matching lines; added
lines use LF. The extraction manifest and byte-normalized comparison preserve
that distinction. No old raw, manifest or historical source is rewritten.

## Behavior

- Opt-in V15 measurement uses the current V12 owner through V4 and the ordered
  release backend. Measurement retains identity-bound keymap brackets, batch
  sample custody, and cleanup lineage without granting input authority.
- V39 retains exact public health/ammo feedback, binds invalidation to the
  corresponding frame, and preserves observation/cancellation while an expected
  stale-sequence cover renewal has no admitted input. These are the existing
  #8094 changes, including their regression tests; this extraction does not add
  a newly selected game policy or health threshold.
- Distinct logical key names resolving to one X keycode now raise `ValueError`
  before batch keymap sampling or any explicit UP. The hold stays owned for
  cleanup. The actual measured backend/Executor exception path publishes
  incomplete release telemetry, releases the physical code once, verifies a
  neutral state, and terminates the failed program. It does not claim two
  distinct physical DOWNs for one already-held code.

## Ordinary integration gate and observed result

**H:** The selected source can be integrated without losing its existing
contracts, and alias rejection can preserve cleanup through the actual owner,
V4, measured backend and Executor V13.

**T:** Current-main source/test extraction; real owner threads with fake Xlib;
four direct alias conditions (both name orders, measurement on/off), two
normal distinct-code controls, and one Executor hold through two logical
names remapped to the same physical code. Game-facing initialization and
snapshot capture are stubbed for this test. This is ordinary construction and
regression, not a prospective formal/native allocation.

**D:** The alias boundary must refuse before query/UP; the Executor must report
that specific error, preserve incomplete rows, and verify neutral cleanup with
no active lease. Distinct codes must continue to release normally. Existing
selected regressions must pass; no first failure is replaced.

**Observed:** 23 modules pass, with 183 test executions and 174 distinct methods
(the nine imported `KeyMeasurementTests` run twice). The new three-method alias
module covers seven cases and also passes under `python -O`. Twenty-two
workspace-index tests and the index check pass. The two scorer replay tests
are included in 183. All 25 changed Python files compile and `git diff --check`
passes. The runtime/test closure contains 95 pinned paths, unchanged during
the final regression run and unchanged between intake main and publication
snapshot `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.

The retained golden source audit exits zero but reports **HOLD_SOURCE_HASH_DRIFT,
3/5**. All five inspected files match unchanged intake main, so that historical
source drift is not repaired or relabeled here. The broad Native MCP CI suite
was not run locally; its explicit test list does not include these new tests.
No claim of full repository CI success or satisfied branch protection is made.

**C/U:** Fake X demonstrates this call-chain behavior under the supplied mapping;
it does not establish native X timing, physical HID behavior, application
consumption, live threat reaction, useful feedback/recovery, model cost or
MAP01 completion. The original #8094 native Executor audit remains **FAIL
337/338**, including its `only_loopback` failure. It was not rerun. The live
lane remains unassigned, and no game/model/display/GPU/VM allocation was started.
The overall goal and Issue #59 remain open.

## Retained failures and separate raw audit

`validation.tar.xz` contains all local regression logs, exact commands, source
locks, extraction/line-ending records, before-fix owner/test snapshots, and
saved-raw auditor versions. Initial RED reproduces all four alias failures.
The executor fixture initially lacked initialization fields; after fixture
repair it reaches the real path and incorrectly completes before the guard.
Post-fix test failures from nonexistent receipt fields and an assertion made
after cleanup are also retained. The corrected test checks the actual trace
and observed schema. These construction repairs do not change any formal
experimental result.

The separate saved-raw auditor v4 reconstructs four alias refusals, both distinct
controls, actual admission/terminal identity, the second DOWN's unconfirmed
measurement, incomplete UP rows, and a single verified cleanup UP. All three
executed copied-record mutations are rejected. Earlier auditor failures
(nonexistent receipt owner field and variable ordering) remain preserved.
This is coauthor technical verification, not a nonauthor review or merge vote.

The archive has only inert `.py.txt` script copies. `MANIFEST.json` names every
member and SHA-256. `RESULT.json` gives the archive digest, source tree and
counts. Read back the archive without executing anything:

```python
import hashlib, json, tarfile
from pathlib import Path
root = Path('research/doom/v15_source_integration_59_e0cc_20261007')
result = json.loads((root / 'RESULT.json').read_text())
assert hashlib.sha256((root / 'validation.tar.xz').read_bytes()).hexdigest() == result['artifact']['sha256']
with tarfile.open(root / 'validation.tar.xz') as archive:
    rows = json.loads((root / 'MANIFEST.json').read_text())
    assert len(archive.getmembers()) == len(rows)
    for row in rows:
        data = archive.extractfile(row['path']).read()
        assert len(data) == row['bytes']
        assert hashlib.sha256(data).hexdigest() == row['sha256']
```

To repeat the ordinary alias regression from a complete checkout, with the
project Python dependencies present:

```bash
PYTHONPATH=research/live_control:research/doom:research/observation_gating:research/observation_tiles:research/real_apps_v1:. \
  python -B research/live_control/test_input_owner_v12_batch_alias.py -v
```

The full 23-module list and actual commands are retained in
`final-test-modules.json` and `regressions-final/result.json` inside the archive.
This candidate is not merged. FINAL-v5 nonauthor content quorum and a fresh
exact-tree integration check remain required before main is updated.
