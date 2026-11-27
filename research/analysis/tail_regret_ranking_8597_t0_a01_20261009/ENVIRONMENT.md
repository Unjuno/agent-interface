# Environment and command receipt

This is a deterministic standard-library Python calculation on the host CPU. No model, GUI, human participant, external service, runtime action, Docker/WSL container, or GPU is needed for this finite enumeration. Container isolation would add no property required by the frozen hypothesis; the source and inputs are local static files and the candidate performs no networking or host interaction beyond reading the fixture and writing its output. The method claims no container-specific behavior.

The exact Python version, OS, architecture, command start/end UTC timestamps, exit codes, raw stdout, and SHA-256 values are recorded in `RUN_RECORD.md` after the frozen one-pass candidate/auditor invocations. No formal retry is permitted.
