# WSL migration auditor repair — static contract checks

## H — Hypothesis

The retained auditor cannot consume its own frozen input shape: the SHA-256 source map and expected test IDs are nested in `FREEZE.json.workload`, while the auditor reads them at the top level. In addition, Python booleans satisfy `isinstance(value, int)`; strict record validation must reject booleans for indices, exit status, timing, RSS, and PSI counters.

## T — Test

Used the immutable FREEZE.json from the retained #6389 pilot and generated synthetic rows matching its schema and expected schedule. Tests exercise the nested-field path and inject Boolean values into all integer-like raw fields. No candidate workload, WSL environment, WSLc container, or Docker Desktop execution was launched.

## D — Data

Host-only verification on CPython 3.12.10. The suite's synthetic passing fixture demonstrates auditor behavior only; it is not a migration experiment, candidate result, memory/performance measurement, or independent formal audit.

## C — Conclusion

Static auditor repair checks pass when the corrected auditor reads the nested freeze contract and rejects Boolean-as-integer records. The retained #6389 experiment remains blocked by its shared-lane ownership state; this package does not change its allocation, STOP, or candidate count (0/0). No migration benefit or Docker-versus-WSL performance claim is made.

## U — Unknowns and next steps

- Obtain explicit release of the #6389 shared execution lane before a fresh, prospectively frozen candidate run.
- Run the exact candidate and independent auditor in the approved native WSL environment; synthetic host tests are not a substitute.
- Resolve whether the documented `wslc.exe` command has an isolation/control combination adequate for a distinct measured allocation.
- Review and integrate this additive audit repair independently of the blocked scientific lane.

