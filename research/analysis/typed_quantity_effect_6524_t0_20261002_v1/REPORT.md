# Formal T0 result — typed quantity-effect oracle

## Disposition

`METHOD_PASS` and `H_PASS_SCOPED` under the preregistered finite synthetic fixture only. This is not a real GUI or product result.

Allocation: `TYPED-QUANTITY-EFFECT-6524-T0-20261002-01`  
Issue: [#6524](https://github.com/Unjuno/agent-interface/issues/6524)  
Frozen main base: `cf467e076b67f103e50fbbd47cc43007624a2ca8`  
Branch head used: `87bbaa940b1e28c7250a825d6c1775cf85412065`  
Formal path: `results/allocation-01/`

## Execution record

One WSLc 3.0.1.0 container used linux/amd64 image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, CPython 3.12.14), network disabled, source read-only, separate writable output, CPU request 0.25, pull never, no GPU flag, and no memory-limit claim.

```powershell
$src=(Resolve-Path .\research\analysis\typed_quantity_effect_6524_t0_20261002_v1).Path
$out=Join-Path $src 'results\allocation-01'
wslc.exe run --rm --pull never --network none --cpus 0.25 --volume "${src}:/src:ro" --volume "${out}:/out" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python3 -B /src/run_once.py /out
```

Formal counts: candidate=1, raw-only independent auditor=1, retries=0. Candidate exit 0; it emitted exactly one newline-terminated JSON document (3,400 bytes). Auditor exit 0; stderr was empty for both processes.

## Reconstructed outcomes

The auditor reported `errors=[]`, 11/11 reconstructed rows, two typed PASS rows, and six bare-number false positives. Status counts:

| Typed status | Cases |
| --- | ---: |
| PASS | 2 |
| WRONG_MAGNITUDE | 3 |
| WRONG_DIMENSION | 1 |
| WRONG_KIND | 1 |
| WRONG_EFFECT_COUNT | 1 |
| NO_EFFECT | 1 |
| UNKNOWN_CONVERSION | 1 |
| UNKNOWN_ROUNDING | 1 |

The accepted cases were the equivalent 120 cm → 1.20 m save and the declared within-tolerance rounded save (1.234 target, 1.235 persisted, tolerance 0.001). Bare-number comparison rejected both valid conversions. It incorrectly passed six planted cases: same number in the wrong unit, wrong dimension, wrong quantity kind, no save despite a matching pre-existing value, undeclared unit, and duplicate save effect. The typed oracle rejected/classified all six; it also rejected the selector-switch and outside-tolerance cases. No injected incorrect/effectless/unknown row received typed PASS.

The nine copied-output corruption mutations were separately verified before formal use by the construction suite on both host and WSLc; each changed the selected field and was rejected by the independent audit function. The construction suite passed 7/7 on host CPython 3.11.9 and 7/7 on the pinned WSLc image. Those construction checks are not additional formal candidate/auditor allocations.

## Raw artifacts and hashes

- `candidate.raw.json`: 3,400 bytes, SHA-256 `587288c17c5a9170d08ef41cbe93db89837a3a11b4ebaf1e9dedfda2c62f79e0`.
- `auditor.stdout.json`: 242 bytes, SHA-256 `fe500c88d012455418b6f1a029408c67e81b6215512868b42f2930bc7cd0e849`.
- `RUN_MANIFEST.json`: SHA-256 `e1244c25fade349095bbd7e39320c5d94b7e45d706ae7fe5b74e7d6751a1bf38`.
- `candidate.exit` and `auditor.exit`: each contains `0\n`; SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.
- Both stderr files were empty; SHA-256 of empty bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Limits and next boundary

This finite synthetic app-state model stipulates the conversion and persistence rules that its independent oracle checks. It does not show that any current application changes units this way, that a real screen or store can be read correctly, or that the typed contract improves runtime decisions. No model, GPU/CUDA, GUI, user/private data, external effect, or network was used. Healthcare dosage, money, calendar units, nonlinear scales, app-specific units, locale parsing, target authority and production safety remain outside scope. No T1 or runtime promotion follows automatically.
