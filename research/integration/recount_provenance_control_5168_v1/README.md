# Independent provenance-binding control for PR #5168

## H / T / D / C / U

**H.** The exact `freeze_inputs.py` from PR #5168 emits a manifest without
stopping when a tracked working-tree input differs from the pinned Git commit;
the emitted SHA-256 then describes the modified bytes while `git_blob` names
the original committed bytes.

**T.** Allocation `recount-provenance-control-5168-20260928-01` uses the exact
candidate source at PR head `d14bc0abfcab3dc8572d4716c73cf3e460c3a5e2`, blob
`a0cd1db94c3c4204f7dfd0e3b88a702f1c1e50b1`. A disposable synthetic Git repo
contains the same 28-path inventory and 14 unique raw `result.json` call IDs
required by the candidate. After committing trusted fixture data, one
`plain/task-details.json` file is mutated only in the worktree. The candidate
freezer runs once against the pre-mutation commit.

**D.** `CONFIRM_DEFECT` requires candidate exit 0 and a manifest entry whose
SHA-256 equals the mutated live bytes while its Git blob equals the pinned
commit's trusted blob, with those bytes demonstrably different. The independent
auditor must re-read both live and Git-object bytes, reproduce the mismatch,
and reject two corrupted audit inputs.

**C.** This is host-only and synthetic. No original historical evidence,
model, GUI, provider, network workload, Docker, or production source is used.
Docker is not needed to reproduce a local Git working-tree/object binding bug;
the shared container lane remains held under #5085.

**U.** This proves only the candidate freezer's behavior under one controlled
working-tree mutation. It does not audit the full recount, fix PR #5168, or
establish any new #57 efficiency result. The active PR's result remains
inadmissible pending its own correction and rerun.

## Frozen source and preflight

The candidate copy SHA-256 is
`93d81f21abe8c047d137da0800ee19069cd16c9f43aa3fbe3e057fdaf3a55a46`; its
Git blob and AST match the exact PR-head source. Current main at freeze is
`43a8f58c126a8d54cb84f2f4fcd2299b9028b380`. Runner, auditor, contract-test
and candidate-source hashes are recorded in `FREEZE.json`. Fixture-free
contract tests check the exact inventory size and candidate source hash before
the one-shot run. An initial test invocation from the repository root failed
to import the package-local `runner`; the tests passed when correctly invoked
from this package directory. An initial PowerShell `py_compile` argument
quoting attempt also failed before compilation; the corrected package-local
compile passed. Both command-invocation failures are retained in
`PREFLIGHT.json`; neither is candidate behavior.

## Allocation 01 result — STOP

The candidate freezer was invoked exactly once. It exited 1, emitted no
manifest, and the runner retained only a SHA-256 of stderr—not the stderr text.
The raw schema therefore says `NOT_REPRODUCED`; the correct allocation
disposition is `STOP_RUNNER_STDERR_NOT_RETAINED`, with **no conclusion** about
the candidate's behavior. This is a harness evidence-retention failure, not a
counterexample to the PR review finding. No candidate retry or fixture change
was made.

A separately frozen STOP-only auditor (not the pass auditor) checks raw
integrity, the live synthetic fixture's 28 committed files/14 unique call IDs,
and that the mutated worktree bytes differ from the pinned Git object. Its
scope deliberately does not claim to know why the candidate exited 1 or to
validate the candidate behavior. The fixture remains in the system temp
directory for inspection. Exact stderr cannot be recovered without rerunning
the candidate, which is disallowed by the one-shot rule.

STOP audit v1 failed because it assumed the pre-mutation Windows working bytes
equal the committed Git blob bytes. Audit v2 also failed due an inverted check
for that line-ending relationship. Both failures are retained unchanged.
`core.autocrlf=true`; STOP audit v3 is separately frozen against the same raw
SHA, validates the appended mutation against the original working bytes, checks
the pinned Git object independently, and reports whether pre-mutation worktree
bytes equaled the committed blob without requiring equality. It still makes no
candidate-behavior claim.
