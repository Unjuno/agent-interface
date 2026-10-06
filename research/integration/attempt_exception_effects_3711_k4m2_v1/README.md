# #3711 — current-module exception / partial-effect boundary (k4m2)

PASS_CURRENT_MODULE_EXCEPTION_EFFECT_BOUNDARY for ten source-frozen cases. Full source, construction failures, actual raw records and audit/control evidence are retained losslessly. This is a current-module/file-effect test, not a full CLI, GUI, model or product result.

## Main result

RuntimeError before/after the first append produces empty/A with a retained runtime_failed report and unknown effect. KeyboardInterrupt, SystemExit and immediate process exit each produce empty/A with the same request-only unknown_or_incomplete recovery. Normal completion writes AB; preexisting-directory refusal invokes no callback. All twenty separate read-only inspections preserve original bytes, replay_allowed=false and process_state=unknown.

Ten workers plus twenty inspectors are reaped; one collector allocation, no retries/replacements. Original raw audit342 checks/errors0; eight effective copied-evidence mutations rejected; five audit-unit methods pass. The returncode0 of the ordinary-error experimental worker means invoke returned a failure report, not that the public CLI or task succeeded.

## Restore and independently inspect saved data

Run `python -S -B verify.py NEW_OUTPUT_DIRECTORY` from this directory. The verifier checks every fragment/hash, boundedly restores206 regular files, verifies106 frozen source/construction files, reproduces original AUDIT.json and CONTROLS.json byte-for-byte, and runs five audit-unit methods. It never launches worker.py or run.py and does not repeat the ten-case allocation. Python3.13 standard library only; no display/network/model required. The new output directory must not exist.

SOURCE_ARCHIVE.json and RESULTS_ARCHIVE.json bind separate archives. Source commit c8921ba8612998a999e7544c8f4b85d99d33ebc8 and Issue comment6016893819 preceded execution. README_PREFREEZE.md preserves the pre-execution status. REPORT.md is copied exactly from the full result archive; restored PLAN.md contains original H/T/D/C/U, variable/unit table and roadmap. subject.py is the unchanged current retention module, also archived as upstream_attempt.py.

VERIFICATION.json records the actual saved-data recheck. It is same-author separate implementation/process, not external human review or authenticated execution attestation. All source/raw first outcomes, initial expected red tests and the corrected construction control bug remain intact. No main merge or full repository CI is claimed here.

Review before adoption. Preserve the no-replay boundary without changing Exception/BaseException handling just to make reports exist. Source/raw publication, applicable checks, nonauthor review and main integration are separate gates. #3711/#57/#59 and global ROADMAP remain open. PR #8239's missing A01 raw are not replaced or validated by this study.
