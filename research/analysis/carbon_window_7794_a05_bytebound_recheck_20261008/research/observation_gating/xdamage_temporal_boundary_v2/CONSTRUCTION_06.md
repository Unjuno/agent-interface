# Excluded construction 06 — run from GitHub-readback source

Disposition: CONSTRUCTION_SCOPED_PASS; FORMAL_NOT_RUN. This is an excluded construction block, not six formal rows. Formal count remains 0/1.

## Provenance

- GitHub source blob: 6fd4f20477e851e56b2b174b177eae68402ceda0
- Source SHA-256 after GitHub readback: 1b0d64c8ee2f135e09f14e7ca24e7a9c819875e2630a81d676d91c7f97f33394
- Rebuilt executable SHA-256: ab068e1e87378f71ef631023a13ae7f9a260381c04e5d2f2b434f1b0346d4c4a
- Image: agent-interface-gtk-preflight:local, sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4, linux/amd64
- Python 3.11.16, GCC 12.2.0, network none; no GPU or package install.

The earlier construction-05 binary was built from the local mixed-line-ending file and did not match a rebuild from the published bytes. That provenance mismatch is preserved; construction 06 recompiles the exact GitHub-readback source instead. The source filename/content identity and rebuilt executable identity are retained in construction_manifest.json.

## Run

From the mounted source and fresh results directory:

    docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=32m --entrypoint /bin/sh -v "${PWD}:/src:ro" -v "${PWD}/results/construction06:/results:rw" agent-interface-gtk-preflight:local -ec 'gcc -O2 -Wall -Wextra /src/construction_native.c -o /results/xdamage-construction -lX11 -ldl; Xvfb :97 -screen 0 128x128x24 -nolisten tcp -ac; /results/xdamage-construction'

The actual invocation saved stdout, compiler stderr, Xvfb stderr, executable, manifest and raw frames into the output directory. Native exit 0; independent raw-only standard-library audit exit 0.

## Six conditions

QUIET equal/equal, 0 damage; REPAINT_A equal/equal, 1; PERSIST_B changed/changed, 1; ABA_1PX, ABA_2X2 and ABA_8X8 changed middle/equal endpoint, each 1. Each raw RGB file is 36,864 bytes. The separate auditor reports PASS_CONSTRUCTION_BYTES; hashes are identical to those in CONSTRUCTION_05.md.

Lossless raw artifact: construction06_raw.tar.gz.base64. Decoded archive size 7,058 bytes, SHA-256 e90b63068255a82fae7234aafca9d9e8a29b55d5768717e9976bbe21cfaca29b.

## Limits

Same-client draw/capture on one serial Xvfb session; no independent renderer/observer boundary, eight sessions, candidate ExactGate, event/process audit or corruption suite. No scientific PASS; formal remains unrun.
