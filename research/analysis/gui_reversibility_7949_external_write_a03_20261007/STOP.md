# A03 execution STOP — candidate invoked twice

This allocation is stopped for protocol deviation. The frozen protocol allowed
one candidate invocation and one auditor invocation. An initial candidate call
completed with tool-reported exit code 0 and emitted stdout in the tool result.
A second candidate call was then mistakenly made to redirect stdout/stderr to
files. This is a duplicate invocation, not an allowed retry.

- Classification: `STOP_DUPLICATE_CANDIDATE_INVOCATION`
- Candidate invocations: 2 (both tool calls reported exit code 0)
- Auditor invocations: 0
- Retries/replacements: 1 unintended duplicate; no further execution permitted
- Scientific disposition: none. Neither output is accepted as a formal result.
- Second-call stdout: `results/candidate.raw.json` (retained only as raw evidence)
- Second-call stderr: `results/candidate.stderr.txt`
- Second-call stdout: 4311 bytes, SHA-256
  `abcf391ce22ba973a0fe9abb19d15c8a03fbc606893afbf03f8a3b760d7f7e18`
- Second-call stderr: 0 bytes, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- First-call stdout is retained in the execution tool record; it was not written
  to a local result file.

The hypothesis, frozen source/input and both invocation records are preserved.
No attempt will be made to repair this allocation. Any later successor requires
a new allocation ID and pre-registration.
