# Reusable native guarded form method

`native_guarded_form_v1.fill_and_submit` extracts the existing native six-task
form operation into an importable method. It accepts a live NativeHandleBridge,
explicit field/submit `(alias, offset)` references, text, a caller-selected fixed
wait and a receipt persistence callback. The six-task harness now uses this
same function for normal use and an explicitly grounded repair.

The method invokes the existing guarded field click plus CTRL+A/text/wait,
retains that result, then invokes the independently guarded submit click/wait.
Every input still goes through NativeHandleBridge's fresh target checks and
ordinary runtime admission. It does not introduce a model, target finder, sensor,
new handle registry, automatic repair or a new public MCP tool.

Both references and options are validated before input. A next step requires
completed input, recovery_required=false, and nonempty verified releases with
no held buttons or keys. A failed entry never proceeds to submit; a refused
submit retains the entered effect. `completed_actions` counts steps that passed
these completion/release checks, not semantic effects. Raw per-step results
remain authoritative. Dispatch exceptions propagate as potentially uncertain
delivery. A failed persistence callback prevents any later step.

The caller must supply `on_step(name, result)` and retain each receipt. The
provided harness writes tasks.json before a later input. It allows one manual
repair only for an initial refused entry with zero new emissions; it never
repairs by replaying a partially completed method. Existing waits remain 100 ms
in that harness; the reusable function has no wait default. Per-program guards
retain their own deadlines. This synchronous method cannot bound a blocked
callback or backend beyond their existing contracts.

Task success is not inferred. The method does not verify the semantic text value
between entering it and selecting Submit. It is suitable for the scoped form
fixture with independent final scoring; this evidence does not authorize its
use for consequential general desktop forms. It is also distinct from the
compiled_gui_interface_v1 conditional state graph.

[Primary six-task use](../../runtime/results/native-method-primary-01/README.md)
records cold grounding, reuse, a changed-layout refusal, manual repair and reuse
through this extracted method. Tests cover failed/unverified release, retained
partial results, persistence failure, uncertain dispatch and pre-input reference
validation. Public CLI/MCP method exposure and matched efficiency measurement
remain later integration work; the importable native function is not a portable
public API guarantee.
