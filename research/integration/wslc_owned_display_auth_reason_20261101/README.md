# Old authority failure reason after Xvfb display-number reuse

The [previous pair](../wslc_owned_display_auth_reconnect_20261101/README.md) recorded a failed connection with the old authority after replacement but discarded the error, so its precise cause was unknown. This new pre-frozen WSLc pair retains redacted probe output and tests old, current and absent authority files against the current server. A fixture holds input on the old private Xvfb, which is either retired and replaced or resumed. In both arms the actual old and current display names were `:0`.

| Probe | Retired and replaced | Same server resumed |
| --- | --- | --- |
| Old authority | exit 1; server reported invalid MIT-MAGIC-COOKIE-1 key | exit 0 |
| Current authority | exit 0 | exit 0 |
| Missing authority | exit 1; server requested authorization | same |

The probes were new X connections. On the replacement arm, the existing old connection also failed when used for an injected stale release, while a new client's `b` hold survived. On the resumed-server control, that release cleared the fresh hold. After fixture cleanup, a fresh guarded `a` task reached its target and had verified release and neutral X state in each arm. Retiring the old display destroyed its target's application context; that target exited 1. These are test-injected holds and releases, not a production cancellation or a previously queued server request.

This one fixed-order pair demonstrates the recorded rejection for this private Xvfb configuration and supports isolation on display-number reuse. It does not establish security against another process that can read the new authority file, credential revocation on a still-running old server, universal X server behavior, production cancellation integration, physical release on the retired server, hard deadlines, MAP01 completion or a general reliability rate. Probe text has 32-hex strings redacted; ephemeral authority files are excluded from the archive.

Both fresh allocations used the `PrivateDisplayOwner` module from draft [#10088](https://github.com/Unjuno/agent-interface/pull/10088) `93ef7f4321b94ef83cdbea472cba7e85f51cfb78` together with an earlier guarded-owner snapshot, retained as a mixed tree. Pre-run main was `e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d`. The pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25` ran with one CPU, a 1 GiB memory limit, no network and no pull; WSLc reported swap was not limited. Both launchers returned zero.

[raw.zip](raw.zip), SHA-256 `999f8c4759ac7fd09a993e55064432a8ac1828ccf705f0c27d2c2f0d33e56c96`, retains frozen source, conditions, redacted probe output, event logs and receipts. The audit verifies hashes, display names, probe statuses and recorded error strings, event ordering, key state, fresh task/release and process exits.
