# Development calibration

The finite post-guard hook is intentionally deterministic: it establishes existence of an observation-to-input race, not its natural frequency.

Representative fresh sessions before source freeze:
- no fault: final guard passed; first input followed within ~4 microseconds; A=`bookkeeperoffice`, B=`bookk`.
- focus fault: final guard passed; B was activated strictly after the guard and before first input; A=`book`, B=`bookkkeeperoffice`.
- text fault: final guard passed; A was changed through UNO to `boox` strictly after the guard and before first input; A=`booxkeeperoffice`, B=`bookk`.

All three ended with empty physical input. This candidate deliberately performs no additional guard after the injected fault. The experiment tests the retained guard boundary rather than proposing another check as a fix.
