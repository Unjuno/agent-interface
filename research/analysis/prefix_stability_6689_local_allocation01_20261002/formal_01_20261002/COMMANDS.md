# Formal commands (frozen; candidate and auditor each once)

Construction command executed in cached pinned WSLc image:

```text
wslc run --rm --name issue6689-prefix-t0-construction-01 --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<package>,target=/src,readonly --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B -m unittest -v
```

Formal one-shot commands:

```text
wslc run --rm --name issue6689-prefix-t0-candidate-01 --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<package>,target=/src,readonly --mount type=bind,source=<candidate-output>,target=/out --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B candidate.py /out/raw.json
wslc run --rm --name issue6689-prefix-t0-auditor-01 --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<package>,target=/src,readonly --mount type=bind,source=<candidate-output>,target=/raw,readonly --mount type=bind,source=<audit-output>,target=/out --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B audit.py /raw/raw.json /out/audit.json
```

Observed raw audit receipt: candidate exit 0, 769 output rows, raw SHA-256 `f95ef664ebfc663a784747297e493dc3c5cd0e4b1adc8d26e9c2bb7e887644e3`; independent raw-only auditor exit 0, emitted `PASS_METHOD_SCOPED`, errors `[]`, 768 states, all four implemented corruption controls rejected, audit SHA-256 `e093260fe645a5ebb2476a18f3b366f1f98200cf3e4586d3a992fd6c6e999b2a`. Candidate/auditor/retries=1/1/0. Candidate source was read-only; auditor received candidate raw read-only. No memory enforcement is inferred from requested 512 MiB. Posthoc acceptance is `FAIL_METHOD`; see `ADJUDICATION.md` for the missed obligation-preservation criterion. The PASS string above is the unchanged emitted audit receipt, not final acceptance.
