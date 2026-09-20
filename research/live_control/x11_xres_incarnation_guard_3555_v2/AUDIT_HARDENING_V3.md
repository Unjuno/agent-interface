# Issue #3676 — strict audit successor, rung 1

## H/T/D/C/U

- **H:** A strict event schema, sequence/cardinality checks, cross-field consistency checks, and a functional CLI can reject contradictory traces that the frozen #3675 auditor accepts, without changing the frozen evidence.
- **T:** Apply a separate v3 auditor and mutation suite to #3675's unchanged raw/freeze. Test the original three documented corruptions plus unexpected/duplicate/reordered/missing events, stale bridge-intent contradiction, extra fields, and boolean-as-integer confusion. Exercise the CLI in a subprocess.
- **D:** PASS this rung only if the untouched raw passes with freeze binding, every mutation fails, the CLI succeeds using its documented argument form, and the original raw file remains byte-identical. Container-validation gate is separate and remains STOP unless a real Docker/OrbStack runtime runs this suite.
- **C:** Additive `audit_v3.py` and `test_audit_v3.py`; `audit.py`, `raw.json`, `FREEZE.json`, and the original `audit.json` are unchanged. The v3 contract is deliberately specific to this frozen event format and is not a proof of all possible auditor soundness.
- **U:** This finite suite does not establish general adversarial completeness, container reproducibility, or any broader X11/product guarantee.

## Rung-1 result

Disposition: `PASS_LOCAL_MUTATION_AND_CLI_TESTS / STOP_CONTAINER_VALIDATION`.

- Windows CPython: `python -m unittest -v test_audit_v3.py` — 3 tests passed, covering untouched raw/freeze binding, all three original and seven additional adversarial changes, CLI execution, and byte-preservation.
- `python -m py_compile audit_v3.py test_audit_v3.py` — passed.
- `git diff --check` — passed.
- The frozen #3675 raw canonical Git-content SHA-256 is `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`; freeze SHA-256 is `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`. The v3 test verifies the freeze binding and confirms raw bytes are unchanged.
- Docker Desktop `desktop-linux` has no responding daemon in this environment. No container build or container audit was run; local unit success is not substituted for the required container gate.

The original v2 files and historical outputs remain untouched. Next: run the exact same suite in a network-disabled container after an approved Docker/OrbStack engine is available; only then consider this audit successor ready for merge.
