# Excluded construction 05 — XDamage temporal boundary

**Disposition:** CONSTRUCTION_SCOPED_PASS; FORMAL_NOT_RUN. This is not a formal result and contributes zero of 48 formal rows. The one formal allocation remains unconsumed.

## Command and environment

Image: agent-interface-gtk-preflight:local, ID sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4, linux/amd64. CPython 3.11.16, GCC 12.2.0, Linux x86_64. No network, package installation, GPU access, GUI input, provider, or host display.

Construction command (inside the container):

    gcc -O2 -Wall -Wextra /src/native.c -o /results/xdamage-construction -lX11 -ldl
    Xvfb :96 -screen 0 128x128x24 -nolisten tcp -ac
    /results/xdamage-construction

The local source uses runtime dlopen/dlsym for the installed libXdamage ABI because the image has no XDamage development header. A private Xvfb and fresh 64×64 window per condition were used. Before subscribing, the drawable was initialized; after creating the non-clearing Damage object and subtracting setup damage, the event queue was drained. This removed an initial setup event seen in the first construction attempts.

## Results

| Condition | Middle differs from A | Endpoint differs from A | Damage events |
|---|---:|---:|---:|
| QUIET | no | no | 0 |
| REPAINT_A | no | no | 1 |
| PERSIST_B | yes | yes | 1 |
| ABA_1PX | yes | no | 1 |
| ABA_2X2 | yes | no | 1 |
| ABA_8X8 | yes | no | 1 |

The independent standard-library byte auditor read each three-frame RGB record, verified its 36,864-byte length and exact expected equality/difference pattern, and reported PASS_CONSTRUCTION_BYTES. It imports neither the C harness nor the protocol module. QUIET and REPAINT_A produce identical byte hashes, while all transient/persistent cases have distinct bytes as expected.

Per-file SHA-256:

- QUIET / REPAINT_A: 1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75
- PERSIST_B: 56f8099c8523d70db1a62a9d241c1b961055a0b23c09fbb3f500dd3f4fb0621d
- ABA_1PX: fcf172f32212c93fd26811eb956fd86620b5b6e6b154be90f0631d208f543b77
- ABA_2X2: 5f1c7a5f1ce4242ed7911733a92ac2de226f292dbfdfef803aeb65be234102e8
- ABA_8X8: 536a29b7a6502fb795ced9905de864b3d8642675d35c04700d0138eb916eef17

Lossless artifact archive: construction05_raw.tar.gz, 6,279 bytes, SHA-256 b393d9ae3b7c8fbfe46242553058346d57442ed2c32197453feb3ccca3ddfe50. It is stored in the branch as base64 text so GitHub Contents can preserve the exact compressed bytes. Construction stdout SHA-256: 5a6c1ed3d8e7ae9fcefca223debcbc23095a0afb695f3161876fc0ac53baf81f.

## Construction-only limits and remaining gates

This code performs drawing and capture on one X client and one serial Xvfb session; it does not implement the planned independent renderer/observer processes, eight fresh X servers, an O1 ExactGate candidate boundary, event-source identity audit, or the required corruption-control suite. The RGB middle frame is captured for scoring, but role separation is not enforced. Damage event counts demonstrate scoped construction behavior only.

Two earlier setup failures are retained as incidents, not experimental rows: (1) unresolved XDamageQueryExtension when the ABI was called without dynamic symbol resolution, and (2) execution from the container's noexec /tmp; an initial attempt also stopped when the host output directory did not exist. These did not run or consume formal cases.

No PASS for the hypothesis is claimed. Before any formal run, the runner and auditor must enforce the independent-process/endpoint-only boundary, exact per-row receipt binding, eight-session schedule, and all corruption controls; then freeze/read back the full source. Until then formal count remains 0/1.
