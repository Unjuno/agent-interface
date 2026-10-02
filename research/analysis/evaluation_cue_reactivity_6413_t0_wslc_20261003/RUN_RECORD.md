# Formal run record — AI-6413-T0-WSLC-20261003-A01

- Base main: `43f7cd88d91af05036fae2100ec4e155c59e105c`; dedicated branch: `research/6413-evaluation-cue-t0-wslc-20261003`.
- Runtime: WSL 3.0.1.0, Arch Linux WSL2, `wslc.exe`, cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, CPython 3.12.15, linux/amd64.
- Construction image `ai6413-evaluation-cue-t0:20261003-a02`, image ID `sha256:e12ace5d8a5ebb7fef86155a11be1acf4127b3ca3492dbaa338d36bb8a974105`; WSLc construction/mutation suite PASS 7/7 before formal freeze.
- Frozen candidate image `ai6413-candidate:20261003-a01`, image ID `sha256:0ce236142180bbb3d146f3e546a60b5091a771786ee0511501f8d6fb5540aef3`.

## Candidate

Exact command:

```text
wslc.exe run --rm --pull never --network none --cpus 1 --name ai6413-candidate-a01-20261003 sha256:0ce236142180bbb3d146f3e546a60b5091a771786ee0511501f8d6fb5540aef3 python /src/candidate.py
```

Exit 0; one invocation; stdout retained byte-exactly at `results/formal-a01/candidate.raw.json` (79,408 bytes, SHA-256 `8ce339f94814436e4bf11cc0b9dbcd1f0ea9db7c921a993c6dc31c4522fac3a9`). No stderr or retry recorded.

## Independent auditor

The auditor image was built only after candidate completion, with the immutable raw output embedded at `/evidence/candidate.raw.json`; candidate source is absent.

Exact command:

```text
wslc.exe run --rm --pull never --network none --cpus 1 --name ai6413-audit-a01-20261003 sha256:41d5cb7cd70c3f09d46811ec5ce22f26aca4a144bd887dce54b7c288bd3254e4 python /src/audit.py
```

Exit 0; one invocation; stdout retained at `results/formal-a01/audit.json` (340 bytes, SHA-256 `a65c3a4bba837347b979fa72a2cabcc590ea685e63f3fbe4747ba820a45c1f61`). Result: `METHOD_PASS_SCOPED`, 12 valid rows, six pairs, four manifest-bound panels, three expected invalid-control classifications, zero errors. No retry.

## Runtime observations and stops

- Formal preflight found the WSLc container inventory empty and no known research candidate/auditor processes active. The latest main advancement was fast-forwarded before freeze; #4695 panel sources and this additive path were unchanged.
- Both formal calls used one CPU requested, pull disabled, network disabled, ephemeral `--rm` containers. No GPU, model/provider, GUI, user data, native input, human, or external effect.
- No warnings were emitted by the formal invocations. WSLc does not expose read-only rootfs/capability drop/no-new-privileges; source/input/evidence were non-writable with UID 65532. Hard memory enforcement is not claimed.
- Candidate/auditor/retry counts: 1/1/0. No formal failure or stop occurred.
