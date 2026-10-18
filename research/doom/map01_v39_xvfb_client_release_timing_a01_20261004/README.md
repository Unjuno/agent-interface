# Xvfb client key-release timing A01

This Issue #59 construction measures how a private Xvfb client observes KeyPress and KeyRelease events relative to two XTEST senders: direct `python-xlib` calls and the exact current-main `InputOwner v10`. It follows the earlier A05 routing check with a new allocation and output path; A05 remains unchanged.

## Result

One frozen candidate invocation completed 30 paired cycles per route (60 presses and 60 releases total). The raw-only audit returned `PASS_XVFB_CLIENT_RELEASE_TIMING`; four auditor mutation tests also passed by rejecting a missing row, wrong target window, unreleased keymap state, and unverified owner cleanup. Guest and host SHA-256 for raw and runner logs match.

For direct XTEST, release-call duration was 20.625–206.751 µs (median 35.751 µs). The Python client receiver dispatched the matching KeyRelease before the direct call returned in 19/30 cycles; dispatch-minus-return ranged from -16.542 to +41.042 µs (median -8.667 µs).

For InputOwner v10, release-call duration was 51.125–170.001 µs (median 69.813 µs). The client receiver dispatched KeyRelease before `owner.call("up")` returned in 29/30 cycles; dispatch-minus-return ranged from -53.209 to +24.292 µs (median -19.959 µs). X server event timestamp deltas were 0 ms median and 1 ms maximum in both routes, reflecting the timestamp's coarse resolution.

These are descriptive measurements from one isolated Xvfb construction run. The receiver timestamp includes Python-thread scheduling; the direct and owner routes ran in fixed order within each cycle. The result indicates that, in this test client, release dispatch commonly preceded the caller's completion boundary, while a client dispatch after return also occurred. It does not measure game/app processing, physical key state, useful task feedback, bounded recovery, matched live-control benefit, or MAP01 progress.

## Reproduction and audit

The exact frozen candidate, runner, `InputOwner v10` source snapshot, raw result, and environment are retained here. Do not rerun this consumed A01 allocation. A future timing study needs a new allocation ID, prospective freeze, and explicit design delta.

From this directory, the raw-only audit is:

```sh
python3 SOURCE/audit.py results/A01/RAW.json /tmp/xvfb-release-audit.json
```

The four fail-closed audit mutation tests are:

```sh
python3 -B SOURCE/test_audit_mutations.py
```

The guest was stopped after readback. Its cgroup reported `cpu.max=max 100000` and `memory.max=max`; no effective CPU or memory cap is claimed.
