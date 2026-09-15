# Matched semantic repair comparison v1

The frozen comparison was intended to measure cached target-handle repair against
Luna-low visual reacquisition after the same Chromium width change. Both arms
would pay for initial visual grounding; only the reacquisition arm would pay for
a second image turn. Four fresh sessions, fixed `local/model/model/local` order,
seed213, complete call/image/token/wait accounting and independent task/release
checks were frozen in commit `c03fd4fd` before execution.

The first and only allocation did not produce a comparison. Arm1 navigated to
the private form, entered the exact token and captured its coherent source frame.
Its required initial Luna-low call then returned `Selected model is at capacity`
and exit1. The runner stopped immediately under the no-retry rule. One model
thread started, but no model message or completed turn exists and no usage record
was emitted. No target handle, resize, semantic probe or submission action began.

The two completed GUI prefix programs each completed four steps and released to
empty input. Owner close also verified no held key or button. The preflight was a
compatible cache hit with zero fresh calls. The 34-file/469,683-byte pre-receipt
manifest preserves the exact source frame, events, model request, process result
and capacity error. Independent Windows and WSL audits pass all11 diagnosis
checks.

This failure says nothing about local repair versus visual reacquisition. It does
show that service availability is currently discovered after GUI setup and task
entry. A new version should expose model invocation as a typed outcome and keep
`capacity_unavailable` distinct from a completed semantic result. It should
admit the GUI comparison only under a frozen availability policy and preserve a
later capacity refusal as a deferred, no-authority outcome. The v1 allocation
remains failed and will not be rerun.

There is no token advantage, recovery-time advantage, semantic completion,
general reliability, portability or human-tempo claim from this allocation.
