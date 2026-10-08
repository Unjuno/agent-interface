# Production spine: additive execution-window usage audit

Decision: **RECORDED_USAGE; integrated efficiency remains HOLD.** This is a
read-only post-hoc audit of the already completed production-spine trials,
not a new trial or a revision of their freezes, scores, or adoption labels.

The original correctness and runtime evidence is retained in
[production-spine-main-01](../production-spine-main-01). Its 993-file archive
SHA-256 is `c00f99f91e3a4d6a11925af608637b55a203e9fdd37f6b9a3b5880f19cca90e5`.
The original runtime source was `3a8936cf20df11ec884244e76c791434fbf5d5fe`.

## Observed whole-context usage

| Explicit window | Outer tool calls | Unique model responses | Input | Cached input (subset) | Uncached input | Output | Reasoning output (subset) | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stopped guarded, seed 1001061 | 4 | 4 | 758,180 | 752,128 | 6,052 | 1,281 | 276 | 759,461 |
| Guarded, seed 1001062 | 39 | 41 | 5,978,297 | 5,663,232 | 315,065 | 17,265 | 2,594 | 5,995,562 |
| Direct, seed 1001062 | 16 | 16 | 1,789,866 | 1,747,072 | 42,794 | 2,519 | 82 | 1,792,385 |

All three windows have no tool calls without chronologically associated usage,
and no repeated response IDs. Cache-write input is zero in these records.
Cost in dollars is **unavailable**, represented by null, rather than zero.
Selected `turn_context` records request `gpt-6.1-sol`, effort `medium`;
this is not an attestation of an internal provider model revision.

These are outer orchestration calls, distinct from the previously reported
public host calls (guarded 77, direct 29). Both successful arms completed 6/6
tasks exactly once. The stopped arm completed 0/6 before first input and stays
in the report. No totals from diagnostic cumulative `token_count` events are
added to the actual per-response `token_usage_record` values.

## Selection and limitations

[selection.json](selection.json) fixes original call IDs for each first public
observe/host-construction request through its host-close outer output. Source
log order determines membership. All per-response usage inside these windows
is retained, including commentary, interruptions, extra previews, and recovery.
The guarded window crosses two turns. Calls containing closure also contain
scoring/source reads; their entire usage is included. A response authoring
multiple pending calls is counted once. Chronological association is **not**
provider-attested per-tool attribution.

Preparation, helper construction, cold acquisition, and analysis outside these
boundaries are excluded. These totals therefore do not measure all-in cost or
break-even. Fixed execution order, changing shared context, compaction, the
conversation interruption, and different control work prevent causal claims of
token savings. Neither elapsed host time nor these totals establish human-tempo
control, useful-feedback latency, semantic completion latency, or broad task
reliability. Issues #57 and #59 remain open.

[projection.json](projection.json) contains selected usage, call identities,
requested model metadata, source line indices, and original line hashes. It
excludes private request/output text, the full conversation, and cumulative
thread usage. The private session is not published. Reproduction requires that
local session and uses the read-only shared scanner:

```sh
python3 research/live_control/primary_usage_projection.py \
  --session /path/to/private-session.jsonl \
  --selection runtime/results/production-spine-usage-01/selection.json \
  --output /path/to/new-projection.json
python3 -m unittest discover -s research/live_control -p test_primary_usage_projection.py
python3 -O -m unittest discover -s research/live_control -p test_primary_usage_projection.py
```

The scanner stops after all selected end outputs and refuses to overwrite its
output. Missing boundaries, overlapping windows, unmatched outputs, conflicting
response identities, and inconsistent counters fail explicitly. Missing usage
is partial/unavailable, never fabricated as zero. Seven accounting tests pass
both normally and with `-O` on Ubuntu 24.04.4 / Python 3.12.3 / WSL 3.0.1.0
(WSL 2 execution mode). No GUI benchmark was rerun for this audit.
