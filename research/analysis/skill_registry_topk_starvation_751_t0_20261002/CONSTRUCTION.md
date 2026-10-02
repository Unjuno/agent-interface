# Construction record

The first Windows-host construction suite ran six tests and failed the independent-baseline acceptance check. Diagnosis showed an auditor-only accounting error: the independent reconstructor counted the fixed shortlist size as returned eligible cards instead of counting only `ALLOW` cards. No WSLc candidate or formal auditor had run. The auditor was corrected before the freeze; its bytes are covered by the source hash in `FREEZE.json`.

The final host construction suite passed 6/6. Its independent-auditor test accepts the unmodified candidate output and rejects six temporary corruptions: missing case, altered k, wrong fixture hash, hard-incompatible selection, false global-absence label for a bounded miss, and falsified metadata-work count. These construction checks are not formal results.


