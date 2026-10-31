# Old authority reconnect after private display replacement

The owner uses Xvfb `-displayfd` to select actual display numbers. The earlier [composition record](../wslc_owned_display_composition_20261101/README.md) had called its replacement a different-display test, but its numeric labels were harness labels and the actual numbers were not recorded. That wording has been corrected. This new pre-frozen WSLc pair records actual display names and attempts a new connection using the old authority file.

| Observation | Retire and replace | Resume old server |
| --- | --- | --- |
| Old / current display name | `:0` / `:0` | `:0` / `:0` |
| New connection using old authority | exited 1 | exited 0 |
| Existing old connection's injected stale release | connection closed; fresh `b` stayed down | sent; fresh `b` became up |
| Later fresh guarded task | target received `a`, release verified, input neutral | same |

In the replacement arm a connection using the new authority had already succeeded and the subsequent fresh guarded task succeeded; the old-authority probe returned nonzero. This is consistent with new-cookie fencing even when `:0` was reused. The probe discarded its error output, however, so the retained result does **not** independently establish that authentication rejection was the precise reason for the failure. The resumed-server success is a positive control for the old authority in its original context. The fixture explicitly released surviving input; the old target exited 1 on display destruction and its application context was lost.

Both fresh allocations used the `PrivateDisplayOwner` module from draft [#10088](https://github.com/Unjuno/agent-interface/pull/10088) `93ef7f4321b94ef83cdbea472cba7e85f51cfb78` with the earlier guarded-owner source snapshot; the mixed tree is retained, not attributed to a single commit. Pre-run main was `e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d`. The pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25` ran with one CPU, a 1 GiB memory limit, no network and no pull; WSLc reported swap was not limited.

[raw.zip](raw.zip), SHA-256 `2d6dc08e50bc5c104c44d6f683d3967d78d4d5a425373f6668a5fdd30fa7e2f9`, retains conditions, source, results and target receipts. Ephemeral authority files are excluded. The audit checks frozen hashes, recorded display names and probe exit codes, event order, key states, fresh task release and process exits. The held old key and stale release were test injections; no actual old guarded cancellation or queued server request was tested. One fixed-order pair does not establish general authentication security, protection from same-user credential access, production cancellation integration, physical old release, hard deadlines, MAP01 completion or a reliability rate.
