# Construction record

The first Windows-host construction suite ran six tests and failed the independent-baseline acceptance check. Diagnosis showed an auditor-only accounting error: the independent reconstructor counted the fixed shortlist size as returned eligible cards instead of counting only `ALLOW` cards. No WSLc candidate or formal auditor had run. The auditor was corrected before the freeze; its bytes are covered by the source hash in `FREEZE.json`.

The final host construction suite passed 6/6. Its independent-auditor test accepts the unmodified candidate output and rejects six temporary corruptions: missing case, altered k, wrong fixture hash, hard-incompatible selection, false global-absence label for a bounded miss, and falsified metadata-work count. These construction checks are not formal results.

The frozen source was then mounted read-only into the pinned CPython 3.12.14 WSLc image (`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`) with networking disabled, pull disabled, and one CPU requested. The same six construction tests passed 6/6 in the container. WSLc warned that the kernel does not support swap-limit capabilities or the cgroup is not mounted; consequently, the requested 512 MiB memory ceiling is not claimed as enforced. No formal candidate or formal auditor invocation had run at this point.
