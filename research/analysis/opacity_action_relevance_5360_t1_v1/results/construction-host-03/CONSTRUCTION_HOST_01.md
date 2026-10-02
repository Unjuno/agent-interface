# Construction host run 01

Status: `PASS_T1_SCOPED` for deterministic host construction only. This is not
the formally gated OrbStack/container execution and does not establish behavior
of a production transaction manager.

- Intake main initially observed: `0cf275c05cc4870d17936bfcff0e8b98539c7cf2`.
- Current main immediately before GitHub publication: `4a1e56eb63501fe02c8438f22ebf95cd46130ca2`.
- Host: macOS 26.6.2 arm64; CPython 3.14.5; standard library only.
- Runner invocation: exactly 1, `simulate.py --output .../raw.json`.
- Independent auditor invocation: exactly 1, `audit.py .../raw.json --output .../audit.json`.
- Syntax check: `python3 -m py_compile simulate.py audit.py`, passed.
- Matrix: 32 rows; final-state comparator admitted 4 invalid action-read cases;
  opacity policy admitted 0 invalid action-read cases and preserved 3 valid
  same-generation action reads. Display-only rows caused no action.
- Auditor: `PASS_T1_SCOPED`, zero errors. Its oracle is separately implemented
  and it imports no runner module. It also exercises abort-status, action-role,
  and generation corruption controls.
- Formal container invocation count: 0. No Docker/OrbStack CLI calls are
  permitted until the exact named CPU allocation is assigned in #5085.
- The prior `construction-host-01` and `construction-host-02` outputs remain
  immutable failed auditor attempts. Host-03 is the passed, frozen output.

## SHA-256

| Artifact | SHA-256 |
|---|---|
| `PLAN.md` | `319868f04def8f5499cb8cc73333af4fc40766323efe657dae92043bd3e9aae7` |
| `simulate.py` | `7f7cbc4564345c8f1721d51e9e229d2d3a71d0229d6f1116882532d6209963ea` |
| `audit.py` | `c9de5b66c2882c381b0aa0deb98a2d3b0a8b87196f18168a6828ba791accca5b` |
| `raw.json` | `76af071d682818315d469edf808d45745b4225db758ac889ca18f8e8da225908` |
| `audit.json` | `6d3fbef7ef4b08a66c6ec97269cc12e53d3f5ad43635849c3a6110178968e452` |

The repository checkout available for local work is 11,301 commits behind its
`origin/main` tracking ref at the time of inspection. Therefore these results do
not include repository CI. GitHub branch/PR checks must be run against current
main independently.
