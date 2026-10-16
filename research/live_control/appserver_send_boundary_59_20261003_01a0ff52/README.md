# Existing app-server caller: send before response deadline

Read this qualification before interpreting the first PASS. Six prospective
ordinary native macOS27.0.1/arm64 Python3.12.13 cells ran once at07:27:42–44UTC,
from main dd6f54bf and the unchanged6303-byte client. This is a concrete
pre-response finite-wait boundary through its actual request API, not an
adopted client, actual Codex/model/GUI action, control-task result or efficiency
measurement. Source and first outcomes remain unchanged.

Both full-owned-pipe conditions retain65536 prefilled bytes, observed
would-block and no peer stdin reads. At250ms nominal checkpoints the current
client remains at source _write line48 / request line67; its response deadline
local is absent. Only explicit owned-peer termination releases it, with the
first BrokenPipeError preserved. Request timeout50ms currently means response
wait after sending; this study does not invent an existing whole-call promise.

| Source path through request | Healthy short | Full pipe,62-byte record | Full pipe,32057-byte record |
|---|---|---|---|
| Current buffered client | Exact inert result | Still _write at251.650ms | Still _write at251.514ms |
| Existing exclusive-unbuffered writer | Exact inert result | WriteUncertain at59.011ms,0/62 | WriteUncertain at60.201ms,0/32057 |

These are single directed descriptive observations from perf_counter_ns, not
medians/maximum delays/error rates/paired efficiency gains. Each elapsed value
subtracts timestamps in one driver process; peer-clock ordering is not inferred.
The inherited writer budget is50ms; observed59–60ms confirms scheduler
overshoot, not a hard50ms bound. A separate later request is refused by its
poison flag with unchanged OS-write-call and diagnostic-record counts.
That prevents appending after uncertain delivery; it does not deliver cancel,
finish, reconnection, lease expiry, physical release or a task effect.

The reference changes only the research transport composition: subclass the
unchanged client _write, detach the newly owned stdin TextIO and buffered wrappers
to exclusive raw FileIO, then use the existing bounded_pipe_writer_v2 with
64KiB ceiling and50ms budget. OSProbe transparently delegates and records only
that writer's OS calls. Current TextIO C writes are not counted by that probe.
Current dispatch/cache/journal/notification semantics are not repaired.
No concurrent buffered user can share the reference fd; no production/default
promotion, Windows/Linux equivalence or new writer framework follows.
Prefill is controlled pressure, not a naturally measured stalled model server.

First frozen separate source/data-only reader accepts all6 saved rows but
rejects only9 of12 copied controls. It accepts two Boolean-alias follow-up
counters and a contradictory ready mode. Original reader/results/control
outcomes are retained. Post-result v2 changes only strict integer counters,
ready-mode joins and output filename; it accepts the unchanged6 original rows
and rejects all12 controls. It imports no producer/client and starts no transport
child. This is scoped sensitivity, not complete causal/authenticity validation.

The single comparison supervisor exits0; all6 driver subprocesses exit0 and
all6 peers exit-15 after explicit native termination. Reader/caller/owned stdin,
stdout, stderr endpoints end closed. All12 actual driver/peer PIDs were absent
in a later owned-PID scan. First v1 copied-control tool exit0 is observed but
its individual start/PID/exit receipt was not captured; do not replace that
missing custody with JSON time. Peer argv is stored as a relative reproduction
projection; the exact invocation is visible in frozen run_cell source, but no
separate full peer argv snapshot was captured. Raw frame names are basename-only.

All Python snapshots/helpers are inert .py.txt. No active source, test
discovery, workflow or native/formal allocation is changed/replayed. To inspect
saved data only, restore a private copy with .py.txt renamed .py and run
python -B audit_saved_v2.py there. Frozen producer entry points must not be
invoked by a reviewer. Reconstruct copied controls by replacing the named
execution/<cell>/result.json with changed-controls/<name>/result.json in separate
saved-data copies; see changed-control-index and controls-v1/v2. No original
raw is rewritten. PLAN/source pins and the flat MANIFEST bind all saved files.

This directly exposes a model-boundary send wait that can prevent the existing
control caller reaching its response/recovery logic. It is sufficient to keep
whole-call timeout claims conditional and to evaluate the existing writer under
exclusive ownership. Future integration still needs partial delivery, bounded
serialization/locks/journal/cleanup, reconnect/old-consumer fencing and appropriate
live task/release/efficiency evidence. #6945/EOF repair, #6952 response IDs and
other authors' startup/journal cleanup remain separate. #59/#57 remain open.

First staged whitespace check exited2 for five immutable helper snapshots with
an extra blank line at EOF. It was stopped before commit/send. Original bytes
remain unchanged; .gitattributes lists only those five inert snapshots and
ignores only blank-at-eof. Active source/docs and other whitespace checks are
unchanged. This is publication formatting, not a native/reader retry.

Publication checks:22 workspace unit methods pass, exit0. First public navigation
check exited1 because the sparse checkout lacked six unchanged public docs;
that first log is retained. Reading only their exact pinned Git blobs completes
the declared checker closure; repaired navigation passes26 docs/1641 relative
links, exit0. No native or workspace-unit replay. The added live_control row
is outside the central26-doc roster, so its single new tracked target is checked
separately rather than inferred from that count.
