# Run record — #5372 A01

## Frozen identity and invocation accounting

Allocation: `SAFETY-BACKPRESSURE-ROUTE-EXPANSION-5372-A01-WSLC-20261003`  
Branch: `research/backpressure-route-expansion-5372-a01-wslc-20261003`  
Frozen main: `c33380b3b08792a331ee11f7aee05e3d41437e3e`  
Candidate invocations: 1; auditor invocations: 1; retries: 0.  
The source, fixture, and audit implementation were unchanged after freeze.

## Candidate

Exit code 0. Exact command shape:

```text
wslc.exe run --rm --cidfile candidate.cid --pull never --network none --cpus 1 --memory 256m --user 65532:65532 --mount type=bind,source=\\wsl.localhost\archlinux\home\unjuno\backpressure_route_expansion_5372_a01_20261003\candidate,target=/input,readonly python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /input/candidate.py /input/fixture.json
```

Stdout is preserved byte-for-byte as [candidate.raw.json](candidate.raw.json); SHA-256 `6142DB37F19AB56E65A8DFE87F802EB13B73950CEDD3C205ACEDC536EFA311DF`. Stderr is preserved as [candidate.stderr.log](candidate.stderr.log); SHA-256 `2562006E62622BCF41C809D627CDC2C6250516B8CF1C9CCD28072C331FCC4096`.

## Independent auditor

Exit code 0. One separate WSLc container, same pinned image and isolation/CPU/memory/user flags, read-only mounted audit directory containing only auditor source, fixture, and raw candidate output. Auditor does not import candidate code.

Stdout is preserved as [audit.json](audit.json); SHA-256 `D3A4435A7B891CA775FBF81A069A2554C1E970081EF6ECFE4F67884A60ED999D`. Result: `PASS_METHOD_SCOPED`, errors `[]`, five mutation controls rejected. Stderr is preserved as [audit.stderr.log](audit.stderr.log); SHA-256 `2562006E62622BCF41C809D627CDC2C6250516B8CF1C9CCD28072C331FCC4096`.

## Environment caveat

Both invocations emitted the WSLc warning: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` A 256 MiB limit was requested; effective memory/swap cgroup enforcement was not verified. No retries or substitutions were made.

The sole scientific interpretation is the frozen authored fixture result in REPORT.md. No runtime, GUI, workload prevalence, product latency, or real-agent inference follows.
