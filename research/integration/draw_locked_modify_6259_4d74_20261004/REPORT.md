# F03: controller lock did not suppress measured modification callbacks

Issue #6259 successor composition test of F02 (#7354) and #2122 B05 (#7345). Earlier outcomes unchanged.

H: display-controller notification suspension might hide modification callbacks while external writes still occur. This hypothesis was not supported in the measured schedule.

T: one actual WSLc invocation, two fresh stable/mutated documents. Controller lock held before listener registration through split reads. Same actual F02 independent writer changes A1800 then B2700 between controller reads of A and B; writer reports controllers_locked=true. Controller records lock and listener counts before/after reads and after unlocking.

D: producer/container exit0/errors[]; unchanged effect and notification auditors both exit0. First notification decision SUPPORT_MODIFY_DETECTION_SCOPED. Stable counts0→0 and unsatisfied split. Mutated counts0→4 before unlocking, split false goal rejected, after-unlock count4. Controller lock true before/after reads, false after release. Independent observer and saved FODG preserve actual final A1800/B2700. Display notification suspension did not suppress these XModifyListener callbacks. Do not manufacture the hypothesized failure.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d; CPU1, memory512MiB, networknone, user65534:65534, read-only source mount/writable output. No model calls. Producer and effect-auditor command used PYTHONDONTWRITEBYTECODE=1. Notification-auditor command instead contained PYTHONDONTWRITECODE=1, an ineffective environment variable. Preserve this first invocation; no corrected retry occurred. Root filesystem is not claimed read-only.

U: measured interface composition only, not comprehensive mutation coverage, authenticated generation, atomic snapshot, callback timing guarantee, future writers, positive admission, task/model value or production adoption. Stable control is unsatisfied. Stop additional controller-lock/property variants without a new concrete gap. F02 remains unchanged.

Evidence: seven pre-run frozen sources, literal F02 controller and unchanged auditors, original raw/run/audit outputs/exits, two saved FODG documents and independent process outputs. FILES.json covers copied members; publication README, FILES.json and .gitattributes excluded. Source/raw review supplements narrow auditors. Publication integrity does not independently prove freeze chronology; original retained execution records provide that chronology.

First result: https://github.com/Unjuno/agent-interface/issues/6259#issuecomment-5975281599
