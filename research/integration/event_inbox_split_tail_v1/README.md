# Split UTF-8 tails and passive-reader cursor preservation

Issue #3952; successor to #3876 / merged PR #3883, separate from PR #3917.
Source main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Allocation: `inbox-split-tail-3952-20260922-01`.

This README records the source-freeze stage. Formal outcomes, when available, are
in `REPORT.md`; a source archive alone is not a research PASS.

## Frozen question and design

Does the unchanged reader/CLI preserve its cursor when a separate writer stops
inside a UTF-8 character or JSON Unicode escape? Does completion including LF
return the remaining payload once? Does an exited writer with no LF remain
explicitly incomplete instead of being inferred complete from reader exit 0?

The fixed plan has 22 private streams: nine split points with completion and exit23
(18 cases), plus complete-valid, invalid-UTF-8, duplicate-ID and skipped-ID controls.
Four separate CLI readers per stream give 88 invocations. Pipe barriers put the
first two reads before producer completion/exit and the last two after its observed
exit. Raw snapshots, exact stdout/stderr, cursors, commands, PIDs and exit receipts
are retained. No retries, case replacement, outlier exclusion or post-data tuning.

PASS requires every frozen byte/cursor/payload/exit/no-authority condition and the
independent audit to pass. The auditor does not import the candidate or runner.
Construction used 12 synthetic tests including 10 semantic corruption controls,
and two writer-only lifecycle checks; two construction invocations are retained.
There were zero formal reader calls before this source freeze.

## Complete source capsule

`source.part*.b64` are ordered pieces of one base64-encoded gzip JSON map from
relative filenames to exact UTF-8 source bytes. All 16 files, per-file SHA-256
values, original reader/CLI/ledger snapshots, both construction receipts, exact
plan, H/T/D/C/U, environment and source freeze are retained losslessly.
`SOURCE_MANIFEST.json` binds every part, archive and restored file.
No raw-source omission is hidden behind a digest. Git blob upload IDs were checked
against locally computed IDs; an independent-directory roundtrip matched 16/16.

Restore into a NEW directory for inspection and offline audit:

```sh
python research/integration/event_inbox_split_tail_v1/restore.py --out /tmp/issue3952-audit
cd /tmp/issue3952-audit
python -m unittest -v test_audit
# Once the result artifacts are published:
python audit.py raw.jsonl
```

The restorer never launches writer/reader/model/GUI work and creates CONSUMED to
prevent accidental formal replay. Do not run launch.py on this historical identity.
A new formal experiment requires a separately frozen successor allocation.

## Scope

Provided Linux execution container, CPython 3.13.5; Docker CLI/image identity are
unavailable. This is a controlled fragmentation transport using DeliveryLedger,
not the full interactive_v17 GUI producer or a Docker/OrbStack reproduction.
No shared reader/runtime changes, provider/model calls, GUI/input, ACK/resync,
compaction, automatic replay or experimental network calls. An incomplete read is
not a producer-termination signal. Persisted epochs, crash/power-loss durability,
model consumption, latency/tokens, task quality and production adoption are unknown.
#3876, #57 and the broad ROADMAP remain open.
