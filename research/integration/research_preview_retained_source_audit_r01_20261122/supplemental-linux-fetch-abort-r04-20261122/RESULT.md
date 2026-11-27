# Supplemental R04: incomplete Linux object-fetch attempt

Status: NOT_ADJUDICABLE; no build result or artifact was produced.

The retained conditions identify a separate Linux build attempt for candidate `6c50fdce0d857fbf1a7c647bcd6ca9a17f8c05c0`. During preparation, the WSL Git client began a large lazy object transfer (approximately 1.3 GB observed in the session) and the attempt was stopped before the builder ran. The conditions file is the only preserved raw record for this attempt; no exit/stdout/stderr/result receipt exists, so this is not a builder failure or product result.

The later R06 attempt reused already-present local object stores with `GIT_NO_LAZY_FETCH=1` and completed successfully without additional object transfer. No user task, GUI, model, formal allocation, dependency installation, or artifact publication occurred in R04.
