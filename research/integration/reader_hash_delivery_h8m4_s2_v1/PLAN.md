# H8M4 CLI compatibility / retained performance delivery

Issue #4399. No new timing experiment. The original 137 files and original labels remain immutable.

## H / T / D / C / U

H: the exact old intra-call hash candidate composes with the unchanged experimental CLI without changing stdout, exit, cursor, incomplete-tail or refusal behavior. Every invocation revalidates its own source bytes.

T: two isolated package roots differ only in reader.py. Exact upstream test_reader.py (five methods), test_cli.py (one method), CLI and DeliveryLedger are copied without edits. Each root runs those six unit methods once. No monkeypatch or backend stub. Python -S -B for runner and matrix; the inherited CLI unit's own child invocation remains unchanged and can expose an environment failure. Stop if a unit run fails.

Then six scenarios x three sequential calls x two arms = 36 fresh CLI subprocesses, fixed scenario/phase/arm order. Phase0 returns first record using max_records1. Later calls use max_records32 and saved cursors. APPEND appends a second record then checks empty end. REPEAT begins with two records and reads the second twice from the same saved cursor. INCOMPLETE appends a JSON object without LF, refuses consumption, then completes LF. BLOCKED_SEQUENCE appends a duplicate ID, blocks twice at the same prefix. PREFIX_CHANGED rewrites ready to equal-length other after phase0, then refuses twice. TOTAL_CAP appends beyond a cap exactly equal to the first record, then refuses twice. Every arm in a phase sees the exact same files and arguments, except its package cwd.

D: complete36 rows, both six-method original unit runs pass, paired stdout/exit match exactly, independent raw-only expected outputs/cursors match, every source/input/cursor byte remains unchanged by the invoked CLI, observed process exits and integer identities/timestamps retained, no authority or ACK. PASS_READER_CLI_HASH_COMPATIBILITY is engineering evidence only. Complete disagreement is FAIL; source/timeout/process/incomplete evidence is STOP/HOLD. No retry, row replacement, source tuning or timing call is allowed after this retained run starts.

C: the test roots contain exact selected source closures, not a full repository. Temporary paths are deliberately shared across arms at each phase; source roots differ. Known numeric representability defects under #4371 are outside this change, not repaired or certified. Existing unit subprocess startup can fail due local interpreter configuration; retain it as engineering evidence, not a scientific finding.

U: supplied Linux x86_64/CPython3.13.5 standard-library container. Docker/gh unavailable; no image attestation, model/provider, GUI/input, user documents, experiment network, installation or performance benefit from this matrix. Separate auditor is same-author, not independent human review.

## Commands and retention

Run `python -S -B compat.py <absent-output-directory>` exactly once after public source/readback and freeze. Retain actual outer process exit/stdout/stderr alongside RAW.json. Audit separately: `python -S -B audit_compat.py <output>/RAW.json FREEZE.json`. Audit corrections, if any, are separately versioned; original failures remain.

Original local performance evidence is never rerun: restore capsule, verify MANIFEST/FREEZE, run the original verify.py only. Public registration here is retrospective for that evidence. Original dispositions are PASS_LOCAL_INTRACALL_HASH_EQUIVALENCE and PASS_LOCAL_COST_GATE.

Roadmap: original re-audit -> source/new gate publication -> CLI compatibility -> all original and new evidence publication -> exact-byte reconstruction -> PR/checks/scoped review -> qualified evidence-only merge/readback. No shared runtime or root roadmap change. Keep existing #3935/foreign blocked source excluded.
