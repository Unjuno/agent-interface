# A02 construction record

The source is a byte-preserving copy of A01's fixture, presenter, auditor and six synthetic source records, with a new seed and an explicit isolated-import path fix in `candidate.py`. A02 construction includes an isolated subprocess import check so the specific A01 failure boundary is exercised without invoking the candidate or creating formal outputs.

The A02 suite is run before preregistration. Construction tests do not invoke `candidate.py` or `audit.py`; the formal commands remain one-shot and are invoked only after the Issue preregistration comment and immediate prelaunch checks.
