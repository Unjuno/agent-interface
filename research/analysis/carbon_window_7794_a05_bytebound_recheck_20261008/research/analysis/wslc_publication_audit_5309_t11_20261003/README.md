# T11 — publication-byte audit follow-up

T11 is a separately versioned, offline follow-up to T10's auditor failure. It keeps T10's recorded STOP unchanged and reuses the same frozen T7 source/remote-blob snapshot. Its only auditor change retains each file's classification on the manifest row before the manifest-consistency phase reads it.

The nine-test construction suite passed after that change. The formal CLI audit is still pending the one-time preregistered invocation; no Docker or WSLc workload is involved. This checks only the 11 published artifact byte sequences and the six checksummed source-manifest claims. It does not rerun T7 or explain which publication mechanism appended any bytes.

See [FREEZE.md](FREEZE.md) for the hypothesis, test, data, control, uncertainty, frozen hashes, and one-shot decision rule.
