# #5890 allocation-01 preparation and STOP archive

Disposition remains **STOP_MAIN_ADVANCED_AND_STORAGE_ZERO**, with historically reported candidate/auditor invocations **0/0** and raw rows **0**. This archive preserves three committed preparation files and the contemporaneous issue-recorded STOP. It establishes no scientific PASS or FAIL and authorizes no retry.

The exact source is branch `research/portfolio-multiplicity-5890-t0-20261001-r1`, head `f7061ed0c2a281de73d0d5fa8f3aefb58ac0d1b5`, based on `5865c5e74842b5bba6a6291e141afae75ca4a147`. The allocation is `PORTFOLIO-MULTIPLICITY-5890-T0-20261001-01`, seed `58901001`. PLAN.md, runner.ps1 and audit.ps1 are retained byte-for-byte under `original/research/analysis/portfolio_multiplicity_5890_t0_v1/`.

## Why the source was stopped

The [registration](https://github.com/Unjuno/agent-interface/issues/5890#issuecomment-5927439711) proposed a one-shot PowerShell method test. The [terminal start-gate record](https://github.com/Unjuno/agent-interface/issues/5890#issuecomment-5927478583) states that main advanced from the frozen base to `f7dedb76d122fe00687aa80206020c8c7b306650` and C: had zero free bytes. No candidate or auditor was invoked. A [later read-only recheck](https://github.com/Unjuno/agent-interface/issues/5890#issuecomment-5927496560) observed main advancing again and explicitly preserved allocation-01 unchanged.

[ISSUE_COMMENTS.json](ISSUE_COMMENTS.json) snapshots the exact four original comment bodies with URLs, authors, timestamps, UTF-8 byte lengths and SHA256. These public statements are provenance, not independent process receipts. The original branch has no STOP file, raw output, process receipt or audit output. None is synthesized here. An archival summary is kept separate from the original source bytes.

## Separate successor

[PR #5945](https://github.com/Unjuno/agent-interface/pull/5945), merged as `e1ebee404930401665c1fef64022b0ad3c373793`, retains allocation-02 under `research/analysis/portfolio_multiplicity_5890_t0_v2_20261001/`. Its different Python source, seed and executed synthetic result are not evidence for allocation-01. In particular, allocation-01 planned 224 eligible tests (96 null, 128 alternative), whereas the successor reports 192 eligible tests (96 null, 96 alternative). Their fixed portfolios and outputs must not be pooled or relabeled. Issue #5890's broader scientific status is unchanged.

## Custody checks

- [MANIFEST.json](MANIFEST.json): all three original paths, Git blob IDs, byte lengths and SHA256; total 8,477 bytes
- [HISTORY.json](HISTORY.json): all three single-file additive source commits; no intermediate source version omitted
- [VERIFICATION.json](VERIFICATION.json): static identities, complete scoped duplicate scans and actual verification limits
- [WORKFLOW_SAFETY.json](WORKFLOW_SAFETY.json): current workflow identities and publication-event checks

At inspection main `523ff6d3ae8b9ee09b435dd7460e6582b8d0d258`, the original path was absent. No matching original blob exists in the complete `research/analysis`, `research/archive` or `research/archives` trees inspected; the source branch had no open or historical PR. This is a scoped search, not a claim about every Git object or historical ref.

For independent byte verification from this directory:

```python
import hashlib, json, pathlib
root = pathlib.Path('.')
for item in json.loads((root / 'MANIFEST.json').read_text())['entries']:
    data = (root / item['archive_path']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['git_blob']
print('3 preserved files verified; no research source executed')
```

Publication base main is `b100d9acee4ec99490b2e97066ec6af5312f1ed9`. The archive adds nine files under this one directory. Original refs, allocation paths and successor records remain intact. No research source, construction suite or scientific allocation was executed for preservation. Exact-head remote readback, hosted check results and independent preservation review remain separate publication gates.
