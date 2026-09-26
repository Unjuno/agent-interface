# Upper-caller IPC completion evidence — Issue #4081

**HOLD_FORMAL_INCOMPLETE. Research evidence only; no runtime promotion.**

This is retrospective publication of the conversation-local
`host_ipc_outer_call_v1` allocation, not GitHub preregistration or a new formal
run. Preserve closed #2818, #3987 / PR #4022 and parallel #3924/#3926. The old
822 files, including their historically true write-unavailable statements,
construction failures and incomplete formal record, are retained byte-for-byte.
The dated delivery record here does not rewrite those files.

## Question and observed boundary

Does actual upper `docker_model_call_backend_v1.call ->
validate_model_response -> integrated_efficiency_model_v1.parse -> plain
validator` catch the completion failures observed at the IPC client boundary?

The upper functions, client and broker run from exact source. Only Docker
command construction is explicitly replaced by the SAME local subprocess
transport for all arms. Real client, broker and harmless fake-executable
processes are used; schema/grounding validation is not mocked. The transport
waits for both process exits, so this is NOT a Docker timing or partial-file
publication replication. There is no real model, provider, GUI or OS input.

| Completed first-repetition case | CURRENT | JOIN_ONLY | JOIN_FIXED |
|---|---|---|---|
| Normal | returned | refused broker exit1 | returned |
| Actual child exit23 | returned | refused | refused |
| Completed plus failed event stream | returned | refused | refused |
| String-valued usage integer field | returned | refused | refused |
| Invalid output schema instance | refused | refused | refused |
| Field/submit points collide | refused | refused | partial: excluded |

These are unbalanced prefix examples, not rates, a full paired comparison, or
full candidate acceptance. The exact current broker contains
`return broker.get("returncode") or 1`: child0 becomes broker1. A strict consumer
alone therefore refuses the normal control; the isolated JOIN_FIXED arm also
corrects that producer exit mapping. No shared source was modified.

The completion envelope is a NEW cooperative transport contract. The upstream
broker does not emit it. Do not deploy the consumer patch without an explicit,
reviewed producer exit/envelope implementation. Hash agreement is neither
producer authentication nor atomic multi-file publication.

## H / T / D / C / U

**H.** Response, event-count, schema and coordinate validity do not establish
child/broker success. Completion evidence must be joined at the actual upper
result boundary; otherwise invalid completion can become a normalized result.

**T.** Original plan: eight conditions, three arms, two repetitions, 48 cases in
eight predetermined six-case batches. Arms CURRENT, JOIN_ONLY and JOIN_FIXED.
The eight conditions also include missing usage and missing completion envelope;
those later cases were not reached. Construction is excluded. Twenty-four
files were locally frozen before formal execution; no post-freeze source/gate
tuning, formal retry, replacement or pooling occurred.

**D.** Full acceptance required all48 cases/all8 outer exits and the frozen raw
checks. Only17 cases have case-level exit/outcome records; one further case is
partial with an outcome but no entry exit;30 are unstarted. Only two batches
have observed outer exits. Five completed cases are in the interrupted third
batch. **The original full auditor fails at the missing batch-02/BATCH.json.**
A separately versioned read-only prefix auditor reconciles the preserved17
cases, but cannot invent missing outer exits or upgrade formal HOLD to PASS.

**C.** Supplied Linux x86_64 execution container, CPython3.13.5,
jsonschema4.26.0/referencing0.37.0. Docker/OrbStack image identity and a real
endpoint are absent from this evidence. Same-author separate audit
implementation/process is not external human review. The directory is trusted
and quiescent while completion evidence is read. Times are diagnostic, not
calibrated performance results; no cross-process clock subtraction is required
by the completion gate.

**U.** Uncompleted denominator, real endpoint/event compatibility, concurrent
publication, asynchronous recollection, cross-platform operation, actual
application effect, cost/latency and general reliability remain unverified.
Normalized coordinates are not fresh input authority or task success.

## Retained failures and continuation verification

Construction-01 exhausted its30-second budget after seven complete cases; two
planned construction cases were unexecuted. Its exit2 remains. Construction-02
and10 unit methods passed before the24-file formal freeze. The third formal
batch stopped under the outer tool envelope. No remaining batch was started.
The full-audit failure and original STOP are retained, not repaired in place.

In this continuation all821 original MANIFEST entries and all822 restored
files match. The unchanged prefix auditor exits0 and reproduces the original
RETAINED_AUDIT.json byte-for-byte, SHA256
`ee8418311624bd16b52c674c3d80ae302ceff9138b4eff44a9763a3b0388bab1`.
All12 evidence-corruption controls reject; all10 unit methods pass. No formal,
client, broker, fake-executable or GUI case was rerun in this continuation.

A literal95408-byte TAR/XZ capsule, stored in16 binary parts, retains822 files
and669923 original file bytes. SHA256:
`e4ec3c7e6d459af3e1130b05ca39bb5727ba2bbcf1b432fb3cd6283d2ad3e78e`.
PACK.json binds every part, the TAR extent and the original manifest. This
preserves original member bytes, not reconstructed ZIP container bytes.

One initial part02 transcription produced the wrong Git blob. It was never
attached to the branch; exact original bytes were re-uploaded and the expected
Git object ID matched. This is a retained publication incident, not a new
experiment or an allegation of GitHub corruption.

## Offline review without executing an allocation

From this directory, use a NEW output directory in a trusted parent:

```sh
python -S -B unpack.py /tmp/outer-call-4081-review
cd /tmp/outer-call-4081-review
python -S -B audit_retained.py . > /tmp/outer-call-4081-audit.json
cmp RETAINED_AUDIT.json /tmp/outer-call-4081-audit.json
python -S -B -m unittest -v test_gate
```

Expected: prefix audit exit0 with formal HOLD, identical audit bytes,10 passing
methods. The unpacker validates bounded part/XZ/TAR/member hashes before writing,
refuses an existing destination, and runs no archived code. Nine package
refusal controls pass. Do not run consumed `execute.py` or missing formal
batches. Reproduction of preserved evidence is not repetition of the experiment.

## Delivery roadmap and integration decision

Intake main `2c76b9e41fd9757cba43dd1968ed71695d8e1fd0`; executed source base
`2308b8301d69b7089a2e0636486736ed59b61537`. MCP read current main, README,
CURRENT_GOAL, ROADMAP, recent open/closed Issues/PRs and two branch pages.
Exact-path searches and intake-main path lookup found no competing publication.
The compare contains only unrelated additive changes, no target-source edits.
This is bounded/non-atomic reconnaissance; unpushed work remains unknown.

Owned path only `research/integration/host_ipc_outer_call_v1/`, branch
`research/ipc-outer-call-retained-20260922`. No shared runtime, workflow, root
roadmap, predecessor or other-worker edits. Delivery stages: immutable restore
and re-audit -> lossless publication and readback -> evidence-only PR -> current
head checks/review -> main readback if qualified -> only supported dependency-safe
own-branch cleanup. CI/review/merge status is recorded in the PR, not inferred
from local audit. Closing #4081 means archival delivery, not48-case acceptance.

Concrete #2789 decision: upper schema/grounding validation is not a replacement
for completion evidence, and strict consumer adoption requires a compatible
producer exit/envelope contract. This does not finish the desktop integration
spine or the repository ROADMAP. Local wrapper/publication incidents remain
under this question; no wrapper-only successor is requested.
