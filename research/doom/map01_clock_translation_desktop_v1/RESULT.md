# Docker Desktop / WSL2 lease-clock translation — formal01

Issue [#3886](https://github.com/Unjuno/agent-interface/issues/3886), successor
to the OrbStack-specific infrastructure gate in #3880. This run is scoped only
to this host's Docker Desktop Linux/amd64 engine and Ubuntu WSL2. It does not
consume #3880's OrbStack seed, modify any predecessor, run DOOM, call a model,
or send OS input.

## Decision

**`PASS_DOCKERDESKTOP_WSL_LEASE_TRANSLATION_SCOPED`** after the corrected
independent audit. One frozen formal invocation completed all 120 timestamp
exchanges and all four lease controls; reruns: 0. The first independent audit
was preserved as `results/formal01/audit.json` and reported a STOP because of
an auditor schema mismatch (see [audit correction](AUDIT_CORRECTION.md)). The
corrected, separate auditor returned zero errors at
`results/formal01/audit-corrected.json`. Raw data and the initial STOP remain
unchanged.

## Measurement

The pinned environment was Docker Desktop Server 28.5.1, Linux/amd64, context
`default` as invoked from Ubuntu WSL2. The offline, read-only container ran
Python 3.12.14 on the WSL2 kernel; host Python was 3.12.3. Image was launched
by immutable local ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
with `--pull=never --network none --read-only`, bounded tmpfs, and read-only
mounts for the production modules. The container ran as the WSL2 user's UID/GID.

All 120 exchanges followed the 5-second target cadence. Observed gap range was
4.989782213–5.007696649 seconds. The four-timestamp intervals for
container-minus-host clock offset all had widths no greater than 1,072,371 ns
(predeclared ceiling: 250,000,000 ns). Their common intersection was
`[-93,033, 196,442] ns`; the frozen translation used the lower endpoint
`-93,033 ns`. This bounds only the observed exchange period and does not prove
future drift, suspend/resume safety, or equivalence to OrbStack.

The production `research/live_control/unix_json_deadline.py` client exchanged
newline-delimited JSON over AF_UNIX with the container service, which loaded
the exact production `research/live_control/lease.py` class. Lease controls:

| Control | Result |
|---|---|
| Conservatively translated +25s host deadline | `accepted`; container remaining 24.999109003s |
| Expired host deadline | `expired` |
| Conservatively translated +31s host deadline | `rejected` by 30s admission horizon |
| 500ms remaining host authorization, with 750ms server delay | `expired` |

For the accepted lease, independent reconstruction found the translated
container remaining duration did not exceed the minimum host-authorized
remaining duration at the same container timestamp. Container shut down via
the JSON protocol and exited 0; no container remained running.

## Construction record

All construction iterations were separate from the formal invocation. The
first Windows-backed `/mnt/c` socket bind failed with `OSError(95, Operation
not supported)`. Moving the shared socket directory to WSL2 `/tmp` made it
visible but root ownership caused `PermissionError(13, Permission denied)` on
the host connect. A later construction used a dedicated WSL2 Linux temporary
socket bind mount and matching UID/GID; production JSON exchange and production
Lease loading passed. These failures and successful probes are preserved in
`results/construction01/` through `results/construction09/`; they do not add
formal samples.

## Provenance and reproduction

Source main: `f7d5cc8535995db0c36dd85d4b71877503bd0db8`. Production source and
frozen allocation code SHA-256 values are in `SOURCE_MANIFEST.json`. Raw host,
container, sample, and control journals plus runner output and both auditor
outputs are in `results/formal01/`.

From WSL2, with the same Docker Desktop engine and pinned image already present:

```bash
python3 research/doom/map01_clock_translation_desktop_v1/formal_runner.py \
  --repo "$PWD" \
  --source "$PWD/research/doom/map01_clock_translation_desktop_v1" \
  --out "$PWD/work/issue3886-formal01"
```

The preregistered formal source is intentionally single-use: this command must
not be rerun to replace or improve the retained allocation. To re-audit the
existing retained evidence, use `audit_corrected.py` against the corresponding
evidence and repository paths. This scoped pass is not evidence for OrbStack,
MAP01, gameplay, or general cross-platform clock safety. If the interval becomes
unstable or the host/container relationship changes, prefer receiver-issued
runtime-domain leases over extrapolating this measurement.
