# #4325 / #4316: pre-capture budget admission (cg42)

Allocation `capture-budget-4325-20260924-cg42-01`. Research-only native acquisition composition; no task-input capability. Own only `research/integration/capture_budget_admission_cg42_v1/**` on `research/capture-budget-admission-4316-20260924-cg42`. Intake main `55d6c6cead19fc02824d620c174bf0fd03681cf1`.

## H
For the pinned single-owner AUTONOMY_RESERVE policy and verified depth24/32-bpp/32-bit scanline-pad, LSB-first X11 format, an early decision on a **deep copy** of the ledger and the predicted exact raw ROI byte length can suppress image reads that would be refused. Final decisions on successful reads still use the unchanged policy and actual returned size. No early preview may consume the live ledger.

## T
Six schedules (NORMAL, CUE_FLOOD, DUPLICATE, VARIABLE_SIZE, CAPTURE_ERROR, OVERSIZE), two fresh repetitions, 12 private Xvfb sessions and 24 independent worker streams. Each session owns renderer + two capture workers + server. Same changing nonflat surface, quiescent during each paired request. Worker order alternates by request and repetition. Six fixed two-session batches run once. `source/schedule.json` is the exact schedule. No old pilot/native worker rerun or outcome pooling.

Both workers use byte-exact cb36 `budget.py`, AUTONOMY_RESERVE with total16384 bytes/packet4096/autonomous reserve8192. CAPTURE_THEN_CHECK attempts a native image read for every frozen request, then checks actual bytes. PRECHECK_THEN_CAPTURE first asks a copied Budget about exact expected bytes; a refusal skips acquisition. An eligible request attempts XGetImage, verifies returned length/depth, and only then asks the real Budget. Actual BadDrawable in CAPTURE_ERROR gives EVIDENCE_UNAVAILABLE, no debit/seen-ID insertion, followed by another distinct request attempt using the same ID on the valid source. This declared sequence is not a retry of a formal case.

All requested ROIs have valid geometry; oversize is valid X11 geometry but exceeds the packet budget. Each renderer draw is followed by an independent full-frame scoring capture not delivered to either budget. The scoring captures, drawing, JSON/Base64/wire overhead and ledger-copy overhead remain separate from worker-native payload accounting. No acquisition-speed, CPU, energy, token, human/model-use or task-success gate.

## D
PASS_PRECAPTURE_BUDGET_ADMISSION_SCOPED only with all12 first sessions, exact source/native/raw/process lineage, byte-identical paired exports and equal decisions/ledger per request, no candidate capture on pre-budget/dedup/packet-limit refusals, strict native attempt/byte reductions on CUE_FLOOD/DUPLICATE/OVERSIZE, NORMAL positive compatibility and CAPTURE_ERROR nonspending + later positive compatibility, output limits preserved, no input/authority, all owned exits0/cleanup, independent raw audit errors=[] and **all12 effective corruption tests** rejected without no-op/parser crash. Do not waive failed control gates. A complete scientific contradiction is FAIL; incomplete source/native/process/coverage/controls is HOLD/STOP.

Expected finite denominator:56 worker requests per policy; native attempts56 versus40; two real X errors per policy; 38 exported packets and18 autonomous packets per policy. Expected captured bytes208896 versus141312; exported bytes141312 per policy. These are frozen schedule arithmetic, not invented measurements. Actual recorded counts must reconcile independently. Full-frame scoring reads56, raw scoring bytes1376256, outside either arm's payload budget.

## Execution
1. Preserve previous mounted inputs and verify the old ZIP manifest; copy only unchanged budget.py as executed dependency.
2. Excluded construction with distinct `construction-` identities. Initial FamilyWild auth failure is retained; current xauth utility mechanism is checked before freeze. No overwrite of construction attempts.
3. Source/plan/environment/auditor/tests/controls freeze and GitHub exact-byte publication/readback before formal. Store full freeze source capsule; no registration claim until readback succeeds.
4. `python -B source/launch.py N` for N=0..5, one at a time; each child bounded30s under a40s outer call. Incomplete batch stops later batches. No replacement/exclusion/tuning.
5. Independent raw audit, then12 bounded copied-evidence controls. Read-only checks may be repeated and labelled, never scientific replay.
6. Full lossless evidence capsule, readable report, PR, exact-head applicable checks/review, qualified evidence merge and readback. Do not alter shared indices/runtime/workflows.

## C and U
Same-owner sequential ledger; no concurrent debit, crash/refund/durability semantics. Source/ROI/origin labels are cooperative. No arbitrary app, task input, source authentication, dynamic format, last-check/use atomicity, natural request-rate estimate, human cue utility or production promotion. The copied ledger costs time and memory and may be slower than a tiny image read. A denied capture cannot reveal its hypothetical later X error; paired disposition equality is scoped to the provided schedules, not all possible combinations of quota refusal and unavailable source. Budget admission is not a lease or action permission.

Times are same-host monotonic diagnostic brackets only. Physical calibration, combined standard uncertainty and coverage factor are unavailable; no numerical uncertainty is fabricated. Counts/raw bytes and hash equality are exact within the frozen instrumentation, not an independent server trace or general guarantee. Two repetitions are coverage, not a reliability sample. Prior cb36 and #4316/ac41/a8d2/#4318 remain separate.

## Sources
Python3.13 copy specification: https://docs.python.org/3.13/library/copy.html
X.Org Xlib image format specification: https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html
API specifications justify format/copy assumptions, not empirical outcomes. Actual installed versions are in environment.json and per-worker setup receipts.
