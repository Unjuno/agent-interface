# MAP01 autonomous key-release construction package

This package captures ordered, monotonic call brackets for owner-issued key
release requests and one shared transport synchronization. It is synthetic,
host-only construction evidence. It does not establish server receipt, physical
key-up, application observation, or the end-to-end MAP01 contract.

Run from this directory with Python 3.11:

```powershell
py -3.11 test_release_envelope.py -v
py -3.11 source_audit.py ..\input_owner_v10.py ..\input_transition_owner_v3.py
py -3.11 build_raw.py raw.jsonl
py -3.11 audit.py raw.jsonl
```

An exception yields no success receipt. In particular, a failed request or
shared sync is not converted into a successful batch. The auditor rejects
missing provenance, invalid ordering, and claims of input authority or physical
key-up. Empty ownership still executes one shared sync and emits no fabricated
key edge.

No X11, GUI, container, model, GPU, or real input was used. Formal X11 remains
unspent; see Issue #5156 and the allocation preregistration for the frozen
source IDs, decision rule, and stop boundary.
