# Formal result — Issue #4834

## Disposition

**`FAIL_ONLINE_CORRECTION_FORGETTING` (scoped synthetic result).** All three
fresh seeds crossed the preregistered gate: candidate B reached at least 0.90
while candidate A was below 0.90 after a correction. The independently audited
untouched base retained A at 256/256 throughout. This is not a production or
general skill-learning claim.

| Seed | First crossing | Candidate A | Candidate B | Untouched-base A |
|---:|---:|---:|---:|---:|
| 65117 | 30/32 | 1/256 | 255/256 | 256/256 |
| 65229 | 29/32 | 5/256 | 247/256 | 256/256 |
| 65341 | 31/32 | 9/256 | 251/256 | 256/256 |

All seeds started with candidate A 256/256 and B 0/256; at step 32 all had
candidate A 0/256 and B 256/256. Every one of the 99 per-seed checkpoints,
including every retained row logit and prediction, was recomputed by the
separate auditor. The four source-defined data streams (A training, held-out A,
held-out B, and B correction support) were regenerated from their frozen seeds
and salts; exact row-level duplicates and cross-split overlaps were checked.
Held-out rows were not used for base training.

## Integrity and execution

- Final frozen source commit: `9b4f163261877c7f46c6ba1d5c016247455e8ab5`.
- Source/image/data/environment identities matched the final `FREEZE.json`.
- Construction: 7 tests passed, 0 optimizer updates.
- Formal trainer: exactly 1 local invocation, exit 0; independent auditor:
  exactly 1 separate read-only-source/output invocation, exit 0.
- Audit decision `AUDIT_PASS`; 99 curve points; 0 audit errors; 9/9 corruption
  controls rejected; frozen base digest unchanged for all seeds.
- Cached local Docker image `needle-pilot05:local`, ID
  `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`,
  linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU/thread, 2 GiB,
  64-PID limit, no network/GPU/pull/install, read-only source and root.
- Raw trainer output: 4,622,354 bytes, SHA-256
  `2ac9b2ddde61949888e08feabe152c20a3b6935f754214c83d509d6db7f9f93a`.
- Audit JSON: 775 bytes, SHA-256
  `f1867a47d13aa3581ce60fb195575602424fa5a36f7502c442bb1a0c4e4a2fb9`.

The raw JSON is archived losslessly in ordered binary chunks under
`result/formal/raw_parts/`; `manifest.json` binds compressed and uncompressed
lengths/hashes, each chunk's SHA-256, Git blob SHA, and reconstruction order.

## Interpretation boundary

This fixed synthetic task uses two opposing mappings on the same balanced
binary feature. It demonstrates the measured adapter plasticity/retention
tradeoff under this exact batch-8/32-arrival schedule. The untouched base
provides an A fallback in this toy experiment, but routing policy/cost was not
tested. No Astra feedback, natural language, GUI, user data, action authority,
realistic skill distribution, transfer, concurrency, restart durability,
production safety, or general forgetting-rate inference is established.
No retries, tuning, replacement seeds, or post-result training occurred.
