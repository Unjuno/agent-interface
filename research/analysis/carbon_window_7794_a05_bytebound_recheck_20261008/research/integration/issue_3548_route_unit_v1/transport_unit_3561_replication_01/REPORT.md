# Issue #3561 / allocation transport-unit-3561-01

## Outcome

`PASS_UNIT_ROUTE_EQUIVALENCE` after independent audit v2. Exactly one fresh, no-input observation was completed through each public route (API, CLI subprocess, stdio MCP) in an Obstac-managed OrbStack Docker container with network disabled. This is a same-host transport equivalence result only, not a routing preference or product/task-performance result.

The independent audit decoded three 500x260 PNGs to RGB (390,000 bytes each). All PNG SHA-256 values are `f3f0307d73acffbba955fdeb7b0f250746c5de8a8898c438991b4cccc58011a6`; all raw X11 pixel SHA-256 values are `6d0d820d1189f43045aeef6f76adbeff6147f1d6ba7990652b33323eb5155329`. The request binding, native target IDs, frame, region, receipt/raw-pixel lineage, MCP image block, exact one-call denominator, and no-input flags passed. Fixture processes and MCP child were reaped; Xvfb was reaped with recorded exit code 0.

## Audit history

The preregistered auditor SHA-256 `628152a20dd59426cbeeff4eb90ed0c9dce59e3f2834d0ae3c272321ed688018` first returned audit failure: it required Xvfb exit code `-15`, a condition not included in the preregistered cleanup gate. After correcting that auditor-only assumption, its run also exposed its own API/MCP raw-report shape parsing errors. Neither failure changed or reran the frozen experiment. The original auditor is retained unchanged. Auditor v2 is a separate file, SHA-256 `629f46211777d92b4848a2ce8316c808088c59238f4a82560459cb92cf9e1b62`; it checks process reaping plus recorded exit status, and correctly traverses API/CLI/MCP raw-report envelopes. Its independent container run returned `PASS_UNIT_ROUTE_EQUIVALENCE`.

The actual route allocation was executed exactly once. Auditor development/review was performed only against retained read-only evidence and used no runtime API, GUI, or network access.

## Reproducibility boundary

- Source snapshot: repository commit `52260e2c7f296771db3c9e725bbd0a427a4b014f`; exact runtime source SHA-256s are listed in `SOURCE_SHA256SUMS.txt`.
- Image: `agent-interface-3548-routes:20260920`, immutable ID `sha256:76af6aaaab4419b3f799f3121aab191a347130cad07080ac285e3b6d9896cefc`, `linux/arm64`; Python 3.11, MCP 1.30.0, GTK/X11/Xvfb, Pillow, python-xlib.
- Network `none`; source mounted read-only; fresh dedicated evidence output; routes sequential API -> CLI -> MCP.
- Fixture: xmessage name/title `route-unit-3561`, 500x260 at +20+20, fixed message `Agent Interface route fixture v1`; Xvfb `:219`, 640x480x24, TCP disabled.
- Target `fixture`; frame `window_client`; region `[0,0,500,260]`.
- No model, network calls, input dispatch, retries, or tuning.

## Duplicate-work coordination

During execution, main integrated Issue #3562 with a successful allocation for the same scientific question and substantially the same fixture/transport boundary; the repository has also advanced through #3564. This run is an independent replication, not a new transport capability or follow-on hypothesis. It is retained separately and must not overwrite #3562's evidence. Do not claim a timing advantage: the three call boundaries are sequential single samples and structurally different. No model/task, token/cost, router-policy, broad GUI reliability, or product claim follows.

All raw outputs, route PNGs, nested MCP receipt files, cleanup records, and summary are retained in `evidence/`. The initial audit failure is described here and preserved as files/history; it is not silently rewritten as if the first audit had passed.
