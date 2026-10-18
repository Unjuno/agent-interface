# A13 results — FAIL_METHOD; schema diagnostic passed

The frozen candidate completed 390/390 calls (360 queries and 30 consolidations), exit 0, no retries. Every request retained the frozen model identity and the raw auditor confirmed the exact JSON Schema was attached to every consolidation request. The frozen raw-only auditor returned `FAIL_METHOD` with 6 transition violations, all at the final `batch_2` state: each of the three seeds lacked the required conflict claim, generating a coverage and conflict mismatch (2 errors per seed).

The preregistered schema-compliance diagnostic passed: all 126 claims emitted across consolidation rows used one of the five allowed `kind` values; 0 invalid enum values. The A12 exception-kind failure did not recur under this allocation's structured-output setting. This is scoped evidence that the enum constraint works for the tested local setup; it does not establish all semantic mappings or transitions.

Answer accuracy by seed was episodic-only 0.2667/0.2667/0.3000, per-episode 0.5333, batch-2 0.6000, and terminal 0.6667. Four consistent contrasts met the numeric threshold. They remain descriptive only because the transition auditor failed; no schedule endpoint is interpreted.

## Preserved artifacts

- Raw: `results/FORMAL_T1_A13/RAW.jsonl`, 2,004,071 bytes, SHA-256 `502b28d5405ed3b1d40bba8f41be6c6245ebd68ed4edf83fa300efa88555979c`.
- Audit: `results/FORMAL_T1_A13/AUDIT.json`, 4,925 bytes, SHA-256 `8230ebef9a1a945fbc8d261e8a10f655c2d9aa4995f8cfc59f47ba0cec6f654b`.
- Preflight: `results/FORMAL_T1_A13/PREFLIGHT.json`, 1,345 bytes, SHA-256 `56796d7077573ea2482f0f5d6fc195cab8d8f92032b5c75f72b5ec1eb2184369`.
- Candidate and auditor stdout/stderr are saved beside them; both stderr files are empty.

The frozen source, prompt, input, schema, seeds, model and auditor remain unchanged. This allocation will not be rerun or repaired. Any successor requires a fresh allocation and fresh seeds.
