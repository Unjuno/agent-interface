# Prelaunch stop record

Disposition: `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`. The freeze recorded in `PRELAUNCH_FREEZE.md` was based on `f11ee9d051239094cf3679e19c80bd7deaed0564`. The immediate remote check observed `d22c094a4a2e2292333479573c2eb446c345e1b9`. Candidate=0, auditor=0, retries=0. This is not a scientific result and consumes no candidate/auditor invocation. The frozen bytes and original prelaunch record are preserved in this directory. Any continuation uses a new allocation ID and additive path.

The frozen auditor source is preserved byte-for-byte as `frozen_inputs/audit.frozen.py.gz`; it was not invoked. The readable root `audit.py` has only trailing whitespace removed and is not the frozen source.
