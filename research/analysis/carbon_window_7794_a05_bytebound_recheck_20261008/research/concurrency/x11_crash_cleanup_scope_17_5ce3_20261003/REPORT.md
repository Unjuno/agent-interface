# First formal outcome: STOP / METHOD_FAIL, not a crash-science verdict

Issue #7024, prospective 18-cell successor to #821, source main 7637ef4.
Candidate ran exactly once on the private owned OrbStack engine and immutable
image. First healthy cell stopped; candidate exit 1, not OOM, no live container.
No SIGKILL exposure, remaining 17 cells not run, formal auditor not invoked.

The saved owner stream proves accepted public dispatch, completed ops 0..3,
one F8 press/up, a completed >=300ms fixed-delay wait, verified source release.
The supervisor registered while the owner was live but its next packet was
STOP_EOF_NOT_ORIGINAL_OWNER_DEATH. Its EOF guard failed before any supervisor
input. The collector then recorded STOP_SUPERVISOR_RESULT. Normal final fixture
emergency emitted zero; Xvfb exited 0 on owned teardown.

Root cause supported by source and packets: owner closes its lifetime writer
explicitly after completion but before process exit. EOF does not imply that
the process is already Z/missing at the immediately following /proc read.
The guard did not emit the actual state/start-tick values; do not claim a measured
race duration, particular live state, or exclude every alternative identity issue.
No conclusion about crash-held persistence, empty-scope false composition,
reference cleanup, bystander preservation, or production recovery is established.

Frozen method, plan, public seven-file byte-identical source snapshot, first raw
row, actor streams/stderr, environment and container receipts are preserved.
Initial hand-oracle RED included 12 assertion failures and two TypeErrors;
corrected RED 14 failures then semantic RED 14 failures, GREEN 14; source joins
added four RED failures, latest GREEN 18. Saved-result test initially assumed
Xvfb -15 but actual clean exit was 0; only the post-run assertion was corrected,
first failing receipt retained. No frozen producer/oracle/source was changed.

Applicable local checks: host package 20 (18 hand oracle +2 saved STOP), workspace
21, scorer replay 2; immutable-image package 20. These are method/packaging and
saved-evidence checks, NOT formal scientific PASS. No full-repository CI claim.
Full #17/#2437/#57 roadmap remains open. Prior #6999/#7010 evidence untouched.

Next experiment must be a prospectively registered successor with a fresh output
allocation: use actual OS process-lifetime writer closure (not explicit early
close), then bounded identity-checked death observation; timeout preserves STOP.
Do not weaken the original death gate or reinterpret/rerun this consumed stage.
There is no security isolation or host CPU exclusivity claim for this normal VM;
all input was private Xvfb, not the user display. Own VM stopped, images/exited
containers retained, no unrelated worker or resource altered.
