# Formal commands (frozen; candidate and auditor each once)

Construction command executed in cached pinned WSLc image:

```text
wslc run --rm --name issue6689-prefix-t0-construction-01 --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<package>,target=/src,readonly --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B -m unittest -v
```

Formal candidate and auditor invocations are retained in the turn execution receipt and are not retried. The candidate source mount is read-only and its separate output mount is writable. The auditor receives the candidate directory as a read-only mount and has a separate writable audit-output mount. Both use `--pull never --network none`, one requested CPU, and the same pinned image. No memory enforcement is inferred from the requested 512 MiB.
