# Error-carry compilation of bounded directional intents — T0 successor

Issue #6081 proposes distributing one fixed desired displacement across finite legal input slots. This package tested that idea with exact rational arithmetic in OrbStack. It did not dispatch live input.

## H / T / D / C / U

**H.** For a stationary constant-displacement alphabet and rational per-slot intent, cumulative error may reduce worst-prefix squared displacement error relative to Euclidean-nearest action repeated for the horizon, without increasing prefix-envelope violations or switch/release failures.

**T.** Ten frozen cases × two explicit alphabets (4-way and 8-way) × four arms (horizon-wide nearest, independent per-slot nearest, error carry, release) = 80 rows. We retained each prefix's exact error and position, terminal error, envelope status, switches, refusal and release. The raw-only S5 auditor independently reconstructed all 80 rows; a separate S6 gate audit assessed the preregistered method criterion; S7 checked exact/zero/refusal controls.

**D.** `PASS_METHOD_SCOPED` for this fixture. S6: A/B were identical in all 20 action-set/case cells; error carry lowered worst-prefix squared error on all 9 eligible safe, nonrepresentable cells; carry unsafe cases 0, nearest-baseline unsafe cases 2; no increased safety violations, switch failures, release failures, or refusal failures. S7 passed all 21 exact/zero/refusal checks. The first two audit decision attempts include defects and remain preserved: S4 auditor STOPped on refusal-schema `KeyError`; S5 reconstructed raw exactly but over-applied its unsafe-baseline gate and emitted `FAIL_METHOD_OR_SAFETY_GATE`. S6 and S7 are separately frozen successors; no candidate replay occurred.

**C.** Fixture-defined rational geometry; diagonal vectors are stipulated, not inferred. OrbStack `python:3.12-alpine`, Linux ARM64 image ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; network disabled; source/rootfs read-only; CPU/memory/PID limited.

**U.** No real actuator calibration, input timing, collision, acceleration, focus, OS release semantics, GUI/game, model, task effect, human tempo, live control, or MAP01 evidence. Prefix bounds are synthetic only. This result cannot authorize runtime use.

## What the experiment teaches

Under this stationary model, “nearest action held across the horizon” and “nearest action independently selected each constant-intent slot” collapse to one comparator. They are not independent baselines. C improved on that shared comparator in each admitted nonrepresentable case. In two near-axis cases the baseline breached the synthetic box while C stayed inside; this is reduced synthetic violation count, not a real-world safety proof.

The raw candidate SHA-256 is `81e8e0f9d34de42272744a3793162fe0cb857c77b8e67f28108f28dfc4bc8e49`. S6 decision SHA-256 is `bb6442cc7a3ec7d2297be3c33dd27ab105f62c54a4d0c6d7471fc50853bccfa5`; S7 fixed-control SHA-256 is `09ac66af62457a232bbcd4555f6ed05a8276cea397c04f4531fb39b4c310d98b`. Full freezes, code, raw, receipts and audit chronology are in this directory; see [README](README.md) and [SHA256SUMS.txt](SHA256SUMS.txt).
