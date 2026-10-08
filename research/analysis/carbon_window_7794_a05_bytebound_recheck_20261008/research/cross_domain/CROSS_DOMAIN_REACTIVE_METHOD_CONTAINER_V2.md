# Cross-domain reactive method container v2

Status: **PASS for one shared local-execution contract across continuous X11 control and an xterm workflow; integration and model efficacy remain unproven.**

Publication base: `57e05035a084e54ea1edd601d910d93ee183dfea`.

Executed source SHA-256: `70ba728cb95d0de7e6323ddba487b2bed0d75061683a10563e13aba686932f54` (16,724 bytes).

Published Git blob SHA-1: `d649d14e4d9f2470e79d377dd73c6abca241bd66`, independently equal to the Git blob hash computed from the executed container bytes.

## Question

Can one domain-neutral local executor carry fresh-observation -> bounded-action -> fresh-observation control across both a continuously changing task and an ordinary desktop-style workflow, while stopping on locally observable invalidation and releasing input?

This experiment deliberately does not optimize a DOOM map. It tests the mechanism that would sit below either a DOOM planner or a desktop-computer planner.

## Shared mechanism

Both domains use the same `GenericExecutor` and `Contract` types. A contract contains only:

- an expiry;
- a transition budget;
- terminal labels;
- invalid labels;
- a mapping from observed labels to bounded universal-input actions.

The executor itself does not contain tracker-specific or terminal-specific policy. It repeatedly obtains a local observation label, either terminates/fails closed or executes the matching bounded input, then observes again. `finally` always calls the common release path.

Only the observation adapter and declarative rules differ by domain.

## Container domains

### Continuous-control fixture

A Tk/X11 task renders a red marker with exogenous drift. The controller can see only X11 pixels and uses actual XTest Left/Right key events. The independent app process retains exact marker state and key events.

Positive case:

- start far right of the target band;
- fresh pixel observations repeatedly change the next action;
- completion requires three consecutive local target-band observations.

Invalidation case:

- the marker disappears during control;
- the adapter returns `MISSING`;
- the executor stops without further useful-control attempts and releases input.

### Desktop/TUI fixture

A real `xterm` hosts a small stateful TUI. The controller sees screen pixels only. Background-color state is used as the local visual signal; XTest provides pointer/keyboard input.

Positive case:

- red -> enter token;
- fresh blue observation -> enter confirmation;
- green -> complete;
- the app independently writes one exact terminal score row.

Changed-state case:

- after the token, the app changes to yellow rather than exposing confirmation;
- the executor invalidates on the fresh visual state;
- independent score rows remain zero.

The scorer path is not given to the controller process. This is evaluation isolation within one container namespace, not a security proof.

## Retained harness failure and repair

The first clean runner used `max_transitions=18` for the tracker. It passed 2/3 complete blocks; one positive tracker run reached `BUDGET` before completion. That v1 failure is retained rather than discarded.

V2 changed only the tracker transition cap from 18 to 24. The expiry (2.2 s), actions, visual predicates and task dynamics were unchanged.

## V2 result

Five complete V2 blocks were executed before publication.

- block PASS: **5/5**;
- tracker positive: **5/5 `COMPLETED`**;
- tracker missing-target case: **5/5 `INVALIDATED`**;
- tracker app-side key press/release balance: **5/5 positive and 5/5 invalidation**;
- xterm positive: **5/5 `COMPLETED`**, exactly one independent success row each;
- xterm changed-state case: **5/5 `INVALIDATED`**, zero independent score rows each.

Tracker positive required 14--15 actual input actions and 15--16 local observe/action transitions. Xterm positive required two actual actions and three local transitions. Thus the evidence is not a one-action wrapper: fresh local evidence changes later authorized input without another planner boundary in both domains.

Machine-readable retained summary: `results/cross-domain-reactive-method-container-v2.json`.

## Environment

- Linux 6.18.44 x86_64;
- AMD EPYC 9V74, 5 CPUs exposed;
- CPython 3.13.5;
- Xvfb 800x600x24 + openbox;
- XTerm 398;
- one controller subprocess per case.

Chromium was considered for the desktop arm, but the installed managed browser blocks localhost, `file:` and `data:` navigation. That environment policy was treated as a harness constraint rather than bypassed. The retained desktop arm therefore uses the installed real xterm transport.

## H / T / D / C / U

### H — falsifiable hypothesis

One bounded, predicate-driven local execution contract can support both continuous and desktop-style observe/action loops, including a fresh-state invalidation, without embedding the domain policy in the executor itself.

### T — minimum test

Run complete positive and changed-state cases in both domains. Require at least two actions in each positive path, exact independent desktop scoring, balanced tracker key release and no score after desktop invalidation. Repeat the repaired V2 block five times.

### D — disposition

**PASS for cross-domain construction mechanics.**

This means only that the same executor/contract shape survived the two substantially different X11 fixtures and their invalidation paths. It is not promotion into the shared runtime yet.

### C — competing explanations / failure modes

- Both adapters are development-authored; automatic semantic predicate authorship is not tested.
- The tracker is simpler than MAP01 combat/navigation.
- The xterm TUI is simpler than Chromium, Calc, Inkscape or a general unknown application.
- Xvfb timing does not prove WSLg/Wayland/Windows/macOS timing.
- A stronger planner can still choose a bad contract even if local execution is mechanically correct.

### U — uncertainty

The dominant uncertainty is now composition: can the existing MAP01 visual/typed signals and the existing desktop target/effect predicates be compiled into this same small continuation contract without granting hidden authority or adding domain-specific executor branches? Model-authored predicate quality is also unmeasured.

## Architecture implication

The common path should be:

`planner -> bounded reactive contract -> local observe/action loop -> independent task verification`

rather than separate high-level runtimes for games and desktop GUI work.

A frontier model such as Astra or Luna should spend model boundaries on semantic decisions and contract updates; it should not be required to resume for every 50--100 ms local correction or every already-described desktop substep. The mechanism remains model-neutral.

## Next gate

Do not tune this fixture further. Use the same contract vocabulary in two existing repository paths:

1. **MAP01 transfer:** map current typed/visual state into local continuation/termination labels and allow bounded motion/fire only under explicit source-bound rules. Keep the independent MAP scorer outside controller visibility. A later full-map attempt remains separately labelled and must retain death/timeout/failure.
2. **Desktop transfer:** wrap one existing independently scored persistent desktop workflow (prefer the golden Chromium/Calc path) using the same executor contract, requiring at least two fresh local transitions and a changed-state safe stop.

Only mechanisms that pass both transfers should move toward the product runtime. A DOOM-only trick does not qualify, and a desktop-only macro does not qualify.

## Claim boundary

This construction does **not** establish MAP01 clear, frontier-model efficacy, general desktop reliability, human-level reaction time or production readiness.
