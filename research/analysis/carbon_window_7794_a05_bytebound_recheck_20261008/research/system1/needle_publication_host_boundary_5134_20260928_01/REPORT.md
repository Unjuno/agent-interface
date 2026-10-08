# Host filesystem boundary result — Issue #5134

## Result

`PASS_HOST_BOUNDARY_SCOPED` on one macOS host filesystem. The one-shot runner exited 0 and the separately invoked independent auditor exited 0 with `errors=[]`. It reconstructed all 28 atomic observations and all 28 unsafe partial-prefix observations. There were 28 distinct reader PIDs in each arm, across seven generations (3789–3795).

For every atomic row, an independently spawned reader opened `ACTIVE` before publication, then read the retained descriptor after `os.replace` returned and observed the exact prior package; a fresh path open observed the exact next package. For every unsafe row, the writer truncated `ACTIVE`, wrote the frozen strict prefix, and waited while all four independent readers observed that exact incomplete prefix through both the held descriptor and a fresh open. Only after all reads did the writer finish; all seven final files matched their exact candidate bytes.

This is a real host-filesystem boundary result for the frozen setup, not a Docker/OrbStack result. It does not establish that a container-to-host bind mount has the same semantics. The requested OrbStack experiment remains open; its distinct allocation `needle-publication-orbstack-bind-5066-20260928-02` stopped before container launch because the shared OrbStack inventory was occupied by an owner-unidentified pre-existing container. That allocation is consumed and must not be retried.

## Frozen design and execution

- Allocation: `needle-publication-host-boundary-5134-20260928-01`.
- Frozen main/source base: `16421aefa2ec357b79e3fd3dc307b32955bc6fab`; tree `addf13a48e55ea55d86b83daae2709ba3fd82903`.
- Host: macOS 25.6.0, arm64, Python 3.14.5; `/tmp` resolved to the local data filesystem (`/dev/disk3s5`, 3.6 TiB volume). The test used a fresh `/tmp/needle-pub-host-boundary-*` scratch path and a separate fresh output directory.
- Input: immutable seed-3788, 15,279 bytes; Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107`; SHA-256 `2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`.
- Formal runner invocation count: 1. Auditor invocation count: 1. Docker/OrbStack invocation count: 0; container ID: none.
- Exact runner command (exit 0):

  ```sh
  python3 -B research/system1/needle_publication_host_boundary_5134_20260928_01/host_boundary.py --repo /Users/taka/Documents/Codex/2026-09-19/new-chat-3/work/agent-interface-5134-host-boundary --output /tmp/needle-publication-host-boundary-5134-20260928-01
  ```

- Exact independent-auditor command (exit 0):

  ```sh
  python3 -B research/system1/needle_publication_host_boundary_5134_20260928_01/audit.py --bundle /tmp/needle-publication-host-boundary-5134-20260928-01 --repo /Users/taka/Documents/Codex/2026-09-19/new-chat-3/work/agent-interface-5134-host-boundary
  ```

- Construction CI before execution: `python3 -m unittest -v test_host_boundary.py` — 5/5 PASS; `python3 -m py_compile host_boundary.py audit.py test_host_boundary.py` — PASS; `git diff --check` — PASS. The test suite verifies a synthetic positive audit fixture and rejects a raw-byte mutation.

## Evidence identities

Retained output is in `results/host-boundary-01/`:

- `raw.json` SHA-256: `6a49e753e40c44df0ed66c0d3b37b744d30479c75bf4e64c681073f4e75ccd8c`
- `run_receipt.json` SHA-256: `8e980a31af50509dd237631969e380b1a07f8913d95d8361f39e81e8efe82e40`
- `audit.json` SHA-256: `d404e33dc5ac9c4a3f0e987d701df286794a007d04024eaa1ae47bd53b526405`

The source inventory and frozen H/T/D/C/U are in `FREEZE.json`; the preregistered design is in `PLAN.md`. The source inventory does not hash this report or the generated result artifacts; their identities are recorded in `MANIFEST.sha256`.

## Scope and next required experiment

The unsafe arm uses a deliberate barrier, so it proves that in-place writes can expose an incomplete strict prefix when a reader runs during that interval; it does not estimate uncontrolled race probability. The atomic arm establishes exact old-descriptor/new-path observations for this host filesystem and schedule only. No crash/reboot durability, performance, other filesystem, cross-platform, OrbStack, application, or production-safety conclusion follows.

Next, after the running shared container's owner/lifecycle is reconciled and a fresh exact queue assignment is recorded, create a new additive OrbStack allocation/source freeze and run that distinct bind-mount experiment once, followed by one independent raw-only audit on formal exit 0. Do not reuse `-02` or this host allocation.
