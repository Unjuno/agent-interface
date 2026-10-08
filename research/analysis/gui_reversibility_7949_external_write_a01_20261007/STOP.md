# A02 execution STOP — wrapper exit was not captured

Allocation `GUI-REVERSIBILITY-7949-EXTERNAL-WRITE-A01-20261007` is stopped.

The candidate runner was invoked once after freeze. Its stdout is a parseable
10-case JSON document, but the zsh wrapper attempted to assign to the reserved,
read-only variable `status` after the process ended. The wrapper therefore did
not persist the candidate process exit code. A zero exit cannot be inferred
from valid-looking stdout, so the protocol's auditor gate was not met.

- Classification: `STOP_WRAPPER_EXIT_UNCAPTURED`
- Candidate invocations: 1 (exit status unverified)
- Auditor invocations: 0
- Retries: 0
- Scientific disposition: none; the candidate JSON is retained as raw output,
  not accepted as a result.
- stdout: `results/candidate.raw.json`, 3703 bytes,
  SHA-256 `6bf69a99710fb1d6f50c528011a41b082b512c9d4968d72465fd88c8254ac28c`
- stderr: `results/candidate.stderr.txt`, 0 bytes,
  SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- wrapper diagnostic: `zsh:4: read-only variable: status`

No candidate or auditor rerun is permitted under this allocation. Any further
test requires a separately frozen successor allocation and must preserve this
record unchanged.
