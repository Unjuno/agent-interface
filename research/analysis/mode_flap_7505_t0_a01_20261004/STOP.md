# A01 infrastructure STOP

- Allocation: `issue7505-mode-flap-t0-a01-20261004`.
- Candidate process: not started; WSLc failed while resolving the CID-file path before container creation.
- Exact first command arguments and start/end receipts: `formal_a01/candidate.start.json`, `candidate.end.json`, `candidate.exit.txt`, and `candidate.stdout.txt`.
- WSLc output: `'/out/candidate.cid' を開けませんでした: 指定されたパスが見つかりません。` (ERROR_PATH_NOT_FOUND).
- Exit: 1. `formal_a01/raw.json` absent; no scientific candidate output. No auditor invocation was made because there was no raw ledger to audit.
- Disposition: `STOP_INFRASTRUCTURE`; this does not mean the hypothesis passed or failed. This allocation is consumed and will not be retried.
- Corrective distinction for any new allocation: WSLc resolves `--cidfile` as a host path; the next command must omit that option or provide an existing valid host-side parent path. A new allocation must also use a distinct preregistered seed set and hashes.
