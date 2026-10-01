# Issue #5156 — invocation-boundary audit successor T1

## H / T / D / C / U

- **H:** The T0 raw-only audit's positive-row mutation control was a no-op, allowing a false 5/6 control result. A corrected audit can demonstrate an actual mutation, reject all six controls, and reconstruct the retained eight-row raw artifact without altering it.
- **T:** Test-driven audit-only successor. One unit test was first run RED against the inherited audit, then passed after the explicit mutation payload was added. The formal audit command ran exactly once. Candidate runner, Docker, X11, GUI, model, and allocation-specific runner invocations: zero; retries: zero.
- **D:** `PASS_INVOCATION_BOUNDARY_AUDIT` iff raw reconstruction matches, errors are empty, all 6/6 controls reject, the mutation payload records both `changed_from_pristine=true` and `rejected_by_reconstruction=true`, and the historical collision remains STOP with null count. **Result: PASS_INVOCATION_BOUNDARY_AUDIT**, exit 0, 8 cases, 6/6 controls, errors empty. Historical collision remains `STOP_INVOCATION_PROVENANCE_OR_BOUNDARY`.
- **C:** Windows host, CPython 3.12.10, Python stdlib only. Input is byte-identical to the T0 fixture. Raw JSONL is byte-identical to the T0 raw artifact (SHA-256 `d3fb121b95d95fa61ea771a7dd0c20a8e255ea83b72752a3ebe371b27762d4b2`). Current main at freeze: `e94101a1bd2ad6e3e103088aa4d169c2ad112086`.
- **U:** This repairs and validates the finite audit mutation control only. It does not rerun or upgrade T0's underlying experiment, establish the number of T0 container attempts, measure ordinary key-up timestamps or physical input occupancy, satisfy the #5156 live bracket, or make an Issue #59 threat-response claim. The predecessor STOP is preserved unchanged.

## Files and result

- `audit.py` SHA-256: `82ff000fdb15dcd1e003be317e873d96219656342b08e188c2b1e106186a6a4c`
- `inputs.json` SHA-256: `2cb27561a3ffe75701a846a68c76d4703fa2027028a9d22d504986db26a01869`
- `results/raw.jsonl` SHA-256: `d3fb121b95d95fa61ea771a7dd0c20a8e255ea83b72752a3ebe371b27762d4b2`
- `results/AUDIT.json` SHA-256: `2875bd8d6f0dc644a7abbd7573a306ed8a696f802c6d38deb8cf4b9eed65e664`
- `test_audit_mutation.py` SHA-256: `43440acedf7bb41f58754db2ab228aa072dde0b33a6f64e347b957e27fd4cbf7`

Formal command (one invocation):

```powershell
python -B audit.py inputs.json results/raw.jsonl results/AUDIT.json
```

