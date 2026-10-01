# Independent audit-only reconstruction for #5037

This is a read-only audit successor. The #5037 seven-case OrbStack formal run and its first audit invocation are consumed; neither may be rerun or altered. #5037's first auditor exit 2 is preserved exactly. The defect was a lookup for `FREEZE.json.broker_sha256` instead of the frozen nested `FREEZE.json.target_source.sha256`.

## H / T / D / C / U

- **H:** A corrected independent standard-library auditor verifies the immutable #5037 raw bundle, reconstructs all seven expected process/receipt/response outcomes, confirms all receipts remain non-authoritative, and rejects eight fixed corruptions.
- **T:** One audit-only allocation, `broker-fake-child-boundary-4485-orbstack-audit-successor-20260928-01`, consumes the exact `formal01/` tree. Freeze pins the input FILE_MANIFEST and RESULT SHA-256s, broker SHA-256, auditor/tests/launcher, and cached Python 3.12.14 ARM64 image identity. The runner verifies the formal FILE_MANIFEST hash before launching and mounts evidence/source read-only. No broker process is launched.
- **D:** PASS only if all raw manifest entries verify, nested broker source digest and runtime/architecture reconcile, all seven semantic rows pass, and all eight mutations reject. The historical `FAIL_AUDIT` remains unchanged; a PASS here is an audit-only addendum, not a rewrite of #5037 or a second formal run.
- **C:** Only the auditor is corrected. The #5037 formal raw bytes and first failed audit are immutable. No real Codex/model/provider/network/GUI/input or task authority.
- **U:** One retained ARM64 fake-child dataset. No AMD64/Docker Desktop parity, real provider behavior, runtime authority, GUI/task correctness, latency, or product readiness.

## Frozen input and first outcome

- #5037 formal manifest SHA-256: `5ae0e8e6dd5cf1d194cf4270f1dc210896e4e78e8fed09599d403177e7b8ad46`
- #5037 formal `RESULT.json` SHA-256: `ae09573149160bda321e10ff14483b9cd4690d5c472b4a630b4ebef6b7583a59`
- #5037 original `audit01/AUDIT.json` SHA-256: `a69284a0a245723469ff740051907271c1f62795151abb4f83a9267a32fbb441`
- Original audit: 7 rows; 8/8 corruption controls rejected; `errors=["broker_source_hash"]`; exit 2.

The raw manifest enumerates 32 evidence files (the manifest itself is pinned separately by this freeze and launcher). All outputs from the new audit are kept in `audit02/`; the old `audit01/` remains byte-identical.

The competing #5036 Docker Desktop/amd64 formal lane is separately owned and is not pooled with this ARM64 dataset. Coordinate before container execution and do not start another broker formal run.
