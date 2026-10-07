# Issue #5905 A06 — longer-horizon image-only cue frontier

## Result

The raw-only independent auditor reconstructed 30/30 sequences and rejected both frozen timestamp and track-substitution mutations. The descriptive frontier showed **no incremental value for secant-TTC** over the simpler cues: at false-YIELD budget 0, TTC detected 3/24 approaches, area growth 6/24 and pixel change 0/24; at budget 1, all three methods reached 24/24. TTC never strictly exceeded both baselines at the same budget.

The strict registered input-blinding condition was **not met**: sequence IDs in the candidate-visible manifest named the family/control type (for example, `approach_00` and `control_camera_scale`). The frozen candidate code only copied those IDs to its output and did not branch on them, and it could not mount/read the separate truth file. Still, the allocated protocol promised candidate-visible inputs without truth labels. Therefore the overall method disposition is **`FAIL_METHOD_PROTOCOL_BOUNDARY`**; retain the audited frontier as descriptive evidence, not as a clean blinded comparison. No thresholds, labels, source or outputs were changed after the run.

## H / T / D / C / U

- **H:** On the frozen finite 24-approach / six-control raster corpus spanning 2.8–7.4 s contact horizons, secant-TTC might identify more pre-contact YIELDs than pixel-change or visible-area growth at a matched false-YIELD budget, with shared timestamp/track/visibility eligibility.
- **T:** A05 stopped pre-candidate when main advanced, with candidate/auditor/retry 0/0/0. A06 refroze at main `d3a51bc4c962b223d05280225042b96a033df8bf`. The WSLc builder produced 24 approaches and six controls, five 256×256 timestamped frames each. Candidate and auditor ran once each, in separate network-disabled CPU-only WSLc containers, using cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. Candidate input mount excluded the truth directory, but case IDs disclosed family names. GPU, Docker, GUI, game, model and input authority were unused.
- **D:** **Overall `FAIL_METHOD_PROTOCOL_BOUNDARY`** because the candidate-visible IDs disclosed labels. Separately, the saved-only audit was `PASS` for all 30 raw feature rows and both mutation controls. The descriptive outcome is `NO_INCREMENTAL_VALUE`: TTC does not strictly improve over both baselines at any false-YIELD budget.
- **C:** A single controlled raster family and six controls may be too small to establish an engineering preference. The area cue is already strictly better at zero false-YIELD in this corpus; at budget one all methods tie.
- **U:** The finite 2-D fixture says nothing about physical optic flow, clock reliability outside the fixture, actual cancellation/release time, a GUI/game, threat response, survival, safety or product benefit. It does not close #59. The strict no-label-blinding failure warrants a genuinely fresh, anonymized successor if this discriminator remains useful; do not rerun this consumed A06 allocation.

## Frozen evidence and execution

- Preregistration: Issue #5905 comments #5989403582 and #5989496927; A05 STOP and source-hash transcription correction are comments #5989490358 and #5989514475.
- A06 freeze: main SHA, script hashes, manifest/truth hashes, image digest and candidate=0/auditor=0/retry=0 prelaunch counts are in `FREEZE.json`. The exact RUN result counts are in `RUN.json`.
- `candidate.py` received only read-only `observations/`, not `truth/`; `audit.py` independently reconstructed features from the archived raw frames and sealed truth.
- The complete PGM input/truth/hash tree is `inputs.tar.gz`. `candidate.json` and `audit.json` are the original saved outputs.
- `--cpus 1` was requested; effective CPU enforcement was not independently measured. No cgroup/swap telemetry was collected. No runtime setting or existing container was changed.

## Exact commands (container image abbreviated only by the documented pinned digest)

```text
wslc.exe run --pull never --network none --cpus 1 --rm --name looming-5905-a06-candidate -v <candidate-code>:/src:ro -v <observations>:/input:ro -v <candidate-output>:/output python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python /src/candidate.py /input
wslc.exe run --pull never --network none --cpus 1 --rm --name looming-5905-a06-auditor -v <auditor-code>:/src:ro -v <bundle>:/bundle:ro -v <candidate-output>:/candidate:ro -v <audit-output>:/audit-output python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python /src/audit.py /bundle /candidate/candidate.json /audit-output/audit.json
```

Threshold arrays and exact arithmetic are frozen in `audit.py`; the full per-threshold results are retained in `audit.json`.
