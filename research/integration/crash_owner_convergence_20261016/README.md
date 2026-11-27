# Crash-owner candidate convergence and current-path counterexamples

2026-10-16. Preservation/adoption review of PR #8876, not a new live allocation.

## Decision

Preserve the published evidence and historical candidate without adopting its
runtime changes. Its old controller/session snapshots must not replace newer
main, and its RPC codec/client is not qualified for the current selected
process-identity backend. Carry the remaining implementation and validation
under [#59](https://github.com/Unjuno/agent-interface/issues/59).

[ORIGINAL_PATHS.json](ORIGINAL_PATHS.json) maps all **614** changed-path head blobs
from PR head `0aca0e31216659a44f285b62db3edb3b5eb228b9` against its actual
merge base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Each original Git blob,
SHA-256, size and original path is retained. Content-addressed `.blob` files are
not importable Python, test-discovery modules, workflows or launchers. Deduplication
preserves original bytes; it does not alter raw. Seven unchanged dependencies
needed for the selected frozen-identity backchecks are separately listed in
[SUPPLEMENTAL_SOURCES.json](SUPPLEMENTAL_SOURCES.json). The archive occupies
3,386,584 bytes; original changed-path sizes sum to 9,507,380 bytes before dedup.
This is complete for that published diff, not all repository dependencies,
GitHub discussion or unpublished local work. Original branch/worktrees remain.

## Executed discriminator

H: directly substituting the archived RPC owner for the current selected owner
can lose target-generation authority and allow a later input request after an
unknown earlier outcome. T: execute exact archived codec/validation/client method
AST with the current Lease and an intercepted send/reply boundary; compare with
the actual current selected owner on Fake X. No service constructor, socket,
subprocess, X server, real display, game, provider or model is invoked.

D: adoption requires process/window bindings survive transport and no new input
send after an unknown/invalid reply. A valid original lease must still admit and
release on Fake X. Missing bindings must fail closed at the selected owner.
These are regression constructions, not consumed formal allocations.

| Saved case | Observation and adoption consequence |
|---|---|
| Generation wire collision | Two distinct process/window source tuples encode to identical wire objects. Decoding loses both fields: current identity transfer **FAIL**. |
| Decoded lease / selected owner | Current selected owner refuses before admission; fake held set remains empty. Fail-closed control **PASS**, not wire compatibility. |
| Original lease / selected owner | Actual returned admission contains its process identity; fake key38 is pressed, then verified released. Positive Fake X control **PASS**. |
| Timeout, wrong reply ID, malformed record snapshot | Each first call fails, then the same archived client sends request2/down/d. Sticky quarantine **FAIL** in all three intercepted-send cases. |
| Healthy reply control | Requests1/down/a and2/down/d complete against synthetic replies. Fixture control only. |

`test_archived_owner_boundary.py` selects exact archived `encode_lease`,
`decode_lease`, `validate_request`, client `call`/`_sync_records`, and their constants;
it does not execute historical module top-level or service code. The transport
is replaced at send/receive, so emitted requests are evidence of send admission,
not remote execution, physical key state or real RPC scheduling. The current
owner control uses the existing selected-backend Fake X fixture. Only the
process-identity path is exercised by that control; window transport loss is
shown in codec values. Concurrent native ownership is not introduced.

Final normal and optimized Python each ran **3 methods / 7 retained rows**,
zero failures/errors/skips. Forty-six current source pins per mode are recorded
with LF-normalized hashing. The [saved readback](verification/READBACK.json)
checks rows and pins separately and rejects six altered records per mode.
These characterization tests pass because they reproduce unsafe candidate
boundaries; the candidate has not passed the adoption requirements.

## Historical outcomes remain historical

All old raw, freezes, candidates, audits and STOP/FAIL reports in the published
PR diff are retained via the path map. In particular:

- Co-resident Executor hard-kill A01: [original FAIL_STUCK_KEY report](archive/c2e81a92d045aeb34e3cbae975f1736c484c57b243b33ad13a24c51df12a57e5.blob).
- [Original source-graph integration audit](archive/95386dde82ad5d8005e25483ca65ec25b437952e60c408590178a23b4a7aa9f1.blob): historical production wiring lacked outer owner recovery.
- [A14 owner-death report](archive/4c8d1d54b1cd1af986da928385013e77055a40bfe1b6be3ff59b8467404ba94b.blob): retain its recorded stuck-input result and scope.
- A35's retained freeze, runner, manifest and candidate identity/hashes match.
  This backcheck alone does not validate all of its live outcome gates.
- A36/A37 retain `STOP_CANDIDATE_FREEZE_ALLOCATION_ID_MISMATCH`; both candidates'
  self-reported pass values remain exploratory. Neither producer was replayed.

The readback uses archived bytes and AST, never imports or executes those
candidates. It does not independently re-audit all37 allocations or promote
historical Xvfb method results to physical-device, current MAP01, scorer/game,
independent task-success or matched-efficiency qualification.

## Provenance and first observations

Comparison main is `c7483785f85933cb5e187ab0c82715314c41d1d7`. Commands used the
dedicated Windows Python3.13 environment with Pillow12.2.0/numpy2.3.4/python-xlib0.33:

```text
python -I test_archived_owner_boundary.py --out verification/normal.json
python -I -O test_archived_owner_boundary.py --out verification/optimized.json
python -I read_saved_evidence.py
```

Run from this packet's directory (the actual retained runs used the equivalent
repository-relative script/output paths). Only local Python/Fake X was used.
Initial3-method normal rows/stdout/stderr are kept in `exploratory/first-normal.*`;
that initial script was enriched in place before an independent source copy was
retained, so those streams are exploratory and not independently source-pinned.
The first enriched normal/-O rows and exact scripts are separately preserved as
`exploratory/pre-readback-fix-*`. The initial readback assumed admissions appear
in owner history, but the owner returns an admission directly and records release
history. It rejected the positive control. Final collection additionally retains
the returned admission, and readback checks that actual payload. No production
or archived source was changed to satisfy the check. The initial readback
traceback was tool-visible only, not separately saved as stderr. Final raw is
new ordinary regression output; no historical outcome was rewritten.

## Concrete continuation

Use current observation-to-lease process/window bindings in a versioned service
handshake and wire contract; reject unsupported bindings rather than silently
downgrade. Quarantine the same client after any uncertain transport/protocol
result while preserving a distinct bounded cleanup path. Test delayed/misaligned
replies and that request2 cannot actuate, then compose the external owner with
current session/controller death handling and durable identity-bound recovery.
Keep owner death, supervisor death, shared-input attribution, blocking server
I/O, independent application effects and finite physical timing as separate
unproven gates. This packet does not install an external owner or claim those
problems solved. Current local ownership remains unchanged.

Publication check: the first staged-byte check found Git newline normalization
of the packet attribute file. Packet-scoped `-text` now preserves all retained
bytes; checksums were regenerated and staged/worktree bytes rechecked.
