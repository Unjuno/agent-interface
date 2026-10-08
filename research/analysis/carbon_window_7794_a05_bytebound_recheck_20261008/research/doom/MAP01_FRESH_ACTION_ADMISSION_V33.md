# MAP01 fresh action admission v33

V33 is a model-free controller construction over the frozen v32 source. It adds
one mandatory immediate-action validity stage and leaves v32, schema v5,
responder v9 and the unrun v32 preregistration unchanged.

For an active answer, schema v6 requires exactly one `action_validity` item in
addition to the separate `next_cover_validity`. The planner specifies bounded
critical health, maximum health loss, minimum ammo and current-snapshot age.
The semantic adapter requires a positive ammo condition for any fire-bearing
command and zero ammo dependency for movement-only commands.

The controller binds these semantics to the exact observation actually used as
the newest temporal-sheet source. It extracts both health and ammo from that
same X11 frame. This also removes a v32 timing ambiguity: cover submission can
deliver a newer observation after the cover-validity source was selected, so
the old prompt health was not necessarily the exact health in the newest model
image. V33 uses the image observation itself as the action source epoch.

After the planner finishes and the cover reaches verified release, V33 reads
health and ammo from the freshest single observation, constructs the generic
snapshot and evaluates the action predicates. Final-admission v2 independently
recomputes the entire receipt against the exact commands. Only
`READY_FOR_FRESH_EXECUTOR_ADMISSION` can reach the primary submission. A failed
or unknown action predicate records `REJECTED_ACTION_NOT_CURRENT`, discards the
returned action and its next cover, admits no primary program and proceeds to a
new planner decision.

Five focused controller tests cover schema/terminal semantics, current health+
ammo pass, zero and unknown ammo rejection, omitted/spurious ammo dependencies,
prompt source values and first Executor acceptance. Together with the semantic
adapter and final-admission tests,15 cases pass on Windows and Linux.

A deterministic eight-case composition replay now covers policy and planner
rejection, controller-invalid and terminal no-input, current-health rejection,
unknown-ammo rejection, valid first acceptance and later revocation. The first
six have zero Executor acceptance. The valid case has exactly one; revocation
retains that one historical receipt with no current authority.

This construction has not called the model, executed the game or passed actual
endpoint schema preflight. It therefore establishes no planner authorship,
latency, survival, gameplay, task-completion or human-tempo result. Before live
work, preregister endpoint-schema compatibility separately. Do not redirect the
already frozen v32 allocation to this source.
