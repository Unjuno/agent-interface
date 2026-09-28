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

On 2026-09-29, main advanced to `1a8f774845f058d199dc976d2488c6b1d1b90c46`;
it was merged without conflict at `b3b35ee71f4c7f3a77379fe8c381a949ab97ec25`.
Included changes #5225's unrelated retained temporal-receipt audit and #5234's
Mindustry acquisition workflow; neither modifies the v6 experiment path. The
latest source suite was rerun host-only after the merge because the #5085
Docker-command hold remains in force.

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

## Independent fail-closed review and source correction — 2026-09-29

A read-only subagent review of the pushed v6 source found three formal-integrity
gaps and one event-time discrepancy before any formal run:

1. `formal.py` accepted an arbitrary `owner_comment_url`/non-placeholder
   `lease_id` without retrieving or matching the actual GitHub comment; it also
   lacked explicit lease start/end boundaries. It now fetches the referenced
   public GitHub API comment before any Docker CLI call, requires the issue
   owner `Unjuno`, parses one machine-readable `needle-docker-owner-lease-v1`
   payload, and exact-compares its allocation, issue, main SHA, branch, Docker
   context, lease ID, start/end, and expiry to the local lease. The lease window
   must be active. Its verified comment body and author/URL are retained in the
   formal receipt.
2. `audit_document` previously skipped provenance checks when passed
   `receipt=None`. It now emits `formal_receipt_missing` and decision
   `HOLD_AUDIT_INTEGRITY`; when present, it independently parses and binds the
   owner-comment payload and verifies receipt start/finish against the leased
   window.
3. `consumed_ns` was timestamped at update setup, before the feedback row was
   first passed to the model forward. Runner now records consumption directly
   before the first forward using that row and fails closed if it was never
   consumed. Both candidate protocol and independent audit treat update
   intervals as half-open and reject `consumed_ns == update_end_ns`.
4. The new lease fixture exposed a type bug: lease issue number 5085 is an
   integer, but was accidentally included in the required-string field list.
   Validation now checks its exact integer type/value separately.

Windows CPython 3.11.9 now passes **22/22** zero-fit host tests, including forged
lease payload/author rejection, receipt-absence HOLD, query/update half-open
boundary, actual feedback-consumption instrumentation, and the prior eleven
online-event mutations. `py_compile` and `git diff --check` pass; all eight
source hashes are frozen in `CONSTRUCTION_FREEZE.json`. No Docker command was
run for these newest changes because #5085 comment #5864690783 forbids further
Docker CLI activity until an exact lease/release is recorded. The prior 17/17
pinned-image suite applies only to the preceding source and does not verify
these new edits. Current result is host-contract evidence only, not a model,
optimizer, quality, latency, or scientific PASS. A future Docker construction
must wait until an explicit coordination update supersedes the hold, and formal
execution additionally requires the verifiable owner lease described above.

## Independent review follow-up — GitHub-backed audit provenance — 2026-09-29

A further read-only review found that the previous audit only checked provenance
asserted inside the receipt. It now independently retrieves the referenced
GitHub API issue-comment record and checks the canonical #5085 comment URL,
issue URL, `Unjuno` author, and exact body against the retained lease comment.
The owner payload parser rejects duplicate JSON keys. The launcher rechecks the
exclusive window immediately before both `docker context show` and the single
`docker run`, so checks that cross expiry fail closed before the next Docker
call. The launcher's lease-file and owner-payload JSON parsers also reject
duplicate keys. Regression tests cover forged URL/record, duplicate-key
payload, and lease-boundary expiry.

Windows CPython 3.11.9: **24/24** zero-fit host tests pass; `py_compile` and
`git diff --check` pass. Updated hashes are in `CONSTRUCTION_FREEZE.json`.
This newer source remains host-tested only: the #5085 comment thread still
contains the explicit no-Docker-CLI hold (#5864690783) and no later exact
allocation lease/release. The historical Docker construction is not evidence
for this source. No model, optimizer, formal seeds, raw result, or scientific
quality/latency claim is included.

## Current-main sync — 2026-09-29

GitHub reports main at `0a213fdb794d7c2498868fb109b1794465b70489`. Compare from
the prior v6 base found eight commits and no changes in this v6 path; after
committing the current host-only hardening, the branch merged that main tip
without conflict at `1b4af173771c2de8831ff23bbe2771814be8d478`. The imported
changes are unrelated runtime/X11 and evidence paths (#5237/#5239). Re-run the
host suite after synchronization; this does not authorize a Docker call or
formal run.

## Adjacent Needle/System-1 issue triage — 2026-09-29

Current open-issue/comment recheck found concurrent-LoRA pressure and CPU2
scheduling work that must remain separate from #5081's role-retention question:

- #4653's corrected concurrent COW-LoRA run passed its raw auditor but ended
  `HOLD_NO_CONCURRENCY_PRESSURE`: only 5/120 query intervals overlapped training
  per seed (gate >=8); seed 99119 also missed two absolute 60-Hz deadlines.
- #4658 increased support workload fourfold. It reached 8/120, 9/120, and 8/120
  COW overlaps and passed p95 latency, but ended `HOLD_LATENCY_BUDGET` because
  seed 99771 missed three absolute scheduled deadlines. This argues against
  treating workload inflation or p95 alone as sufficient.
- #4917's query-boundary-pulsed CPU2 schedule is the distinct next scheduling
  hypothesis, but its latest comments preserve a supplemental Stage-0/adoption
  boundary and ask for explicit ownership before further formal work. Do not
  reuse its allocation/seeds or merge its evidence into #5081.

These results motivate keeping #5081's fresh online role-skill retention test
and #4917's scheduling intervention as separate hypotheses. They do not remove
the current #5085 resource gate, and no additional container or model work was
performed for this issue triage.

## Review follow-up — comment-ID binding and lease-bounded container cleanup — 2026-09-29

An additional read-only review found two remaining authorization/resource
edges. First, the launcher and auditor now require the GitHub API record's
numeric comment `id` to equal the ID encoded in the canonical #5085 comment
URL; the formal receipt retains that ID. Second, the launcher pins the checked
Docker context on both run and cleanup calls, records the container ID with
`--cidfile`, and sets the attached run timeout to end before the earlier of
lease expiry/slot end, reserving 20 seconds for a single `docker rm --force`
cleanup. If the run times out, its receipt records exit 124 and cleanup evidence;
the audit cannot accept it as a formal result. If insufficient lease time
remains for cleanup, it stops before launching.

Host tests additionally exercise API comment-ID mismatch, local Docker-run
timeout and in-window forced cleanup without invoking Docker. Current suite is
**27/27** on Windows CPython 3.11.9; compile, preflight-only, `git diff
--check`, and all manifest SHA-256 entries pass. This is still not a Docker
runtime verification: #5085's no-CLI hold remains unsuperseded, and no formal
seed/model/optimizer or scientific result was used.

## Independent stop-path review follow-up — in-container watchdog — 2026-09-29

Independent review then identified that a host `docker rm --force` fallback
could itself hang or fail, leaving the container runner alive past its owner
window. The launcher now freezes an absolute UTC stop instant 30 seconds before
the earlier slot-end/lease-expiry and passes the remaining duration to a new
PID-1 watchdog. Inside the pinned container the watchdog supervises the runner
as a child using monotonic elapsed time, sends terminate and then kill on
deadline, and writes a watchdog receipt. The host-side attached Docker timeout
still leaves 20 seconds for bounded best-effort removal; the watchdog is the
independent stop mechanism if the CLI/daemon cleanup path is unresponsive.
Independent audit now requires the container ID file to match the receipt,
checks the watchdog receipt hash/schema/outcome and binds its stop instant and
runtime to the recorded owner lease. Timeout remains a STOP and cannot become a
scientific PASS.

The complete Windows CPython 3.11.9 host suite passes **27/27**; syntax checks
pass, `formal.py --preflight` reports `PREFLIGHT_ONLY` with zero Docker calls,
and `git diff --check` passes. The freeze manifest includes current hashes for
the launcher, argv protocol, independent auditor, watchdog, and tests. No Docker
command was run: #5085's no-CLI hold still applies. Consequently the new watchdog
has host unit coverage only, not in-container runtime verification; the earlier
17/17 image run predates it and does not verify this source revision. No formal
seed, model, optimizer, or scientific outcome is claimed.
