# Rescue of #6914 browser/SQLite endpoint evidence

Exact original head `b010462c13df0b333544d110182bfc84a777f2fc`, PR #6914,
Issue #5442. Preserve all 61 original files, source mapping, original compile
failure and actor setup error, all SQLite backups, UI trace and audit receipts.
No original outcome, source, private path, frozen allocation or worker artifact
is changed. Source files remain archival `.txt` in the packet.

`python -B runtime/results/browser_sqlite_rescue_6914/test_archive.py -v`
checks the complete 60-entry manifest and all twelve source-freeze identities;
materializes exact original source names only in a fresh temporary directory;
runs the independent auditor against copied retained SQL/raw/trace with a new
exclusive receipt. All receipt content except fresh start/end UTC must exactly
equal the historical receipt: fourteen joins and ten original directed copied
row mutations. Only those two time fields are excluded, not any result/hash.
The auditor uses read-only SQLite connections and imports no app/observer/actor.
Two additional copied-data experiments corrupt SQL state and UI nonce separately
and require the full CLI to refuse each with its nominated reason and no receipt.

The historical first eight accepted form submissions had two CONFIRMED and six
UNKNOWN effects. Six separately declared fresh-version repairs were CONFIRMED;
the six original effects remain UNKNOWN. Owned application/database evidence
does not establish arbitrary-app fidelity, observer authenticity, concurrency,
power-loss durability, physical input/release, latency or promoted authority.

This is local retained-data review, not browser/server/primary replay or a new
container/live allocation. No source producer, network service, GUI, model,
backend input, shared VM or another worker's resource is invoked. Full source
history is retained separately before retirement; dependent evidence branch
`evidence/6914-diff-01a0ff58-20261003` is not removed by this rescue.
