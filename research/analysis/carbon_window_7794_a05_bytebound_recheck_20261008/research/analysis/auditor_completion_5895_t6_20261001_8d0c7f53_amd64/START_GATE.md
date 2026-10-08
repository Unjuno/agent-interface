# T6 start gate

- Observed UTC: 2026-10-01 12:38:00Z; inside owner-confirmed 12:35–12:55Z slot (#5085 comment #5931167730; registered on #5895 comment #5931175249).
- Owner/allocation/branch: current task thread `01a0b98b-8d0c-7f53-92bc-4c6a28d73c73`; `AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53`; `research/auditor-completion-5895-t6-amd64-8d0c7f53-20261001`.
- Queue reread: later #6001 allocation #5931436251 is 13:00–13:15Z, after the T6 slot and five-minute handoff; #5752/#5882 are distinct Windows GPU host reservations. No later local OrbStack overlap observed.
- Issue #5895 remains open with this exact eight-case synthetic CLI scope. PR #5630 remains open/draft, mergeable, frozen head `288d0498d11cf16657e523a04616bf4f49cd94f4`.
- Current main and HEAD: `722c42bf0d6d808cf80575ecb6353401de934b26` (fast-forward complete).
- Docker context: `orbstack`; running container inventory empty at gate.
- Image: exact digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; platform image ID `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`; platform `linux/amd64`.
- Frozen PR target blobs verified against `FREEZE.json`: `da805fb83f70a57ad68a0768186e214524689d40`, `3d33bda096c4c8789e183e3f864ee7626e643a7e`, `d1eb9a854cc810fa77ca173d7e2de287ee1bd64a`.
- Source, preregistration and host-tool SHA-256 values verified against updated `FREEZE.json`. The formal output and host receipt paths were absent before launch; one-shot scripts enforce empty paths, context, image, and no running containers.
- Decision: all start gates pass. Candidate invocation limit 1; auditor invocation limit 1 conditional on candidate exit 0; retries 0.
