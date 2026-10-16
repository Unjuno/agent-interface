# Issue #5156 successor — logical-key audit integrity

## H — hypothesis
The completeness-v2 raw auditor used by #5467 does not bind the `key` field to the frozen expected-release inventory. Adding `key` to the audited identity and restricting it to a non-empty string or JSON null will preserve the valid explicit/cleanup fixture while detecting changed, missing, or malformed logical-key values.

## T — frozen construction
- Base: exact main commit recorded in `FREEZE.json`.
- Inputs: immutable expected inventory and raw fixture copied byte-for-byte from PR #5467; baseline auditor is the exact pinned #5415/#5467 blob.
- Candidate: additive v3 copy; predecessor sources, raw, reports and PRs remain unchanged.
- Cases: pristine explicit/cleanup rows; modified explicit key; modified cleanup key; missing key on each type; null cleanup acceptance; malformed key type rejection.
- Environment: host Python only. The #5085 shared-container slot is unassigned; no Docker/OrbStack invocation is authorized or claimed for this source-only audit test.

## D — gates
Scoped pass requires the frozen test suite to pass all seven unit cases and a separate raw-only invocation to accept the pristine three-row fixture with zero errors. The baseline controls must reproduce its false acceptance for explicit-key, cleanup-key and omitted-key mutations; v3 must reject them. No physical-key or live completeness claim follows.

## C / U
The source-shaped fixture is synthetic and contains three records. This tests the auditor's contract only, not InputOwner emissions, complete live inventory, X11, physical key-up, MAP01 control, useful task effect, or recovery efficacy. Any later live run still requires fresh current-main pins and an explicit exact resource allocation.

## Prefreeze note
An exploratory in-memory probe preceded this freeze. It ran nine assertions against the pinned baseline and candidate and all passed. It is retained as exploratory only; the frozen package tests and separate audit are the confirmatory construction checks, with no runtime/GUI allocation consumed.
