# #5260 A05 — focus acknowledgement construction successor

H: In an instrumented disposable Tk app, a fresh target FocusIn receipt
can bound admission of the first key after a click better than XTest sync
alone. A wrong-target click must time out with zero key and Save requests.
This receipt is an app oracle, not a universal screenshot/public sensor.

T: New construction01 only: ten fresh apps, seeded order. NOW_TARGET and
ACK_TARGET each idle/busy x2 (eight rows), ACK_WRONG_TARGET idle/busy x1
(two). Same app always emits its focus evidence, including NOW controls.
One candidate and one separate raw/file auditor, each once/no retries.
Click once; ACK waits at most500ms polling1ms for a source/PID/token/target/
clock/active-state-bound receipt. No extra fixed first-key sleep. hxy with
20ms gaps, Save250ms after the last key only if admitted. App ends naturally
1500ms after readiness; wrong-target rows may click only, not type or save.

D: METHOD_PASS_CONSTRUCTION_ONLY requires complete immutable source/image/
fixture/argv/stream/app/readiness/focus/file/input identity and clean child
exits. ACK admitted rows must have acknowledged target before first key;
wrong-target rows must refuse keys/Save. Exact text is scored separately:
all four ACK_TARGET rows exacthxy/decoyempty => H_PASS_FINITE_FIXTURE_ONLY;
any nonexact or post-ack/pre-key focus drift => H_FAIL_FINITE_FIXTURE_ONLY.
NOW outcomes are observations, not qualification/retry criteria. A missing
receipt in ACK_TARGET is observed refusal, not a substituted row or retry.
Provenance/runner/auditor failure preserves first STOP, no source repair.

C: Cached WSLc Tk image217851fe68e7, private Xvfb/Openbox :97, same app
geometry and single-epoch ReadinessOnce helper as A04. Networknone, uid65534,
source/input RO, own outputs, requestedCPU0.5/512M only. Busy child2200ms;
auditor not importing candidate/ack admission implementation. Synthetic
wrong-token/PID/stale/boolean/state/sequence controls before input.

U: Construction finite10, no formal population efficacy, same-model task
benefit, screenshot-only focus detection, defaultwait or runtime adoption.
Atomic focus receipt plus a later sample does not make keyboard admission
atomic with the app; FocusOut between sample and key remains a race and is
audited, not assumed impossible. No useful-visual, physical-release, OOM,
resource enforcement, Docker comparison or performance claim. A02/A03/A04
first sources/results/consumed allocations remain unchanged; only new path.

Roadmap: TDD admission guard -> instrumented app/candidate/independent audit
-> new source/fixture/command freeze and scoped CPU record -> one10-row
construction -> readonly adversarial audit -> batch PR/main handoff. Any
later formal held-out or public sensor test needs a genuinely new freeze.

Status: preparation only; no A05 container/input allocation invoked.
