# Issue #5156 synthetic completion-sentinel terminality result

## Result

The frozen T3 auditor accepted the completion record in both positions:

| Case | Completion position | CLI exit | CLI result |
|---|---:|---:|---|
| Positive control | Final row (25 of 25) | 0 | PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY |
| Treatment | First row (1 of 25) | 0 | PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY |

The independent raw-only audit exited 0 with no errors and reported FINDING_NONTERMINAL_COMPLETION_ACCEPTED. It verified exact source Git blobs and SHA-256 values; the final/first positions; identical completion-row content; equality of every non-completion row in unchanged relative order; identical serialized row multisets; and consistency among both raw hashes, saved audit JSON, stdout, row counts, and exit codes.

The positive control was built from the retained T3 fixture rows, with its single completion row moved to the end to match the actual frozen runner, and with raw_rows set to 25 as the runner does. The treatment moves only that same completion object to row zero. The target CLI ran once per case under Python 3.14.5 on macOS; candidate invocations 2, retries 0. Raw SHA-256 values are af6acf7d18603665899fa153ae7b54c27c74262a0bd8a331da03774cd1e03158 for the control and 28d23cca05313a8e6ae434627c815ad53eca2fc219ccd35b964b2d07caa31bf7 for the treatment.

## H / T / D / C / U

**H:** The T3 auditor may validate the existence and equality of a successful runner-completion sentinel without requiring the sentinel to be the final raw row.

**T:** Against the frozen source, run the synthetic CLI once on a 25-row control ending in an integer-zero completion sentinel and once on the matched treatment with only that sentinel moved to the first row. Use a separate raw-only auditor after both target calls.

**D:** The control must pass. A rejected treatment means the terminality guard is enforced; an accepted treatment means the auditor does not enforce terminality. A malformed baseline, provenance mismatch, or changed non-completion record invalidates the result.

**C:** This is a deterministic synthetic JSONL ordering test of the exact CLI source and fixture lineage. It is separate from the already executed #5895 T6 Boolean/float-zero and mixed-completion experiment; those cases were not rerun.

**U:** The target was invoked only in synthetic-cli mode. The formal mode's trusted host receipt/HMAC path was not invoked. Therefore this result does not show a tampered formal receipt bypass, a formal X11 result, physical key-up, application consumption, MAP01 effect, safety, latency, or product success. No candidate runner, Docker container, X server, GUI/input, game, model/provider, GPU, or network was used.

## Provenance and preserved outcomes

- Frozen main: f474970f82d68b6648aac64f99048ad0c2fd5732.
- Target auditor, fixture, expected-input, and runner Git blob/SHA-256 identities are recorded in FREEZE.json.
- Formal candidate and independent X11 auditor invocations: 0. No consumed allocation was used or retried.
- A shell redirection setup error occurred before the zero-invocation preflight. It and its correction are retained in results/formal-01/SETUP_ATTEMPT_00.md.

The frozen preregistration used broader “evidence-integrity gap” wording than this synthetic result supports. The [scope correction](SCOPE_CORRECTION.md) records that formal host-receipt validation was not tested and no tamper-bypass claim is made.

## Delivery-rebase verification repair

After the delivery branch advanced beyond the frozen source commit, a new regression exposed that both preflight and raw-only audit required `HEAD` to equal the original freeze. That made the verification tools fail on a later delivery commit even when the frozen dependencies were unchanged. The shared provenance check now requires the frozen commit to be an ancestor and verifies each dependency's blob at the frozen commit and current `HEAD`, plus its worktree SHA-256. The original freeze and formal-01 raw/audit outputs remain unchanged.

Two temporary-repository regressions pass: an unchanged descendant delivery commit is accepted, and a descendant that changes one frozen dependency is rejected. These are verifier construction checks; they invoke no candidate CLI and do not rerun the terminality experiment.
