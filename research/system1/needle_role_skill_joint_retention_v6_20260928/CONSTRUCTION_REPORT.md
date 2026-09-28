# #5081 v6 — host zero-fit construction report

**Disposition:** `PASS_HOST_CONTRACT_FIXTURES_ONLY`; not a Docker construction
PASS, formal result, scientific result, or authorization to use the shared
container.

## H/T/D/C/U

- **H:** exact realized Docker argv and live query/update event contracts can
  be validated independently. Feedback must arrive after the first inference
  call starts and its optimizer interval must overlap an individual active
  inference call, not merely a broad query window.
- **T:** allocation `needle-role-skill-joint-retention-20260928-v6`, branch
  `research/needle-role-skill-joint-retention-v6-20260928`; additive source
  path is this directory. Formal seeds remain reserved by #5081 and were not
  read or consumed. Formal Docker execution remains lease-gated by #5085.
- **D:** 16/16 host tests pass. Coverage includes exact argv token equality and
  mutation rejection; inference-call overlap, fresh arrival, and distinct
  worker identity; pinned predecessor Git blob identities; event-generation
  ordering; independently rebuilt auditor argv/event contracts; one-run/no-retry
  launcher structure; and rejection of a missing owner lease. Syntax checks pass for `runner.py`, `audit.py`, `protocol.py`,
  `formal.py`, and `test_protocol.py`; `git diff --check` passes.
- **C:** checks use synthetic timestamp fixtures and temporary directories.
  No construction seed, optimizer, model forward, Docker command, or image was
  run. The independent auditor imports its frozen predecessor oracle but has
  not yet audited a generated v6 raw record.
- **U:** no model-query/optimizer overlap, adaptation outcome, A/B retention,
  latency, or scientific threshold has been measured. A separate one-shot host
  thread-boundary probe now verifies only placeholder-call/empty-critical-section
  event capture; it is not a model experiment. The v6 result remains a host
  contract pass only, not a container or LoRA experiment pass. v5 evidence is
  unchanged.

## Resource and allocation boundary

The formal issue #5081 remains queued. #5085 still requires the resource owner
to record an exact allocation lease and lane release; absence of a visible
Windows container is not authorization. This report makes no Docker invocation
and consumes none of the formal seeds.

## Historical construction evidence

Earlier revisions passed 8/8 and then 15/15 host tests. The current 16/16 suite
adds an independent auditor implementation check: it rebuilds exact argv and
online-window decisions without importing candidate `protocol.py`. The earlier
counts are retained by Git history and are not represented as the current count.

## Current-main synchronization checkpoint

Latest observed main `d07b5b593d25c5d5833381f029e385ab93838ea1` was merged without
conflict at `06cce787db`. Its changes were confined to research/runtime README,
interface, and Inkscape evidence; the v6 experiment path remains additive and
isolated.
This is branch freshness only, not a formal freeze or resource grant; repeat the
current-main and lease checks before any seed-consuming work.

## Pinned-image construction and audit correction — 2026-09-28

After main advanced to `d8ca8bfed9cd8d84201c91645e4ed25364181d3f`, it was merged
without conflict at `40a552b60891e234b7cb244bc8759b9367a1d4bb`. Current branch
head is pushed to GitHub. The experiment image is present locally at the frozen
digest and its config entrypoint is `python`.

Independent code review found two construction blockers before any fitting:

1. The raw auditor accepted a record if any one feedback update overlapped an
   inference call, although every registered feedback/query pair must satisfy
   the overlap condition. It now rejects a mixed record with one valid and one
   non-overlapping event; a dedicated negative test covers this.
2. The auditor and formal launcher assumed the repository parent tree via
   `parents[3]`. The frozen Docker command mounts only this experiment directory
   as `/src`, so those parent indexes do not exist. The auditor now anchors its
   local root to its mounted experiment directory; the launcher invokes Git
   from that directory on the host, where Git discovers the enclosing checkout.
   A regression test rejects the old depth assumption.

Pinned local Docker construction command (only the experiment directory is
mounted read-only; no output mount, model run, construction seed or formal seed):

```text
docker run --rm --pull=never --platform=linux/amd64 --network=none --read-only
  --cpus=1 --memory=2g --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=256m
  --entrypoint=python --mount type=bind,source=<v6 experiment dir>,target=/src,readonly
  --workdir=/src <frozen image digest> -B -m unittest -v test_protocol.py
```

The first Docker construction attempt ran 16 tests and failed 3 with
`IndexError` from the invalid parent assumption; all failure output is retained
in this report's Git history/Issue #5081 comment, and the ephemeral container
was automatically removed. After the source-path fix and test addition, the
same isolated pinned-image command exited 0 with **17/17 passing**. Windows-host
suite also passes 17/17; `formal.py --preflight` remains `PREFLIGHT_ONLY` with
zero formal Docker calls. Docker used no network and was not given any seed
environment variables. This is `PASS_PINNED_IMAGE_CONSTRUCTION_FIXTURES_ONLY`,
not an optimizer, adaptation, latency or scientific result. Formal v6 remains
`STOP_RESOURCE_GATE` pending exact #5085 owner lease; prior v5 evidence is
unchanged.

PR #5226 was opened as Draft against main observed at
`b556c109828e89b3a8e78cb618530a044c97d7d8`. That latest main commit (#5224,
retained-host-time accounting) was immediately merged without conflict at
`b324284ee1616280e4dde9f0d2b1c126735ff331`; this newer synchronization is
recorded in the checkpoint manifest and report. The branch is pushed/rechecked
before review.

## Supplemental independent-auditor mutation matrix — 2026-09-29

After the pinned Docker result, #5085's latest comment was discovered; it
explicitly prohibits any further Docker CLI call until a fresh exact lease and
owner/resource release. Therefore this supplemental run is host-only and does
not claim Docker reproduction. Windows CPython 3.11.9 reran the complete zero-fit
suite: **18/18 passed**. Ten deterministic malformed event mutations were
rejected: boolean arrival clock, post-query arrival, consumption-before-arrival,
reversed update interval, consumption outside update, same inference/trainer
identity, call interval outside query, duplicate feedback ID, duplicate query
ID, and a mixed record where a non-overlapping event follows a valid overlap.
Only synthetic timestamps/IDs were used; no seed, model, optimizer, or raw formal
record was read. This host-only count supersedes the earlier 17/17 host count;
the pinned Docker 17/17 result applies to the prior source revision and was not
repeated because of the explicit coordinator hold. The ordering/process issue
and prior Docker construction are disclosed on #5085; this new run used no
Docker command.
