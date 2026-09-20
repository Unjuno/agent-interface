# Issue #3642 GTK effect binding — preregistration

Status: frozen before the one formal allocation. The two local OrbStack smoke
runs are explicitly excluded from formal evidence; their outputs remain outside
this directory under `/private/tmp/3642-smoke*-evidence`.

## H/T/D/C/U

- **H:** A valid gen-1 rising edge emits once; replacement advances to gen-2;
  delayed seq-2 gen-1 replacement is refused by the global sequence guard;
  seq-4 old-gen observation is refused; current gen-2 seq-5 rising edge emits
  once. Both emits map to one visible GTK counter increment and physical Space
  release. Counter remains 1 through prefixes 2–4 and reaches 2 at prefix 5.
- **T:** One Linux/arm64 OrbStack container, offline and read-only except for a
  fresh mounted evidence directory. Feed the five pinned events one at a time
  to the actual `Resident.step` and independent `PrefixOracle`; translate only
  an actual candidate `emit` to one XTest Space press/release. Save every prefix
  raw frame, title, action delta, states, keymap release, process lifecycle,
  logs, and hashes. Execute the independent raw-only auditor in a separate
  container invocation. No retries or replacement allocation.
- **D:** PASS only if candidate/oracle deltas and states agree at all five
  prefixes; exact deltas are `emit`, `invalidate`, `refuse_control`, `refuse`,
  `emit`; GUI count is 1,1,1,1,2; frames remain byte-identical through prefixes
  1–4 and change at prefix 5; two and only two Space actions each verify key-up;
  fixture and Xvfb exit 0 and are reaped; X11 socket is removed; all hashes and
  provenance checks pass with zero failures. Otherwise retain HOLD/FAIL/STOP.
- **C:** Base `3bbb1523aaae7959adf131be6447334647acfcb3`. Candidate guarded
  policy SHA256 `f2bc10dff9c2d5fdc0b066ad1ca38b690d68b1b21488bcfffe96373f695486df`;
  oracle `fc1c15bbaeec5b94d01ed6b3b0c749525a72b2424f6cdd2d1d9d6c0089e82221`;
  fixture `290bfb1f67093364bea322d012c900a29d80945a84c3dc2c46ad26fec5afaaf8`;
  runner `e18637a7e30d4684377411fd42d1484cfbad05090c9579f85511ab229dd02079`;
  auditor `eab5a025116904937a0e660014282a7e7222c0e6885bd783130d274f583f7f90`.
  Image `agent-interface-2972:20260920`, ID
  `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`,
  platform `linux/arm64`. Fixture exact source matches #3518 formal-03 SHA256
  `97467cc1685b7a7bfecda3a789f82b9e1174e75bbdf7db431d789d04159c2150`.
- **U:** One synthetic GTK/X11 policy-to-effect unit only. No production safety,
  real event source ordering, model/MCP use, general app correctness, latency,
  cost, or human-benefit claim.

## Frozen event sequence

1. `obs valid-gen1`: gen 1, target 1, seq 1, true
2. `replace replace-gen2`: gen 2, target 2, seq 3
3. `replace delayed-replace-gen1`: gen 1, target 1, seq 2
4. `obs stale-gen1`: gen 1, target 1, seq 4, true
5. `obs valid-gen2`: gen 2, target 2, seq 5, true

## Formal allocation and invocation

Allocation ID: `issue3642-gtk-effect-01`.

Evidence output is a newly created empty directory at
`/private/tmp/3642-formal-evidence`; auditor output is a newly created empty
directory at `/private/tmp/3642-formal-audit`.

Runner (one invocation only):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  -v /private/tmp/3642-work:/src:ro \
  -v /private/tmp/3642-work/research/analysis/resident_gtk_effect_binding_3642_v1/runner.py:/runner.py:ro \
  -v /private/tmp/3642-formal-evidence:/evidence:rw \
  -e ALLOCATION_ID=issue3642-gtk-effect-01 \
  -e OBSTAC_IMAGE_ID=sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  -e OBSTAC_PLATFORM=linux/arm64 \
  agent-interface-2972:20260920 /runner.py
```

Independent raw-only audit (one invocation after runner completion):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  -v /private/tmp/3642-formal-evidence:/evidence:ro \
  -v /private/tmp/3642-work/research/analysis/resident_gtk_effect_binding_3642_v1/audit.py:/audit.py:ro \
  -v /private/tmp/3642-formal-audit:/audit-out:rw \
  agent-interface-2972:20260920 /audit.py /evidence /audit-out
```
