# CURRENTNESS_INVALIDATED decision barrier v1

TASK: CURRENTNESS-INVALIDATED-DECISION-BARRIER-20260918-001
BASE: b6b716963fa1559f375d516180dcae8128807ca5
ISSUE: #1087

H: incrementing a required decision generation by one on each currentness invalidation should make every older installed policy inadmissible until a fresh decision is installed.

T: standard-library container only. First discriminator includes a deliberately skipped/high installed generation. No GUI/X11/model/provider/task-input/shared-runtime action.

D: any installed pre-invalidation policy admitted after invalidation is FAIL_STALE_POLICY_ESCAPE.

C: planner-supplied generation numbers may be sparse or ahead of the runtime-required counter.

U: synthetic state semantics only; no runtime/task-performance claim.
