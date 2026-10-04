# Post-run stdout / checksum recovery receipt

This receipt documents a run-record omission; it is not a new experiment or a claim that the initial capture was written contemporaneously.

- The single generator invocation returned this stdout in the execution tool result: `{"eligible": 2, "final_cue": "upload-result", "intentions": 7, "matching_cues": 7}`.
- The first post-run verification command (`python3 -m py_compile ... && sha256sum ... GENERATOR_STDOUT.txt && cat AUDIT.json`) exited nonzero because `GENERATOR_STDOUT.txt` had not been saved. It printed source/input/candidate/audit hashes through `AUDIT.json`, then reported `sha256sum: GENERATOR_STDOUT.txt: No such file or directory`; the trailing `cat AUDIT.json` was not executed because the command used `&&`.
- The stdout above was then restored from that captured tool result (without rerunning `generate.py`) into `GENERATOR_STDOUT.txt`.
- A subsequent `sha256sum -c SHA256SUMS` returned `OK` for each of: README.md, RUN.md, REPORT.md, generate.py, candidate.py, audit.py, INPUT.json, CANDIDATE.json, AUDIT.json, GENERATOR_STDOUT.txt, CANDIDATE_STDOUT.txt, and AUDIT_STDOUT.txt.
- These bytes prove the saved files match the saved manifest, not that the run was eligible under the already-existing #7162 protocol. The protocol mismatch is why this package is withdrawn.
