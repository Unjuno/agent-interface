# R03: post-effect abort detects a failed late-replacement task

Issue #2122 successor to B04 (#7343). Original outcomes are unchanged.

H: post-effect membership/effect reads may suppress false completion and stop further edits after late replacement, without preventing the stale invocation.

T: one actual WSLc invocation; four fresh documents positive_0, replacement_0, replacement_1, positive_1. Uses actual independent B04 replacement after guard and before retained-reference setter. After that setter, the candidate reads page state and compares retained reference with freshly enumerated page references. It reports EFFECT_OBSERVED_AT_READ only for matching intended effect plus one live reference match; otherwise ABORT_EFFECT_UNCONFIRMED. No recovery setters, Undo, automatic rebinding or retries follow. Fixture titles are not admission/detection inputs.

D: producer/container exit0. Original byte-identical task auditor exit1, FAIL_OR_HOLD, exactly two replacement admission errors. Separately pre-frozen contract auditor exit0, errors[], SUPPORT_POSTEFFECT_ABORT_SCOPED. Both replacements invoke one stale setter, then find zero live matches and effect mismatch, report ABORT and perform zero recovery mutations. Independent observer/saved XML preserve generation1 A1700/B2700. Both ordinary controls find one live match and intended effect, report EFFECT_OBSERVED_AT_READ, and save A1900/B2700. Prevention remains failed and replacement tasks remain incomplete; the contract PASS is not a regrade.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d; CPU1, memory512MiB, networknone, user65534:65534, read-only source mount/writable output. Root filesystem is not claimed read-only. No model calls.

U: this measured post-effect detection can avoid a false completion report. ABORT is not successful recovery or task completion. Observation is valid at its read only; no atomicity, future-writer safety, generic native identity, authenticated generation, natural race rate or model value follows. The original Issue's stronger safety/value requirements remain open. Do not replace prevention requirements with this weaker contract.

Evidence: seven sources frozen before execution, including literal B04 controller and unchanged task auditor. Four saved FODG, independent initial/late writers and observer outputs, raw data and both original audit outputs/exits retained. FILES.json covers copied members; publication README, FILES.json and .gitattributes are outside the manifest. Attributes preserve bytes. Independent review checks raw/source detection decisions separately from saved-state task failure.

First result: https://github.com/Unjuno/agent-interface/issues/2122#issuecomment-5975172045
