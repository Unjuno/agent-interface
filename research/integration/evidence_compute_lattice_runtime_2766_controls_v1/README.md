# #2766 mutation-control targeting successor

## H / T / D / C / U

**H.** The two preregistered #2766 corruptions that were not rejected can be
re-targeted, without changing the retained formal rows, so the frozen raw
auditor detects the intended selector and post-cancellation violations. A
separate probe replays the original `wrong_g` mutation to check whether each
decision input is bound to its raw calibration median.

**T.** Restore the 110-member evidence capsule from the seven verified chunks,
run the frozen raw auditor on the retained 18-case results, then mutate only
fresh copies of two selected `result.json` files. `wrong_g` sets `g_ns` to zero
on `active_run_low_p`, making the exact rational selector choose `WAIT` while
the copied disposition remains `RUN`. `publish_after_cancel` marks the
`active_compute_invalidation` record reusable even though its later decision is
`CANCEL_STALE`. The independent frozen auditor must reject both copies.

The original `wrong_g` mutation is also replayed exactly: add 999,999,999 ns to
the decision row while leaving calibration samples unchanged. It preserves the
mathematically correct `RUN` disposition. The frozen auditor accepts this
record with `errors=[]`, showing that it does not bind the decision input to
`calibration.wait_measure.median_ns`. Thus `g_ns=0` tests selector/disposition
consistency only; calibration-provenance auditing remains incomplete.

**D.** Capsule restoration succeeds; the unchanged formal raw audit reports
18 cases / 23 decisions / no errors; both selector/post-cancellation mutations
are rejected; and the original six construction tests pass. The original
+999,999,999 ns `wrong_g` calibration-provenance mutation is accepted, so this
successor remains `HOLD_CALIBRATION_SOURCE_BINDING_GAP`, not a full repair of
#2766's control gate. The original allocation remains
`HOLD_RUNTIME_INPUTS_INCOMPLETE`.

**C.** The test mutates temporary copies and uses the frozen auditor. Docker
Desktop Python 3.13.15 was pinned by local image ID and run with network off,
read-only root/source, one CPU, 512 MiB memory, 64 PIDs and tmpfs-only scratch.
The host Windows Python 3.12.10 run of the original six tests had one
timer-resolution failure (`g_ns == 0`); the same suite passed in the Linux
container. Preserve both environment outcomes.

**U.** This validates only two corruption-control targets and evidence
reconstruction. It does not rerun any formal allocation, validate scheduler
quality, or establish live GUI, model, task-effect, latency, product, or general
runtime claims.

## Reproduction

From this directory, using the pinned local image
`sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b`
(`linux/amd64`):

```sh
python restore.py /tmp/ec2766-evidence
python audit.py /tmp/ec2766-evidence/formal
EC2766_FORMAL_ROOT=/tmp/ec2766-evidence/formal python -m unittest -v test_control_targets.py
EC2766_FORMAL_ROOT=/tmp/ec2766-evidence/formal python -m unittest -v test_calibration_binding_probe.py
python frozen_source/test_contract.py
```

The full invocation used one disposable container with `--network none`,
`--read-only`, `--cpus=1`, `--memory=512m`, `--pids-limit=64`, and a bounded
`/tmp` tmpfs. The terminal output was: restore `PASS` (110 members), frozen
raw audit `PASS_RAW_AUDIT` (18 cases, 23 decisions, `errors=[]`), selector and
post-cancellation tests 2/2 PASS, original wrong-g acceptance reproduced, and
original construction tests 6/6 PASS. No formal rows were executed again.

## Evidence capsule boundary repair

At main `2207354ba293d87b4723c6e62a4d12a0fc2ec16f`, the parent
`CAPSULE.json` names `EVIDENCE.part-05` as 7,000 bytes and `part-06` as 1,292
bytes, but the parent tree contains one 8,292-byte `EVIDENCE.part-05` and no
`part-06`. The bytes are recoverable: split that retained part after byte
7,000. The two resulting SHA-256 values match the capsule's frozen values
exactly, as do parts 00–04. This package stores the reconstructed seven chunks
additively; it does not alter the parent evidence.

The parent result remains 10/12 corruption controls rejected. The original
`wrong_g` increased `g_ns`, which preserves `RUN`; its corrected negative
control decreases `g_ns` to zero. The original `publish_after_cancel` targeted
`active_run_low_p`, which had no later cancellation; the corrected control
targets `active_compute_invalidation`. Both corrected violations are rejected
by the unchanged raw auditor. However, the exact original `wrong_g` mutation
remains accepted; a later successor must validate calibration samples and
measurements against every decision input.

## Append-only calibration-source probe

After the selector-target repair, the exact original `wrong_g` mutation was
replayed on a fresh copy of `active_run_low_p`: the decision row's `g_ns` was
increased by 999,999,999 ns while the calibration object and sample list were
left untouched. The copied disposition remained `RUN`, and the frozen raw
auditor returned `errors=[]`. An independent comparison found decision
`g_ns=1,004,100,558` while
`calibration.wait_measure.median_ns=4,100,559`.

This is **not** a second runtime failure or a formal rerun. It demonstrates
`HOLD_CALIBRATION_SOURCE_BINDING_GAP`: the frozen auditor checks the decision
math but does not bind row-level `g_ns` to the retained calibration summary.
The calibration record does not retain full clock event pairs, so this probe
does not authenticate the calibration samples themselves. The first Docker
attempt stopped at a test-harness path lookup because
`EC2766_FORMAL_ROOT` was not read; after correcting that lookup, the probe ran
on the immutable evidence copy. Both outcomes are retained in
`CALIBRATION_BINDING_PROBE.json` and `FREEZE_CALIBRATION_PROBE.json`.
