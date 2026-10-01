# Input plus existing read-only application feedback

Integrated optional `feedback` into the production guarded MCP input tool. Input
receipt and application cue remain separate. After completed input and verified
neutral release, explicitly selected title feedback can return its own final
capture in this same reply. Defaults are unchanged. No sensor/model/automatic
continuation/retry/remint was added. Any unknown extension keeps full receipts.

Frozen source: 56b704f9ead16b8c6fc9dea7e5cb4b26256bf8f7. Archive SHA-256:
827c491539354f416da714053691c65b3225d9bf24629352f35724caf027477b.
Three fixed authored Tk cases, seed 1001068, one allocation each, zero input
replays. Primary reviewed six original images and grounded Save at [360,172].
Each case used observe, mint, input with explicit cue, close: four actual public
calls, one input program, two primary images and verified neutral release.
Independent application events were read only after all three owners and children
were terminal. Matched and rejected wait for a 600 ms delayed app response;
pending uses a 5000 ms app response with a 1000 ms polling budget. Closing the
pending fixture is experimental cleanup, not a general operation cancellation.

| Case | Returned cue/image | Input receipt | Call wall time | Independent task |
|---|---|---|---:|---|
| matched | SAVED | completed | 705.783 ms | one Save, SAVED ack |
| rejected | REJECTED / needs_review | completed | 731.359 ms | one Save, rejected |
| pending | PENDING / needs_review | completed | 1097.367 ms | one Save, no completed task at cleanup |

The timeout bounds polling, not total capture/serialization or blocking X11.
Times are local public call boundaries, not primary semantic awareness. This
study proves functional composition and exact image delivery in these cases;
it supplies no equivalent-route speed comparison, actual token accounting,
billing, model-generalization or human-speed result. HOLD_EFFICIENCY remains.
The live scaffold invokes the production public MCP server directly and does
not prove a separate relay/process route. Host STOP behavior is checked by
18 primary-caller unit tests, including all four cue verdicts. Scoped guarded
and presentation suites pass 38 tests both normally and under Python -O.
Audit rejects eight corruption categories, including non-neutral release,
false success/authority, wrong image/title and duplicate Save. These checks
are finite contract checks, not a formal proof. Preparation and first audit
failures are retained in PLAN.md and audit-first-failure.txt; no favorable rerun.

Run `python3 audit.py` and `python3 test_audit.py` in this directory. REPORT.json
contains local timings, independent events, cleanup results and limitations.
