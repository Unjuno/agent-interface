# Primary-assistant use of the existing guarded form method

The assistant used the existing integrated six-task Chromium fixture and
`RuntimeClient.execute_handles` directly. No helper model or app-server model
thread was started. After viewing task 1, the assistant selected field/submit
points A `[300,401]` / `[377,401]`; the existing mint path checked current pixels
against that source. The unchanged method checked the field, entered the token,
checked Submit after entry and activated it, with normal per-program admission.
Tasks 1–3 ran without a model resumption between these local stages.

On task 4, layout B invalidated the old target. The existing method yielded
`missing_symbol` with zero completed actions and zero old-target pointer
admissions. The assistant viewed sequence 72, selected B `[760,558]` /
`[689,634]`, and reminted. Tasks 4–6 then completed through the same method.
The assistant finally viewed the saved-state image (sequence 125).

The independent server oracle reports six exact submissions, one per task,
no duplicates, unexpected values or missing tasks. All 43 terminal programs
verified empty input release. The runtime and local driver exited 0. The
control journal and complete GUI evidence are retained.

## Timing and scope

Successful local method calls took 1,841, 2,025, 2,137, 2,783, 3,331 and 3,426 ms.
The stale-target stop took 351 ms. These exclude navigation, initial grounding,
minting, manual repair and tool orchestration; they are not end-to-end task
latencies. See raw nanosecond endpoints in the result files and SUMMARY.json.
This is one actual-use allocation, not a matched comparison or human baseline.
This conversation's per-decision model usage is unavailable; absence of a
helper model does not mean zero tokens or free grounding.

This run exercises the existing guarded method, **not** the distinct
`compiled_gui_interface_v1` state graph. The local Submit check tests target
eligibility; it does not independently verify the semantic text-entry effect
before clicking. Final task correctness comes from the separate server oracle.
That distinction matters when extending the method beyond this fixture.

## Integration disposition

Keep this as evidence that the primary assistant can ground and repair an
existing reusable method while local checks govern intermediate input. It is a
stronger integration starting point than adding another caller framework.
The public native CLI still needs an explicit bridge to these existing method
and target-handle semantics; this run does not close that gap. The next adapter
must retain the pre-submit target refusal, partial actions, input release,
independent scoring and cold/repair accounting.

`interaction-driver.py` is the exact accumulated local orchestration used in
the three stages (initial, first, repair); its dead socket and historical paths
are retained, not advertised as a fresh-launch command. It selected points
only after the corresponding images were viewed. `client-source/` copies
selected unchanged components, and runtime source identities remain in
`runtime/sources.json`. `first-results.json` retains the task-4 refusal;
`repair-results.json` retains the deliberate repaired continuation. The
temporary journal was not replayed as a new action. SHA256.json covers all
evidence before this README; paths have not been rewritten.
