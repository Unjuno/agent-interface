# #5156 completion-record auditor counterexample — T0

Status: **STOP_ALLOCATION_SCOPE_AND_SHARED_RESOURCE_CONFLICT**; candidate=0,
independent auditor=0. After the 07:30 gate, I found the newer #5156 comment
[#5926720911](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5926720911),
which had already rejected this completion-auditor T0 as out of scope for
#5156's formal X11 hypothesis and required a distinct issue/allocation. I failed
to refresh #5156's latest comments at the start gate; that process miss is
preserved explicitly. Separately, the local Engine service was stopped and the
read-only `docker version` probe remained pending, so inventory/image gates were
also unavailable. See `results/start_gate/STOP.json`. No service restart,
container operation, candidate, auditor, or retry was performed.

## H / T / D / C / U

**H.** In the frozen #5630 T3 auditor, filtering `runner_complete` records with
`exit_code == 0` before checking the count may accept JSON Boolean `false`
(`False == 0` in Python), float `0.0`, and a successful record accompanied by a
second failing completion record.

**T.** In one bounded, network-disabled container, run the frozen CLI against
eight raw JSONL cases, in order: pristine integer-zero control; Boolean false;
float zero; null; string zero; missing exit code; duplicate integer-zero
completion; integer-zero plus integer-one completion. If and only if that one
candidate container exits 0, run the independent receipt/raw audit once in a
separate bounded container. No retry.

**D.** Expected target CLI exits are `[0,0,0,1,1,1,1,0]`. The independent
auditor must verify frozen source hashes, exact case IDs and completion rows,
all raw/audit/log hashes, unchanged non-completion evidence, target status, and
the preregistered success predicate. A mismatch is retained without tuning;
resource/provenance/source failures are STOP, not a scientific FAIL.

**C.** Pinned image requested in the allocation: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Linux/amd64, network disabled, read-only root and source, bounded CPU/memory/PIDs, no capabilities, fresh writable result mount. Synthetic JSONL only.

**U.** This checks one auditor's synthetic completion-record boundary. It is not
formal X11, owner key-up timing, keymap, GUI/input, game, model, GPU, task effect,
MAP01 occupancy, safety, efficacy, or Issue #59 completion evidence.

## Frozen source

Source PR #5630 head: `288d0498d11cf16657e523a04616bf4f49cd94f4`.

| File | Git blob | SHA-256 |
|---|---|---|
| `target/audit_formal_x11.py` | `da805fb83f70a57ad68a0768186e214524689d40` | `f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0` |
| `target/EXPECTED.json` | `3d33bda096c4c8789e183e3f864ee7626e643a7e` | `7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076` |
| `target/test_audit_formal_x11.py` | `d1eb9a854cc810fa77ca173d7e2de287ee1bd64a` | `1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5` |

## Construction verification

Host CPython 3.12: `python -m unittest discover -s tests -v` — **8/8 passed**.
`python -m py_compile matrix.py independent_audit.py run_candidate.py
target/audit_formal_x11.py target/test_audit_formal_x11.py` — **passed**.
These tests validate case generation and the independent evidence checker only;
they do not invoke the frozen auditor CLI on the scientific matrix.

## Start gate and commands

Before the candidate gate, current main/source, Issue #5085 queue, PR #5630
source head, and unique empty output path were checked, but the latest #5156
comments were not re-read. The overlooked issue-scope STOP comment predates the
window. The Docker Engine, container inventory, and image-ID gates also
failed/are unknown. No candidate command was issued. Do not reuse this window or
allocation ID. A separately scoped successor issue and fresh allocation are
required before any candidate run.

If a fresh, separately scoped successor is later authorized, its candidate
container may be named
`unjuno-5156-completion-t0-candidate-20261001-01`; use `--network=none`,
`--pull=never`, `--read-only`, `--cpus=0.50`, `--memory=512m`,
`--pids-limit=64`, `--cap-drop=ALL`, and
`--security-opt=no-new-privileges`. Mount this package read-only at `/work`,
the unique empty result folder read-write at `/out`, then run:

```text
python3 -B /work/run_candidate.py --target /work/target --out /out
```

Only after its actual container exit is 0, run the independent auditor once in a
separate container, with the package read-only and candidate output mounted
read-only:

```text
python3 -B /work/independent_audit.py /results/candidate_manifest.json /work/target
```

Retain exact container IDs, image ID/platform, commands, exits, stdout/stderr,
output hashes, and the independent audit. Do not treat host construction tests
or the source-level prediction as the experiment result.

## Separate scope after the superseding STOP

The independent follow-on is now tracked by [Issue #5895](https://github.com/Unjuno/agent-interface/issues/5895).
This directory preserves preparation from the superseded #5156 preregistration;
it is not a runnable freeze for #5895. In particular, the embedded candidate
allocation ID belongs to the invalidated #5156 schedule. Any future authorized
run must receive a new explicit allocation, update/freeze the candidate and
auditor identities for that allocation, refresh main/PR #5630 source, and pass
a new Docker/queue/output gate. Never reuse #5926417922 or its 07:30–07:35 UTC
window.
