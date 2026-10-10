# V39 session child-pipe composition A01

**A01 disposition: `HOLD_CONSTRUCTION`. A02 disposition:
`PASS_CHILD_PIPE_TRANSPORT_SCOPED`; audit V3: `PASS_AUDIT`.** The frozen A01
runner stopped before child launch because its freeze omitted `python_version`;
the error and independent failure audit are retained. A02 corrects that
runner/freeze wiring under a new freeze and output path, then sends the retained
cancellation-cleanup event through an actual local Python child stdout pipe.

The exact session `emit` serializer ran in the child. The exact V39 controller
`reader`/`wait` functions consumed one real `stdout=PIPE` line. The child exited
0 with empty stderr; one event reached the controller unchanged except for the
expected integer `emit_ns`; both nested per-key release records survived and all
authority flags remained false. The source-tree merge and all source/input
hashes are pinned in `FREEZE-A02.json`; A02 candidate and raw files are under
`results/a02/`.

Audit V1 and V2 construction failures remain intact. Versioned audit V3
independently validates the source refs/blobs, input, pipe row, writer logs,
decoded row, authority, process closure, and recorded raw hashes without
rerunning the candidate.

This closes only the local child-process JSONL transport boundary for this
synthetic retained event. It does not invoke session `main`, the real executor
or input owner, X11, ViZDoom, a planner/model, GUI/OS input, useful feedback
during planner latency, bounded recovery, threat efficacy, matched outcomes, or
MAP01 completion. The live #59 allocation remains unassigned and the Issue gate
remains open.
