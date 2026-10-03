# Singleflight cancellation/completion event-order boundary

See [REPORT.md](REPORT.md) for the executed result and limits,
[PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and the finite contract,
[FREEZE.json](FREEZE.json) for source hashes, and [run01/RUN.json](run01/RUN.json)
for actual invocations and exits. Parent: [Issue #6501](https://github.com/Unjuno/agent-interface/issues/6501).

The exact retained T0b helper is copied for source identity. The new test uses
new finite inputs and calls only its classification helper. No historical
allocation, scheduler, GUI/controller or main runtime is executed or changed.
The result is scoped analytical construction evidence; explicit ordering resolves
the cancellation/delivery ambiguity in this finite model.

Raw is retained through reversible gzip/base64 with a checked SHA256; recovery
and read-only re-audit commands are in the report. Never rerun `run_once.py`
against the consumed allocation/output directory.

## Publication representation v3

Original execution bytes remain unchanged in local evidence. The public log/receipt is a disclosed path derivative. The earlier v2 manifest incorrectly used pre-publication CRLF hashes for the files now listed in PUBLICATION.json. Exact base64 Git blob readback shows committed LF bytes. This metadata repair binds those committed bytes, retains both original and public representation hashes, and gives an exact CRLF reconstruction for every newline-only derivative. For before-tests.txt that reconstruction restores the path-sanitized derivative, not the private original paths. The original and final path-derivative sizes/hashes are separately recorded. Source/harness/raw files, first outcomes, counters, times and exit fields are unchanged from the previous public head; no candidate, probe, formal allocation, test or auditor was rerun. Earlier public commits and erroneous historical manifests remain in Git history; this forward update does not erase them.

The public FREEZE.json is an LF representation of the original CRLF freeze. Use its PUBLICATION.json entry to reconstruct and hash the original frozen byte string; its eight source pins are unchanged and match the committed source bytes. Do not compare the original freeze byte hash with the LF representation as if they were identical. Never replay the consumed run.
