# Validation-completion age — premeasurement plan (#4010)

Allocation: `validation-completion-age-20260922-01`.
Intake main: `81a004527e5124e54fb1f4da5785fc0c5640ef50`.
Parent #2117 and closed #3953 remain separate; no production promotion.

## H / T / D / C / U

H: receipt-time freshness does not imply freshness after validation. A current
post-validation monotonic sample can bound age at that sample. It cannot prove
unchanged display state or later action/model freshness.

T: three fixed serial batches, seven cases each, one fresh private authenticated
Xvfb and one separate native capture/renderer process per batch. Order is the
following list rotated left by batch index: PROMPT_VALID, DELAYED_UNCHANGED,
DELAYED_CHANGED, PROMPT_CHANGED, STALE_BEFORE_RECEIPT, BAD_DIGEST, WRONG_ID.
Exactly 21 formal cases, zero retries/replacements/pooling/post-result tuning.
Each original packet is validated once; both interpretations share that result.
The original full transport module and native.c are unchanged. Only a transparent
pixel_digest callback wrapper injects a declared display change and/or >=60 ms
wait, then computes the original exact digest. This does not measure normal hash
cost, throughput or GIL causality. The stale-receipt control delays the handoff
before stamping the declared received_ns; both actual pipe receipt and handoff
are retained. A prompt-changed control deliberately exposes the distinction
between recent and still-current pixels.

D: PASS_VALIDATION_COMPLETION_AGE_BOUNDARY_SCOPED requires all 21 cases, source
and complete raw packet/pixel/process/external-exit reconstruction, six delayed
validation cases receipt-FRAME_FRESH but completion age >20 ms and candidate
refusal; prompt valid/changed positives fresh at the recorded sample; three
stale-receipt and six invalid digest/identity controls refused; changed pixels
independently established in both changed modes; no input/model/authority;
independent raw-only audit and >=8 rejected semantic corruption controls.
Complete candidate false freshness is FAIL_VALIDATION_AGE_ESCAPE; a complete
nondiscriminating or over-budget prompt is HOLD_BOUNDARY_NOT_ESTABLISHED.
Missing/changed source, process exits, rows or audit evidence is STOP/HOLD, never
PASS. Audit-integrity success is not automatically scientific success.

C: the verification delay is injected, not natural workload prevalence. A digest
identifies bytes, not authenticated origin or semantic currentness. Cooperative
private core-X11 drawing is not a physical-scanout or arbitrary-backend guarantee.
The second time sample precedes candidate return and any later use: the output
explicitly names that sample, not a future freshness promise. No bypass of
original schema/digest/identity refusals is permitted.

U: one provided Linux x86_64 container, Python 3.13.5; no Docker/OrbStack image
attestation, network-none claim, real model, user desktop, XTEST/input, installs,
GUI task effect, performance gain, calibrated uncertainty or production result.
CPU frequency/host load unpinned. Separate auditor means separate implementation
and process, not independent human review. Full #2117/#2789/ROADMAP remain open.

## Source, construction and stopping

Native.c is exact Git blob 92b2ca11117f6bcb80f45dbac62e16d62bb4f6fd. The complete
legacy_transport.py has SHA256 b4ce352c141406a47cebd2f210e997cc74748ae6b461edd2cdce12d699bb8c80.
The old performance allocation is immutable HOLD_EVIDENCE_INCOMPLETE (13/32).
Its complete archive remains a conversation attachment, not claimed hosted here.
Retained old receipts and selected posthoc examples are motivation, not new
formal data or a retrospective production bug. The legacy label always meant
fresh at receipt.

Construction01 source-path failure, construction02 Xauthority-family mismatch,
and construction03 old-Xlib string/bytes mismatch remain excluded. Construction04
completed seven cases; raw audit errors zero, 12 semantic mutations rejected,
12 unit tests passed. No construction row enters the formal denominator.

FREEZE.json commits source, binary, environment and this plan before batch0.
The binary was locally compiled from the exact source; its published hash does
not imply portable ABI equivalence. No code changes after formal start.
execute.py makes an exclusive consumed marker and actually waits for its private
child. Batch timeout12 seconds, bounded TERM then KILL; each batch must have a
successful observed exit, immutable bytes and the same freeze before the next.
Missing/failed batch stops the allocation. No asynchronous service is started.

Exact commands from the source directory, executed separately once each:
```
python -B execute.py 0 formal-01
python -B execute.py 1 formal-01
python -B execute.py 2 formal-01
python -B audit.py formal-01 --controls
```
The last command is read-only reconstruction, not another formal allocation.

## Conditional analytical boundary and variable table

| Symbol | Meaning | SI unit / storage | Definition and domain | Type |
|---|---|---|---|---|
| a | Native acquisition start | s / integer ns | Nonnegative same-clock XGetImage entry | scalar integer |
| b | Native acquisition end | s / integer ns | a <= b | scalar integer |
| r | Declared receipt sample | s / integer ns | b <= r | scalar integer |
| v | Post-validation sample | s / integer ns | r <= v, sampled after legacy return | scalar integer |
| B | Maximum age | s / integer ns | 0.020 s = 20,000,000 ns | scalar integer |
| c | Hypothetical exact sample instant | s | a <= c <= b, conditional backend assumption | scalar real |

For valid metadata, the old policy tests r-a <= B. The new gate additionally
tests v-a <= B. Since v>=r, v-a=(r-a)+(v-r)>=r-a. Therefore the earlier test cannot
imply the later one: e.g. receipt age 1 ms and validation delay60 ms give final
age61 ms. Conversely the later test implies the earlier age condition. Both
subtractions and B have the same time dimension; integer nanosecond comparisons
avoid rounding at the inclusive boundary. The tests cover equality and one-ns
overflow.

Under the conditional exact-sample assumption c in [a,b], v-c <= v-a. Thus the
new test bounds that capture's age at v by B. It says nothing about a later
instant, a new display update between c and v, or semantics beyond these pixels.
PROMPT_CHANGED is the explicit countercontrol. No input authority follows.

## Roadmap

Predecessor/source and collision checks -> excluded construction -> public
source/gate freeze and readback -> three one-shot batches -> raw-only audit and
corruption tests -> additive report/source/raw PR -> exact-head review/checks and
main readback if accepted -> only owned-branch cleanup when safe and supported.
Local execution/publication incidents belong to this same Issue, per #2789.

Primary API context: Python 3.13 time.monotonic_ns documentation,
https://docs.python.org/3.13/library/time.html#time.monotonic_ns ; exact incremental
hash semantics https://docs.python.org/3.13/library/hashlib.html . The experiment
uses the recorded installed implementation, not a claim derived from docs alone.
