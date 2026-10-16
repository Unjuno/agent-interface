# V39 typed-event timing: current-main convergence of #8867

Parent [#59](https://github.com/Unjuno/agent-interface/issues/59).
Candidate [#8867](https://github.com/Unjuno/agent-interface/pull/8867), exact head
`598109fd6329ef88ec469557ae4beae2a2ef3002`.
Base `5abbc37e7674d52ef452f08f64bce3b8cb82fd0b`.
Reviewed runtime/test delta `4fa7a07d2ed89d3038c9b26294f54e4eed403222`.

The old `emit_ns` precedes two JSONL appends. Treating it as transport departure
confounds producer log work with serialization, stdout delivery and controller
dispatch. The selected session now stamps typed-event stdout handoff after both
appends and before stdout serialization/write. Actual V39 reader/wait stamps
parse, enqueue, dequeue and monitor entry/exit. The report keeps legacy arrays,
adds explicit aliases and per-event rows, and marks missing/reversed/non-integer
stages incomplete. Monitor exit is stamped even if the monitor raises.

The three-way transplant conflicted at the reader changed since the candidate.
The current duplicate-member JSON hook and control-boundary refusal were retained;
the new stamps do not replace failure cleanup, target authority or source refresh.
The original six candidate files and the four-file transplant patch are retained
in `original-candidate/`; the adopted source is separately frozen in `sources/`.
AST test harnesses now execute the actual current failure guards.

## Checks and decision

H: stage boundaries can distinguish producer pre-handoff work, controller queue
wait and monitor service without weakening current refusal paths.
T: use actual extracted session emitter and V39 reader/wait, local temporary
JSONL files and an in-process serialized stream/queue, plus existing targeted
retirement, artifact reconciliation and cleanup regressions.
D: ordered complete rows, explicit incomplete rows, joined raw/stdout/controller
records, retained primary exception, duplicate JSON and control-failure refusal.
C: added timestamps and the second typed-event serialization themselves add
work. These construction checks cannot show reduced latency.
U: no GUI, game/provider, actual observation capture or matched performance run.
The composed timing test is in-process; it does not characterize OS pipe latency
or validate child/parent clock synchronization experimentally.

**Adopt the instrumentation; keep live timing/effect/recovery qualification open.**
Normal and optimized Python each passed **70 methods / 10 modules**, zero skips.
Seven detailed rows per mode and **59 source pins** include the two actual AST
source files, which are not imported as game/controller entrypoints.
The existing owned-Python stdio retirement regression runs separately in the
suite; it is not the timing measurement. Other custody regressions use Fake X.
No WSLc, Docker, real display/input, game, provider or model execution occurred.

The initial three-test baseline failed on the absent parent stamps, summary
helper and stdout handoff marker. `exploratory/` preserves that output and later
12/17-method checks. Full final stdout/stderr and result JSON are retained.

## Saved-only readback

`read_saved.py` uses standard-library JSON/hash checks without runtime imports.
It verifies all six original candidate files, the 59 frozen sources, exact suite
and row inventories, interval arithmetic, raw log→stdout→controller joins,
incomplete states, and error/refusal records. Each report rejects eleven mutations,
including erased handoff/log/source, a duplicate row, false completeness, wrong
interval and suppressed errors. Readback itself passes normal and optimized.
`SHA256SUMS.txt` checks the new packet's exact member inventory; normalized source
pins use LF and the original candidate bytes are preserved separately.

## Meaning of the spans

`stdout_handoff_started_ns` is **before** serialization, print and flush.
Its interval to parent parse includes those stages, scheduling and JSON parsing.
`controller_enqueued_ns` is before queue insertion, so queue wait includes that
operation. The report states the same-host monotonic-clock assumption; timestamp
order alone does not validate clocks on another host. `events.jsonl` and
`delivered.jsonl` retain producer log-start rows without the later handoff marker;
the enriched row is retained by controller events. No artifact is rewritten to
pretend that a marker existed before its actual boundary.

This supplies measurement capability through the selected caller. It does not
prove useful environment response, physical release deadlines under blocked I/O,
session/controller-death recovery, task success or matched token/latency economics.
Those remain under #59/#57 and the preserved V15 selection work.
