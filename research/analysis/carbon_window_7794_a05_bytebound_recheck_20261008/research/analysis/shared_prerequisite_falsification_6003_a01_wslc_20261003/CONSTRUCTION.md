# Construction history — Issue #6003 A01

This log records method-construction checks only. It is not a candidate or audit result.

1. The initial 11-test construction suite passed on the host. Review then found that its incomplete-coverage assertion substituted the expected string in the test instead of calling the selector. That pass was therefore insufficient for the coverage gate.
2. The candidate selector and independently implemented oracle were changed to return `UNRANKABLE` when `coverage_complete` is anything other than `true`. The test now calls both implementations on a copied incomplete-coverage fixture and compares their complete reconstructions.
3. The corrected host construction suite passed 11/11 tests. `python -B` was used to avoid creating bytecode in the source tree. No candidate or auditor formal command has run at this point.
4. The pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` image is present in the WSLc local image inventory. The preflight did not start a container and did not inspect or change unrelated running containers.
5. Pre-execution command review found that the draft auditor mounted its output directory read-only. The command was corrected to mount candidate input at `/input:ro` and a separate writable auditor directory at `/out`. The host capture runner retains subprocess stdout/stderr bytes, timestamps, exit codes, exact argv, source hashes, and result hashes; an occupied role directory refuses a second attempt.
6. A frozen disjoint graph now explicitly tests the source proposal's no-shared-effect control. Its VERIFY decision uses an independent premise, so failing `P_SHARED` can change only CAPTURE. The candidate and oracle both enumerate this graph; an eighth effective corruption control changes its raw outcome incorrectly. Full null outcome tables are also retained. These controls were added before any formal invocation.
7. The selector file was named `candidate.py` to avoid shadowing Python's standard-library `select` module. A source search found and corrected the old hash-key name in the candidate CLI gate before freezing. The final 13-test host construction suite passed, including the disjoint portfolio and separate auditor input/output mounts. Importing the capture runner confirmed its repository path without starting a container.

Any later construction correction must be recorded here before the source freeze. Once the frozen candidate begins, its first outcome is retained and no candidate/auditor retry is permitted by this allocation.
