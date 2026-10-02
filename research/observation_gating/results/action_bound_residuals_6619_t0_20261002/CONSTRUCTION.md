# Construction history

The deterministic fixture generator produced 16 input pairs and five independently stored event labels. The five focused host construction tests passed after repair. The first run was 4/5: the hard critical-pixel predicate counted ordinary scroll-through at the designated coordinate as a safety cue. The original pre-fix construction output is retained at `construction/pre_fix_candidate_raw.json`; the failure note and corrected test transcript remain under `construction/`. The cue was corrected to the frozen transition into value 255, and the final 5/5 test transcript is retained.

The post-fix construction candidate exited 0 and produced 16 rows. The host raw-only mutation suite rejected all 5/5 corruptions. These are construction checks only. Formal candidate/auditor invocation counts and outputs are recorded in `RUN.json` and `formal_01/`.

The optional posthoc denominator summary initially had a syntax error; it was corrected before being run against the immutable formal raw and oracle. It does not invoke or modify the candidate or formal auditor. Its full-denominator counts are retained separately in `SUPPLEMENTAL_SUMMARY.json`.
