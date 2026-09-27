# OpenTTD wrong-anchor recovery v2

## Question

Can the anchor-first interface recover when its first semantic probe is wrong,
without granting target-click authority before the ambiguity is resolved?

This is a deterministic fault-injection study. It does not estimate the model's
natural error rate. The injected source is the retained Luna-low failure at
`[436,51]`, whose archived one-receipt decision is `expand_search`. The live
allocation adds the newly observed whole-surface translation and normalizes the
result to the nearest screen-derived toolbar slot.

## Preserved preflight failure

Study `openttd-wrong-anchor-recovery-live-01` never reached the runtime. The first
launcher used Windows Python, where `fcntl` is unavailable. The WSL launcher then
found that Windows-generated backslashes in preregistered relative paths were not
portable. No model call or input admission occurred. The preregistration and a
typed failure record are retained. V2 writes portable POSIX relative paths and was
preregistered as a new study instead of overwriting v1.

## Fixed live allocation

- app/task: OpenTTD 13.4, open company finances;
- seed: 991004;
- requested surface movement: `[20,8]`;
- observed surface movement: `[21,28]`;
- model: `gpt-5.6-luna`, low reasoning, no subagents;
- retry policy: retain the first runtime allocation, with no model, task or runtime
  retry;
- injected archived point: `[436,51]`;
- translated probe point: `[457,79]`;
- nearest detected wrong slot: `[456,79]`;
- bounded radius-two candidates: `[410,79]`, `[433,79]`, `[456,79]`,
  `[479,79]`, `[506,79]`.

The first hover yields one persistent receipt at `[456,79]`. Luna returns the
strict `EXPANSION_REQUIRED` result, which has observation authority only. The
interface then collects the other four receipts in bounded three-plus-one batches.
The same Luna route selects receipt 5 at `[506,79]`. An exact rehover reproduces
the selected tooltip before ordinary input admission. The released click opens
company finances, and the independent title oracle shifted by `[21,28]` passes.

There is exactly one `button_down` admission in the complete runtime event stream.
Its operation id is the final click operation. Hover moves occur earlier as active
observation probes, but no target click is admitted before semantic selection.

## Measurements

| Measure | Result |
| --- | ---: |
| Slot detection | 159.662 ms |
| Wrong-anchor hover submit to return | 1,340.926 ms |
| Decision start to first verified receipt ready | 1,573.486 ms |
| Decision start to semantic selection | 20,355.623 ms |
| Decision start to independent evaluation | 24,956.241 ms |
| Initial receipts before decision | 1 |
| Added receipts after expansion | 4 |
| Durable calls | 18 |
| Exact frames | 50 |
| Anchor-decision input tokens | 8,107 |
| Expanded-selection input tokens | 8,280 |
| Total measured model input | 16,387 |

The prior accepted-anchor live route used 14 durable calls and 39 frames. The
recovery therefore costs four additional durable calls and eleven frames in this
fixed UI route. Its end-to-end latency and total model tokens are not a matched
comparison: the fault allocation injects the archived point and omits the earlier
coarse-candidate model call. The scoped recovery increment is one additional
8,280-input-token semantic selection after four extra receipts.

## Independent audit

The audit passes on Windows and WSL. It verifies preregistered source hashes, the
archived fault and translation, screen-derived slot structure, all 50 exact AIT
frame reconstructions, every terminal release, both raw model event streams,
compact presentation pixels, receipt composition, strict decisions, exact
rehover, the single final button admission and the shifted independent oracle.

Decision: `RETAIN_WRONG_ANCHOR_RECOVERY_EVIDENCE`.

## Limits and next step

This proves that the current interface can recover from one deliberately injected,
previously observed wrong OpenTTD anchor. It does not prove a natural failure rate,
general recovery, resize/reflow transfer, another application, causal speedup or
human-tempo operation.

The next useful comparison should exercise anchor-first acquisition in another GUI
domain or layout where tooltip semantics and control density differ. Repeating the
same fixed OpenTTD fault would add little evidence. A later natural wrong-anchor
episode should be retained when it occurs, but it should not be manufactured or
reported as a natural error sample.
