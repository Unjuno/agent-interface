# B04: replacement after membership admission invalidates the guard

Issue #2122 successor boundary experiment to B03 (PR #7340). Previous outcomes are unchanged.

H: live-page reference equality and the subsequent setter are separate UNO operations; an actual replacement between them can invalidate admission.

T: one WSLc invocation, four fresh documents positive_0, replacement_0, replacement_1, positive_1. A first independent writer moves A/B to x1700/2700. The retained-reference visible guard and live-page equality guard run next. In replacement cases only, a second independent process removes A, inserts a distinct generation1 A with matching visible fields, and restores page order. The controller then uses the already-computed admission to invoke the retained original setter. This deliberately schedules a concrete gap; it does not estimate spontaneous races.

D: first frozen auditor exit1, FAIL_OR_HOLD, exactly two replacement admission errors. Producer/container exit0/errors[]. All four guards passed with one live equality match. Both replacements invoked one setter despite required refusal; observer and saved XML retained replacement generation1 A1700/B2700. Both ordinary controls saved A1900/B2700. Controller timestamps establish guard_completed < late_writer_completed < setter_started for both replacements. Zero-setter refusal remains the required outcome, even though the replacement was not modified by the stale setter.

C: pinned image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d; CPU1, memory512MiB, networknone, user65534:65534; source read-only mount, writable output. No model calls. Root filesystem is not claimed read-only.

U: B03 qualifies membership at enumeration time, not an atomic check-and-effect operation. This actual deterministic interleaving establishes a possible stale admission, not a natural race rate or a particular native cache/pointer branch. No universal identity, authenticated generation, ABA safety, model value or production adoption follows. Further ordinary rechecks still leave a last-check/setter gap; arbitrary delays do not establish exclusion. Strong safety needs an authoritative operation coupling admission and effect, or a contract that explicitly handles the gap.

Evidence: six pre-run frozen sources, literal B03 controller copy, four saved FODG files, initial and late writer outputs, independent observer outputs, original run and audit logs. The unchanged B03 auditor checks saved effects/refusal; source/raw review separately verifies interleaving and equality. Publication FILES.json covers copied members; README, FILES.json and .gitattributes are outside the manifest. Attributes preserve raw bytes. No producer replay or outcome regrade.

First result: https://github.com/Unjuno/agent-interface/issues/2122#issuecomment-5975099851
