# Scope and integration report

Retrospective delivery under #4042; source questions #34/#3048, preceding exact-
value result #4007, causal-evidence distinction #1873. Neither a publication
failure nor this evidence PR creates a new fleet-wide dependency.

## H / T / D / C / U

**H:** A current requested value and an acceptance receipt cannot determine
whether this accepted request committed an application operation in the declared
window. A trusted complete request-bound journal can distinguish those claims.

**T:** One original 36-case SQLite experiment (12 conditions, 3 repetitions),
36 application and 36 read-only observer children. State and event commit in one
transaction. Observer starts after application exit. Candidate sees only the
request, acceptance and delivered snapshot; the independent auditor reads raw
protocols and retained DBs without importing the candidate. Twelve construction
cases are separate. Formal retries, replacements and post-freeze edits: zero.

**D:** The original all-row/source/process/DB/decision gate passed. State-only
PASS33; own single commit plus final-state match9. Naive completion is contradicted
by complete event evidence18 times and unestablished6 times. Candidate unsupported
completion0. All15 frozen semantic corruption controls reject. A separate original
source-change control remains retained; no missing evidence was invented.

**C:** A state-achievement request may legitimately succeed without a new action.
A same-value action can commit without changing state. A committed action can
subsequently be overwritten. An event is not evidence that the operation was
counterfactually necessary for the observed value. A full journal is a stronger
input than a state snapshot, not a free efficiency improvement.

**U:** Supplied Linux x86_64/CPython3.13.5/SQLite3.46.1 execution container only.
No Docker/OrbStack image attestation, real GUI task, model/provider, input,
experiment network, user data, shared runtime change, authentication, crash/power-
loss, concurrent acquisition, log retirement or distributed external effects.
Sequence/integer equality determines categorical gates; same-domain monotonic
nanoseconds only check process ordering. No calibrated physical uncertainty,
latency/token benefit, natural failure frequency or product claim is made.
Separate implementation/process by the same author is not independent human review.

## Retained per-condition decisions

Each condition has three fresh cases. The previous state-only verifier passes
all except OWN_THEN_OVERWRITE. Its weaker output is preserved unchanged.

| Condition | State | Request-event evidence | Complete this request |
|---|---|---|---|
| OWN_WRITE | MATCH | APPLIED_ONCE | yes |
| PREEXISTING_NO_EXEC | MATCH | NOT_APPLIED_IN_WINDOW | no |
| FOREIGN_WRITE | MATCH | NOT_APPLIED_IN_WINDOW | no |
| ROLLBACK_PREEXISTING | MATCH | NOT_APPLIED_IN_WINDOW | no |
| OWN_NOOP | MATCH | APPLIED_ONCE | yes |
| FOREIGN_THEN_OWN | MATCH | APPLIED_ONCE | yes |
| OWN_THEN_OVERWRITE | DIFFERENT | APPLIED_ONCE | no |
| DUPLICATE_OWN | MATCH | APPLIED_MULTIPLE | no |
| WRONG_PAYLOAD | MATCH | REQUEST_CONFLICT | no |
| INCOMPLETE_HISTORY | MATCH | UNKNOWN | no |
| WRONG_INCARNATION | UNKNOWN | UNKNOWN | no |
| PRIOR_OWN_OUTSIDE_WINDOW | MATCH | NOT_APPLIED_IN_WINDOW | no |

The wrong-incarnation row can pass the old value-only check while the new
identity-bound state remains UNKNOWN. That is different information/scope, not a
retroactive defect in the previous verifier. Request-event counts are APPLIED_ONCE
12, NOT_APPLIED_IN_WINDOW12, APPLIED_MULTIPLE3, REQUEST_CONFLICT3, UNKNOWN6.

## Integration decision

Keep at least three separately typed claims in the #34/#2789 result boundary:
current state satisfaction; own committed-event status in a declared window;
and counterfactual causal attribution. No missing or non-matching journal can
be repaired by promoting a state-only PASS. A NOT_APPLIED_IN_WINDOW result is not
permission to replay: later work may still happen outside this finite window.
No production adapter is promoted by this report; source ownership, current
application identity, complete windows and effect semantics need validation on
an actual integrated entry path.

## Publication validation

This continuation inspected main/direction/failure routing, recent open and closed
Issues, PRs and125 returned branch names. Exact allocation/path searches were empty;
unpushed work remains unknown. #4007 owns the earlier90-case delivery; #3951/#3217
and crash/retention/cursor studies remain untouched.

The supplied ZIP hash,109 checksum entries and110 original research files passed.
Unchanged audit output was byte-identical,14 unit methods passed, and the original
110-file inventory stayed unchanged. A fresh capsule restore also reproduced
110/110 files and the same audit bytes. Eleven postformal packaging rejection
checks passed. These are offline verification and engineering checks, not new
scientific samples or external approval. GitHub source readback and current-head
CI/review are separate delivery gates recorded in the PR, not presumed here.

Broad #34/#3048/#1873/#2789 and the repository roadmap remain uncompleted by this
publication. Scientific disposition, evidence integrity, delivery status and
product acceptance remain separate.
