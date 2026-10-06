# A02 formal run — PASS_METHOD_SCOPED

Allocation: `SERIAL-CUE-7387-T0-WSLC-A02-20261004`. A01 remains terminal STOP and contributes no data.

## Frozen identity and invocations

- Intake base main: `2ed11c5552956499454e8a99acf5a2f374106d34`. Before A02 candidate, latest main was `95206640bacbdf31dd9f8653148e0f3535d203dc`; before audit it was `8094af4631fc7bc5d92990e5151d5e89477ee39f`. Each post-freeze advancement was reviewed and affected only `research/analysis/README.md`; changes were merged into the branch, while the frozen package/source remained byte-identical.
- Branch head used: `cc162c2184aa13d7fb46bde86ecb28e4e4fafa11`.
- WSLc 3.0.1.0; `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `9e87977b8678`; Python 3.12.14, Linux/amd64.
- Candidate: one invocation, exit 0, `2026-10-04T03:18:48.5079444Z`. Auditor: one invocation, exit 0, `2026-10-04T03:20:07.9982893Z`. Retries=0.
- Both invocations used `--rm --pull never --network none --cpus 1 --memory 512M`, the repository source mounted read-only, and a unique separate writable output mount. Active-container inventory was empty before each invocation and after each exit; the image digest and ID were checked before each.

Candidate command:

```text
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --name ai-7387-t0-a02-candidate --volume C:/Users/junny/Documents/Codex/2026-10-04/observation-cue-7387-t0:/src:ro --volume C:/Users/junny/Documents/Codex/2026-10-04/observation-cue-7387-formal-a02-output:/out:rw python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/research/analysis/serial_cue_interference_7387_t0_20261004_a02/candidate.py --out /out
```

Auditor command:

```text
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --name ai-7387-t0-a02-auditor --volume C:/Users/junny/Documents/Codex/2026-10-04/observation-cue-7387-t0:/src:ro --volume C:/Users/junny/Documents/Codex/2026-10-04/observation-cue-7387-formal-a02-output:/out:rw python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/research/analysis/serial_cue_interference_7387_t0_20261004/auditor.py --out /out
```

## Result and audit

- Candidate reported 144 matched trials, 288 presentations, 16 isolated controls, 1,280 PPM files; candidate SHA256SUMS text digest `9538a4e4203887c89523b4b48e27107bdf924f6529235319c7407daf8d0e297e`.
- Copied formal output contains 1,284 files / 4,313,874 bytes before adding the two invocation transcripts to this package. `output/SHA256SUMS` SHA-256 is the same `9538...` digest. Audit JSON SHA-256: `C8EB9A349894B01DA129D951D84DF6E636C6BE6AE8F3902AA94D22ED8E5CE70C`.
- Independent auditor: `ok=true`, `errors=[]`; exact reconstruction of 144 trials, 288 presentations, 16 isolated controls and 1,280 images. It checked byte-identical arm image-path sequences, pixel masks, positions, source indices, prompt/arm mapping, answer-metadata leakage controls and file checksums.
- Offline construction checks: A02 suite 3/3 (absent root, existing-empty root, nonempty-root preservation); original pixel/oracle mutation suite 5/5 (clean control plus four corruptions) passed before formal use. The A01 and A02 construction/import failures are preserved in their respective READMEs; neither was a formal retry.

## Warnings and scope

WSLc emitted on both invocations: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The `--memory` value is not claimed as an effective hard limit. Synthetic authored shapes and stipulated lags only; no model, human, GUI, action, timing, safety, runtime or product result. `PASS_METHOD_SCOPED` is only a finite deck/oracle construction result; Issue #7387's lag-by-task-demand hypothesis remains untested and any T1 needs separate model-call ownership and preregistration.

Exact combined invocation transcripts: [candidate](formal_01/candidate.combined.txt), [auditor](formal_01/auditor.combined.txt). Raw fixture, image files, oracle, and inner checksums are retained under [formal_01/output](formal_01/output/).
