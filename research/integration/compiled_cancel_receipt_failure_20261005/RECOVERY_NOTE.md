# Construction attempt boundary

Attempt 01 was run once after `FREEZE.json` was committed. It stopped before
the target scenario because the synthetic fake client omitted the adapter's
temporary-output `root` path. The callback was queried once, no client command
or GUI/model/Docker activity occurred, and no typed-receipt behavior was
observed. Its exact stdout, stderr, raw result and failed audit are preserved in
`out/attempt-01/`.

Attempt 02 uses a new study ID and a separately frozen harness. The only
construction change is to provide the temporary-output path required by the
adapter fixture. It does not change the PR source, callback schedule, frame,
completion terminal, or expected gate. The failed attempt is not pooled with or
relabeled as attempt 02.
