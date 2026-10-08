# #5081 v6 current-source Docker construction — 2026-10-01

## H / T / D / C / U

**H.** The frozen v6 fail-closed contract suite (exact Docker argv and online
query/update evidence checks) executes in its pinned Linux/amd64 image when the
experiment directory is mounted read-only with networking disabled.

**T.** One zero-fit construction invocation on the existing branch
research/needle-role-skill-joint-retention-v6-20260928, exact head
d32a771ac9aa090fc39ff596c55e75484f437dc5, under Windows Docker Desktop
context desktop-linux. Main at invocation was
55c467786b3b98e5f8d1746f9c2970b7ada8b47c; the v6 branch's prior merge base
was 3a96b8ea80201edd8860318b14148facecd009b8. GitHub compare from that merge
base through main-at-run listed 429 commits/300 files and zero changes in
this v6 experiment path. This is a source-isolation check, not a claim that
the branch is rebased/current-main frozen.

The candidate image was already present locally and inspected by exact image
ID: sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e,
linux/amd64, repo digest
needle-pilot05@sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e.
No pull/build occurred. Immediately before launch, docker ps was empty and C:
had approximately 13 GB free. The independent runner used one CPU, 2 GiB
memory, 64 PIDs, a 256 MiB /tmp, read-only source/root filesystem, and
--network=none.

Runner argv (the unabridged realized token array is in docker_stage0.stdout.txt):

    docker run --rm --pull=never --platform=linux/amd64 --network=none --read-only
      --cpus=1 --memory=2g --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=256m
      --entrypoint=python --mount type=bind,source=<v6 experiment dir>,target=/src,readonly
      --workdir=/src sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e
      -B -m unittest -v test_protocol.py

**D.** Runner exited 0: 27/27 passed in 2.308 seconds. The separate
network-disabled raw-only audit container's corrected v2 auditor passed 25
checks, found no source-hash mismatches, and returned
PASS_DOCKER_CONSTRUCTION_FIXTURES_ONLY. Raw stdout SHA-256:
299b414adbca9e22ccc370aa4ef288711cdfcc25e4cc0f7aa8e9cfc9e088cf6f.
Decision is strictly PASS_DOCKER_CONSTRUCTION_FIXTURES_ONLY.

Audit chronology is retained, not overwritten:

1. A host wrapper path error stopped before Docker; zero container calls.
2. Independent auditor v1 ran once in a container and returned
   HOLD_AUDIT_INTEGRITY for two auditor/receipt defects: it checked network=none
   instead of the actual --network=none token, and the manually transcribed
   raw digest differed by one character. The runner output itself remained
   unchanged.
3. A separate corrected receipt and v2 auditor were added. The v2 auditor ran
   once in its own container and returned PASS. Both audit outputs and both
   receipt versions are retained.

**C.** This was one local Windows Docker Desktop run, separate from the remote
Mac OrbStack allocation noted in #5085. No other container was running in this
local Docker context. No network, GPU, GUI, input, user data, provider, model
forward, optimizer step, construction seed, or formal seed was used. PyTorch
emitted a non-fatal warning that NumPy is absent in the pinned image; the
affected test and full suite passed.

**U / limits.** This is fixture/construction evidence only. It does not measure
actual OS-thread/process overlap, online adaptation, model quality, A/B
retention, update latency, natural-language role recognition, user-facing skill
reliability, or production behavior. The historical v5 HOLD and quality miss
remain unchanged. The old branch base and formal resource/fresh-freeze gates
remain; no formal invocation is authorized by this result.

## Artifact ledger

- Candidate suite stdout and realized argv: docker_stage0.stdout.txt
- Runner receipt: construction_receipt_v2.json (v1 retained as the initial
  transcription)
- Independent audit source: audit_construction_v2.py (does not import
  candidate protocol.py or audit.py)
- Independent audit output: audit_attempt_02.stdout.txt
- Initial audit HOLD: audit_attempt_01.stdout.txt
- Host-side prelaunch path STOP: audit_launcher_preflight_01.txt

The formal allocation remains unspent. Any formal run requires a new exact
current-main freeze and the issue's separate resource/owner authorization.
