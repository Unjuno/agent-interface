# Follow-up 01 execution disposition

- Allocation: `MAP01-CONTROLLER-FINISH-PIPE-FOLLOWUP-01-20261005`.
- Invocation: exactly one, as preregistered; no retry.
- Observed output: `run-01/argv.json` only. No container result, stdout/stderr capture, exit status, or probe outcome was produced.
- Infrastructure: the owned WSLc invocation remained unresponsive before container execution and was stopped. This is a HOLD, not a probe failure or pass.
- Interpretation: the text-mode correction was not measured. The historical `baseline-run-02` PASS is invalid for the synchronous-write hypothesis because its finish send raised `TypeError` immediately under binary-mode stdin.

No frozen input or preregistration was changed. The attempt is retained in place, and no claim is made about whether the pinned helper blocks on a full text-mode pipe.
