# Preservation qualification for Issue #6301 T0 STOP

This is an additive, read-only provenance receipt for the artifacts retained at commit `ccf905c34173d6edb5c08596c581b64db11c76f2`. It does not replace the original evidence, repair the candidate, or rerun any scientific allocation.

## Outcome remains unchanged

- `STOP_AUDITOR_DISAGREEMENT` remains the formal outcome; there is no `PASS_METHOD_SCOPED`.
- The retained report records candidate=1/exit 0 and auditor=1/exit 1. The retained auditor traceback fails full-output reconstruction; all four formal mutation controls were not reached. The original complete argv and separate exit-code sidecars remain unavailable.
- Construction 5/5 is historical construction evidence only. This receipt introduces no model, GUI, runtime, safety, or performance evidence.
- Issue #6301 remains the owner for unresolved research. This preservation receipt is not a new allocation.

## Exact bytes and historical manifest qualification

All 13 retained artifact contents were fetched by their Git blob IDs and independently rehashed using the Git blob header and exact UTF-8 bytes. All 13 Git identities matched.

The original `SHA256SUMS.txt` is a historical manifest, not an exact-current-Git-byte manifest: only its zero-byte `audit_raw.json` entry matches literally (1/12). For ten source/raw entries, removing exactly one final two-byte CRLF suffix (hex `0d 0a`) from the current Git content reproduces the historical SHA-256. No internal newline conversion, text cleanup, or source change is part of that mapping. The current Git blobs are preserved unchanged.

Those ten entries are `FREEZE.md`, `fixture.json`, `candidate.py`, `auditor.py`, `test_construction.py`, `wslc_smoke.sh`, `construction_raw.txt`, `candidate_raw.json`, `candidate_stderr.txt`, and `audit_stderr.txt`.

The remaining historical manifest entry, `REPORT.md`, refers to the initial report, before the subsequent transport and missing-argv disclosures. The [initial report at immutable commit 8c4abedc73dbab0a0081bbcd763c45684a485380](https://github.com/Unjuno/agent-interface/blob/8c4abedc73dbab0a0081bbcd763c45684a485380/research/analysis/effect_terminal_feedback_6301_t0_20261002/REPORT.md), Git blob `e471fb1949f6628ab93deb847fac7779fa6ffb67`, reproduces historical SHA-256 `f51264abac5001a5fdcc250fcdde7cf76d70f2c3d6424e999dce2a0c55a5a684` after removal of exactly that same terminal CRLF. The current report is a different, later document and does not match that historical digest.

This qualifies the current report’s earlier description of a single terminal LF affecting only candidate JSON/traceback: the observed transport suffix is CRLF and applies to all ten listed source/raw entries. No claim of a full original-byte SHA-256 pass is made for the current package. The original manifest and report remain untouched.

## Exact current Git-byte manifest

The table covers the 13 original artifact blobs at the pinned head. It excludes this additive receipt and the shared analysis index.

| File | Git blob SHA-1 | Exact current-byte SHA-256 |
|---|---|---|
| `FREEZE.md` | `ca0fa93108a48a399481f6d0a6feda683bb6510b` | `ea9ac46189890c3c1a20ef29c50937c9a8ee0515a97dba1c91acc90c244fddd8` |
| `REPORT.md` | `397f5183db4f13155957e640c56a42751ea87a50` | `b99997a43e36e5245013affe762cfd9ae22ded31b0a4fce72aabdbd8f514dfb7` |
| `SHA256SUMS.txt` | `76a2c55be7ce178c137786e644e071337aafe0fc` | `86019698b445efeff90289e14803033ea3ecfa81f5c9586b05e9ec6633721577` |
| `audit_raw.json` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `audit_stderr.txt` | `ba28363c413a79a63af2b8c923131c7fb19db6f3` | `697519e03117127a5e6fee8aa3267b7b63180100df035b96002b6b56646d27a8` |
| `auditor.py` | `3e68a2368293b9477dc0167a5d5b7dafd28d5573` | `2d2c0b13fe459e18c3b000271daa98ec9d27c0d2cd2ee28df6bac5269e30467b` |
| `candidate.py` | `11f38798c98a85b2110e6ee38e93bd07275d56df` | `980041ad5585eafa1b5e742b7badacef30bde12f876f4509dcc6b743abe585e1` |
| `candidate_raw.json` | `e7900af203acd24fd3371367fc5bfd5bdf036f84` | `921ed1ea70eb34f4b2bb4902e0455be94448fc41b9a4e463bcd4d48c9730f1a9` |
| `candidate_stderr.txt` | `fa5b691f394f9bbf4aaf2238067b54bcd19e408b` | `065c7499862adf905edff704475828472debe3e2fed0413955dbfd92613e97b7` |
| `construction_raw.txt` | `7cd52950123e591d84b6e6aa2769c55b374019b0` | `25a51c78f8482424934ca829b85fa1776cc04aa18c8a635d403daeaa2c295a57` |
| `fixture.json` | `4cb8e017a9b343e5d32dbcf583d23e9492af7cae` | `4590302d3fbbbdd11a8ed5f6c008b60a92465077cfc3c4db183f6dfb931dbbee` |
| `test_construction.py` | `70709539290667472d51e4f76db9a2f6f0d41257` | `32df5088d097d3f87dac83021312a709736df0cd97115ab5756d36558be4f778` |
| `wslc_smoke.sh` | `85dbacf0b5a6d5884a71fad52a01ad16375a56d9` | `bb321ebf1c2c35f786b9ff7075df2825ec02f0c122e661466daf1af59df5d336` |

## Verification boundary

Only byte identity, historical-manifest mapping, retained-output inspection, and qualification consistency were checked for this receipt. No candidate, auditor, construction suite, container, or consumed experiment was invoked. Historical environment limitations, including unverified peak-memory enforcement, remain as recorded.
