# Primary use: paced text and repeated keys in one public program

Source: `ff3cac885a082eb4956338b1e9c47091a7394cdc`.
Disposition: **WSL functional evidence; formal container adoption gate remains open.**

The primary agent viewed the initial empty Tk entry, then chose one program:
click the entry, type `AB1234` with explicit 20-ms character gaps, press Left
twice using `repeat`, insert `-`, save, capture with a zero final wait, and release.
The expected independent saved value was `AB12-34`.

The action reported completed, verified empty input release, and no required
recovery. Its image showed only `AB123` and `unsaved`. Retained lookup returned
the same image and outcome without changing the raw files. After viewing that
image, the primary agent chose one explicit read-only observation, which showed
`AB12-34` and `saved:AB12-34`. Independent effect readback matched exactly.
There were two observations, one input dispatch, and one retained-result lookup.

This exercises the combined public text-gap and key-repeat compilers through
one persistent SDK stdio MCP connection. It supports their use together in this
owned fixture. It does not establish a useful default delay, redraw detection,
model-token savings, useful-feedback latency, or general application reliability.
No input was replayed. The copied harness always waits for a primary decision
before input and before the additional observation; it is not an autonomous
model loop. Source/binding assertions are caller supplied and the harness mints
a 10-second lease immediately before the chosen dispatch.

This was WSL/Xvfb, not Docker/OrbStack or a host-registered tool. Event logging
used Linux temporary storage. Inter-call time includes primary tool/turn delays
and is not a performance metric. Owner PID 33353 exited 0; tracked fixture PID
33358 exited -15 and Xvfb PID 33354 exited 0. Descendant cleanup was not verified.

`evidence.tar.gz` preserves 36 files plus their manifest: scripts, requests,
receipts, PNGs, primary decisions, application effects/events, and cleanup.
`archive.json` records its size and SHA-256. All manifest entries were checked
against archive bytes. Frozen predecessors remain unchanged. Do not rerun this
record in place; a new attempt needs a fresh allocation and result directory.
