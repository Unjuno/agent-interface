# Evidence manifest — live authority-ended two-dispatch v1

## Directly retained experiment sources/results

This namespace retains:

- `REPORT.md`
- `prereg.json`
- `runner.py`
- `authority_ended_bridge_executed.py`
- `two_dispatch_gate_executed.py`
- `formal-result.json`
- `formal-valid.json`
- `formal-stale.json`
- `audit_live_two_dispatch_v1.py` — local/raw-directory audit source
- `audit_retained_compact.py` — audit runnable from retained GitHub evidence only
- `formal-valid-raw-text.json.gz.b64` — full valid-arm text evidence bundle
- `formal-stale-compact-evidence.json` — exact claim-relevant stale-arm extraction plus hashes of its original raw sources

### Important retention boundary

The full stale-arm text bundle exists only in the disposable experiment container. Two GitHub uploads of that base64/gzip payload had remote byte counts that did not match the local frozen file. Those malformed uploads were deleted. Therefore **the full stale-arm raw bundle is not claimed retained on GitHub**.

Instead, `formal-stale-compact-evidence.json` retains the exact first terminal/expired owner-release/post-authority fields, all post-release input admissions (empty), all `second`-ID events (empty), terminal score, direct-final independent scorer sample, and SHA-256 identities for the original stale `events.jsonl`, `owner-events.json`, `score.json`, and `scorer-samples.jsonl`. This is sufficient to audit the stale-arm claims made in the report, but is not equivalent to retaining every raw stale text file.

## Executed local source/result identities

```text
4513c91d5bd5df22fdffa61a036eb41f1627704696bd2fe0f6bfb767c6df1ab6  prereg-live.json
b4ed6db6a545cb200e72099c3aab9af5681fa43d235894303179de6d68d7dca6  run_live_two_dispatch_v1.py
82d5b1df8c2d999c6d2c98a528ffc5361a06ef9dd45d70140e0c9f709e9e7698  formal-result.json
f820c327d2e26d95b5497cb5ddf6e13fe2093ec9d54b8fd1f29def635b315080  formal-valid.json
b6d438e4eb24e17bda76321db453e24b160e3e7a394191b62646e936914c88ce  formal-stale.json
2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e  authority_ended_bridge_v1.py
dc179545ced6790c55b348d6553047188eed83cbb2129cb576a83fa406dc1c87  two_dispatch_gate_v1.py
5dd8158a9e2c7041f080736130183cfca51482570e7f6736c02d5b81eb739e7c  audit_live_two_dispatch_v1.py
56d48d70f758451dea76971944cdc61f42ba2384589303637fb7a3c3bfd16005  audit_retained_compact.py
051aa1053c7d802a42619e7ff3d930a34721f65c97cd38ef1f3bee9f7beaece4  formal-stale-compact-evidence.json
```

The published source filenames differ slightly from the disposable-container filenames (`prereg.json` vs `prereg-live.json`, `runner.py` vs `run_live_two_dispatch_v1.py`, and `*_executed.py` vs local candidate names). The hashes above identify the exact local executed bytes; Git blob hashes separately identify the published files. Do not substitute one hash namespace for the other.

## Valid-arm full raw evidence

Uncompressed frozen bundle:

```text
af07c99f46ac0c24bfa98d9c717f16c27f1ff6ba9ec56b7fea5c29c5cac06c1c  formal-valid-raw-text.json
```

GitHub-retained base64/gzip text file (gzip used `mtime=0`):

```text
834eb5844c218651afa3111145abfe753bbd67b6464cbb7c0fde0e96b9c38d4c  formal-valid-raw-text.json.gz.b64
```

Reconstruct with:

```bash
base64 -d formal-valid-raw-text.json.gz.b64 | gzip -dc > formal-valid-raw-text.json
```

Then restore each original text file from `files.<name>.utf8` and verify it against `files.<name>.sha256`. `audit_retained_compact.py` performs these checks directly from the retained base64 bundle.

## Original per-file raw hashes

```text
d2cf84449f6720598ca047611619b7f3566ca6f1ca3cee0a6e85843c84c0b8e9  formal-valid/events.jsonl
48e792793e16db24d85460f56abed386d14043fe299ccf92288ba7d731165093  formal-valid/owner-events.json
ee6c9be57c1ab9234d0d33ca5a26bb96e29c46f2c300a90583d271b4a8ac5b31  formal-valid/score.json
6893a394b9f6a33c74e30874d91b0bff0d1fbb3637a65c495d801d028cc1899c  formal-valid/scorer-samples.jsonl
00ad56d0ac1d2738e684ccc04868a95828ab2fa2117610580a9849f1f9700e19  formal-valid/scorer-summary.json
4f4188ca125652caea60ab1c4b114539422af41bc92fe04549e65056057977a3  formal-valid/environment.json
01f35ffcc32595145dea3da60ac2d52030199413a981af69080130198b439d76  formal-valid/sources.json
d698de161eafc53637415742780c5b773c3ca48d7535ef82f9158e1ce36bf23e  formal-valid/harness-stderr.txt

d3186958dab266d1487caeeab63db5c6004942925136586d6aa192aad3fe10d4  formal-stale/events.jsonl
c3e4641cf602439067bcb01440a2b694d68b322d08eb5bcfd1c791da0aef740e  formal-stale/owner-events.json
f0e696438b0841855e2adc7fcaaa35c85ccf5d39fa73ea63c34f7b0610c3c1f4  formal-stale/score.json
2ca2db2d5aa41e29320ec681e01202da7df2cbcf79670c52486637ca33af79cf  formal-stale/scorer-samples.jsonl
d323f1305a1ee0a011bfb59c2a99ee763a191fa42a29ac124d981e0c6984faab  formal-stale/scorer-summary.json
4f4188ca125652caea60ab1c4b114539422af41bc92fe04549e65056057977a3  formal-stale/environment.json
01f35ffcc32595145dea3da60ac2d52030199413a981af69080130198b439d76  formal-stale/sources.json
365b22fa1527c55e9610e968dee67c3cf310b3cf9f4a56384cee47fa07d07fb8  formal-stale/harness-stderr.txt
```

PNG/AIT/setup-screen binary artifacts remain only in the disposable container and are not required for the release/admission/scorer claims in this report. They are **not** claimed retained on GitHub.
