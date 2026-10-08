# F01 real OS pipe successor boundary — #59

H: exact E02 candidate preserves typed JSONDecodeError notification on actual
subprocess stdout pipe, not only E05 injected text iterator.
T: four fresh sequential children, original malformed/candidate malformed/
candidate valid-ready/candidate close-stdout-while-alive, once/no retry/model0.
D: literal wire, sourceSHA, positive clocks, exception/cause/unhandledthread,
ready/events, reader+child liveness, termination cleanup, runtime receipt.
C: historical E02 original/candidate immutable; fixed E05 sourcearchive/image;
timeout.35s; private own Docker netnone/CPU1/1GiB/swap0/pids128/UID501.
U: no useful task feedback, fullcontroller, GUI/native input, gameplay,
productiontimeout/default/adoption or causal latency inference. EOFalive is
diagnostic, not presumed fixed. All first rows retained even if H contradicted.

Expected malformedoriginal TimeoutError/unhandledJSONDecodeError/deadreader,
candidate _SessionReaderFailure/causeJSONDecodeError/deadreader/no unhandled,
healthy ready/deadreader/childalive after stdoutclose, EOFalive timeout/deadreader.
Each child's exact pipe bytes are emitted with flush then os.close(1); child
remains alive3s so this does not substitute processdeath for pipe EOF.
Harness terminates its own child after measurement, records actual exit.
Fresh output required; outer container error is first STOP, never replay.
This is a new four-cell pipe-boundary experiment, not E05 native allocation.
