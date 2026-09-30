# Excluded construction recovery — 2026-09-30

## Identity and environment

- Frozen allocation: `blind-tail-generation-witness-2923-20260923-01`
- Frozen formal denominator: 40; formal invocations before and after this
  recovery: 0
- Frozen source archive SHA-256: `daad816cef866df63424dc7351ec1cf84de5a9983f0c9326fe032d760736b874`
- Docker image: `tk-xkb-refresh-4664:20260927-01`, image ID
  `sha256:4c62a3d908f6bffdbff88b28eeff305bed40f5d6fcee029b7c0a3fa2ea5a86d6`
- Actual platform: Linux/ARM64 under OrbStack; container kernel reported
  `7.0.14-orbstack-00380-ga7e0a2dc9535`
- Actual Python/Xlib/Tk: CPython 3.12.3 / Python-Xlib 0.33 / Tk 8.6
- Frozen required environment: Linux x86_64 / CPython 3.13.5 / Python-Xlib 0.15
- Docker Engine: client 29.5.2 / server 29.4.0

The mismatch is why only the disjoint construction schedule was run. The
container had no network, a read-only root, private per-case TCP-disabled
Xvfb (`-nolisten tcp -ac`), a temporary filesystem, dropped capabilities, and
an explicit empty XAUTHORITY file. No model, provider, GUI on the host, task
input, or user data was involved.

## Command

```sh
python3 -B study.py construction --out /results/construction --display-base 740
python3 -B audit.py /results/construction --out /results/construction/AUDIT.json
```

Both ran inside the image above with the frozen source mounted read-only and
only the output directory mounted writable. No formal command was invoked.

## First construction outcome

`SUMMARY.json`: 4/4 disjoint construction rows; two blind-tail rows resolved
by the fresh generation witness (2/2), predecessor control remained UNKNOWN
(2/2), stable control matched (1/1), stale witness remained UNKNOWN (1/1),
wrong directions 0, authority grants 0. The retained frozen audit reports
`rows=4`, `errors=[]`, `pass=true`.

This is not evidence that the formal 40-row acceptance gate passes. No frozen
formal corruption controls were run. The runner terminates each Xvfb child but
does not store its exit code in the raw row; stdout/stderr are retained. The
Xvfb stderr contains xkbcomp missing-keysym warnings that explicitly state
they are non-fatal to the X server. Those process/provenance limits remain
open for formal review.

SHA-256:

- `SUMMARY.json`: `075e539b7b7fd0a3767d2f3024701792dbfd1ad6207fa2c09b21620d73c18764`
- `AUDIT.json`: `1a540108e6d952a945308865832170f2d28ff7eff1ec18523cd5d22fe1c6f588`
