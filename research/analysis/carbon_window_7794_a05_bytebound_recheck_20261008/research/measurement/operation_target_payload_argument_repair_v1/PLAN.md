# #1212 collision-normalizer harness repair

TASK: OPERATION-TARGET-PAYLOAD-ARGUMENT-COMPLETENESS-REPAIR-20260918-002

Only the collision normalizer/auditor changes relative to #1206. Representation, deterministic rule, #1133 seed/digest and semantic gates remain fixed.

H: target_admissibility + actual payload_ref fully closes the synthetic96-row corpus under the frozen deterministic rule; #1206's four conflicts were opaque argument-name artifacts.

T: alpha-rename target IDs to current candidate slots and normalize non-null payload_ref to PAYLOAD_PRESENT for collision analysis only. Exact proposal membership always uses untouched literal target/payload values. Construction includes ID-only non-collision and true semantic collision controls. Source-first freeze, ownership reread, one primary, reruns0.

D: HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION iff exact96/96, positive48/48, negative48/48, false-exec0, normalized conflicts0, missing args0, audit PASS.
