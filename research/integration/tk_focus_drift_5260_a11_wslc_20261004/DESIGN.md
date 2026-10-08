# #5260 A11 prospective actual-GUI post-admission drift probe

Preparation only. No source freeze, formal allocation, candidate/auditor run,
or actual GUI input has occurred for A11. A09/A10 consumed runs remain unchanged.

H: In a private actual Tk app, an observed target FocusOut after fresh target
admission can invalidate using the returned admission as current input authority.
Rejecting an observed drift before typing may prevent that finite misdelivery,
without making focus-check and key emission atomic.

T: Six fresh idle apps: STABLE, DRIFT_STALE_CONTROL, DRIFT_REFUSE each twice,
with preregistered shuffled order. Reuse exact A09 readiness/cache/pipe/app
components, with complete inherited source hashes in the NEW pre-input freeze.
All arms initially click target and require fresh target receipt. Drift arms
then click the decoy with XTest. Bounded polling must retain every read/sample
and observe a later bound target FocusOut followed by decoy FocusIn before
the next phase; missed/expired/unbound intervention is first METHOD_STOP,
not a success or a reason to try the intervention again.

Stable sends hxy and saves once. Stale CONTROL deliberately sends hxy using
the old admitted object AFTER independently observed drift, then saves once.
Refuse arm records invalidation and emits zero keys and zero Save after drift.
The stale input is an experimental control only, never a proposed runtime API.
No automatic target refocus, corrective replay or application-side focus forcing
is introduced. Existing decoy initialization is retained as fixture setup only.

D: Method gates require frozen source/image/fixture/commands, fresh token/PID,
complete readiness/pipe/read/write/cache/diagnostic/cleanup custody, observed
drift sequence and exact ordering initial-admit < intervention < observed drift
< first control key or refusal decision. App stderr must be empty, warnings
from host retained separately. Each app must terminate once with retained
key/event/frame/field/Save evidence; original independent auditor first result
is immutable. Any missing gate is STOP/UNQUALIFIED with no allocation retry.

Finite H threshold: both stable rows exact target hxy/emptydecoy/save1; both
stale rows observed keypresses and exact decoy hxy/emptytarget/save1; both refuse
rows zero post-drift key/save and empty fields. Otherwise first H_FAIL retained.
No causal ranking from six cells, no probabilistic reliability estimate.

C: Single own WSLc private Xvfb:97 container, no network/model/GPU/user display;
CPU0.5/512M requests only, swap/cgroup warnings retained and caps unproven.
Before freezing/executing, refresh main/open PR/Issue/resource contention,
claim only the owned CPU allocation and publish prospective conditions.
New additive package/branch; never edit peer paths or frozen A09 sources.

U: This is explicit local intervention, not naturally occurring focus drift.
Observed app FocusOut/decoyFocusIn is a private oracle, not a public sensor.
Ordinary app effect, useful feedback, physical key release, model recovery,
matched human tempo, broad multi-app reliability and main runtime promotion
remain unresolved. A final recheck cannot eliminate the remaining race.

Implementation order: first test no-input refusal and strict drift receipt
identity/order/timeout behavior using real OS pipes; implement bounded observer;
derive fresh candidate schedule/intervention; derive independent auditor and
copied-packet corruption controls; construction tests; publish all prospective
source hashes/conditions; execute candidate once/auditor once; retain first
result; verify saved packet; batch PR delivery. No GUI run before these gates.
