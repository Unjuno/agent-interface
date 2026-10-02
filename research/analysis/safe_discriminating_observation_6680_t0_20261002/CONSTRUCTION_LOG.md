# Construction log — Issue #6680 T0

Base main at construction start: `9a573b00dc595e64d09387e567c85e10b61a46c1`. This log does not change the preregistered H/T/D/C/U or formal decision gates.

## Collision and ownership audit

- #5430 has a posted candidate×safe-probe matrix test, nonseparability/forbidden-probe controls, and a safe-probe selection refinement. #1874 has a completed finite-horizon minimax selector. #6147 has a separate terminal candidate STOP for safe distinguishing sequences; its raw is unverified. #6061/#6096 test identity/currentness and residual-history identifiability, respectively. Inspected main artifacts contain no four-policy comparison of fixed reobserve, fixed reset, immediate YIELD, and one-step diagnosis on the same residual/fault worlds. Keep this package limited to that outcome comparison and do not advertise a novel generic probe selector.
- GitHub inventory showed no branch or PR for #6680 and no assignees/comments on #6680 at audit time. Related issues #5430, #6061, #6096, #6147, #6195, and #6604 are open; #1874 is closed with its minimax result retained. No existing result was edited.
- The Docker inventory exposed two pre-existing running containers: `unjuno-native-ci-6092` and `cans-of14-n64-dt0.0005`. The OrbStack inventory exposed five running machines: `agent-interface-6576-tailid-parity-a03-20261002`, `agent-interface-6604-t0-isolated-20261002`, `effect-terminal-feedback-6301-t0-orbstack-20261002`, `obs-audit-t1-5681-20261001`, and `research-path-width-6581-t0b-20261002`. These inventories were read-only; no foreign container or machine was inspected internally, stopped, modified, or reused. This allocation has no exclusive runtime grant. `wslc.exe` is unavailable on this macOS host. Formal execution has not started.

## Local construction checks (not formal experiment)

1. Initial construction suite: `python3 -m unittest -v test_construction.py` — **FAIL**, 3 tests passed / 1 failed. The auditor incorrectly classified safe `yield` on a non-identifiable/unsupported trace as a forbidden transition and compared the wrong transition field. No formal process or container ran. Retained here as a pre-freeze construction defect.
2. Corrected construction suite: same command — **PASS, 4/4**. Controls: positive/negative matrix, response-label swap, oracle corruption, and ineligible probe fail-closed.
3. CLI smoke: `python3 candidate.py /tmp/6680-construct.raw.json` — exit 0, 20 rows; `python3 auditor.py /tmp/6680-construct.raw.json` — exit 0, `PASS_METHOD_SCOPED`, 20 rows, `errors=[]`. This was an unisolated host construction smoke, not formal evidence. The temporary output is not an accepted result.
4. A later `exec_command` attempt relying on its `workdir` field ran unittest discovery outside the new worktree and failed with `ModuleNotFoundError: No module named 'test_construction'`. No candidate/auditor code ran. Corrected command using an explicit absolute test-discovery path passed 4/4; this runner setup failure is not a scientific result.

Construction activity to date: host unit suite ran initially and twice after corrections/runner adjustment (the first suite failed on the auditor defect; both subsequent suites passed 4/4); standalone host candidate and auditor CLI smoke commands each ran once. Temporary smoke raw is not promoted. **Formal candidate=0, independent formal auditor=0, container=0, retries=0.** No result is claimed from construction checks.
