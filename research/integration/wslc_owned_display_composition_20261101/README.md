# Draft private-display owner with held input and stale release

Two fresh WSLc allocations exercised `PrivateDisplayOwner` from draft [#10088](https://github.com/Unjuno/agent-interface/pull/10088), head `120e382ad1ba64574accaf53a5cfa010e7e00907`, in the deliberately injected [stale-release comparison](../wslc_xvfb_stale_release_20261101/README.md). The owner launched an authenticated Xvfb and retained its pidfd. A fixture sent `a` to a separate old target, verified it was held, and stopped the server. One arm retired the owned server and launched another owned display; the other resumed the same server. After the control's fixture released old `a`, a separate fresh client held `b` while the old connection attempted a `b` release.

| Observation | Owned display retired and replaced | Same owned display resumed |
| --- | --- | --- |
| `b` before old release | down | down |
| Old connection release | `ConnectionClosedError` | sent |
| `b` afterward | still down | up |
| Fresh guarded `a` task | target received press/release, release verified, input neutral | same |

In the replacement arm the retired server and the later fresh server exited with code -9 because the draft owner's `close()` also retires its owned child. The old target exited 1 on display destruction and the fresh target exited 0; the resumed arm's two targets exited 0. A fixture explicitly released surviving `b` in the replacement arm, and explicitly released the old `a` in the control. The old held key, stale release and server stop are test injections, not a production cancellation flow or an already queued server request. Terminating a display destroys its application context; a fresh display's neutral state does not confirm the old server physically released input.

Both arms used pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU, a 1 GiB memory limit, no network and no pull; WSLc reported swap was not limited. Both launchers returned zero. The fixed-order pair was frozen before the first run. [raw.zip](raw.zip), SHA-256 `06e1420e635bb9fc36733cdbc8b4b61f18e8cb20e392644ed905999464bdf6d2`, retains source snapshot, conditions, logs and receipts; ephemeral authority files are deliberately excluded. The packaging audit checked frozen hashes, ordering, recorded key states, target events, release receipt and process exit codes.

This is composition in a test harness, not integration of display ownership with the guarded owner, cancellation, MCP or replay policy. The different-display test does not prove same-number cookie fencing, protection against other same-user processes, bounded startup failure cleanup, task preservation, natural failure behavior, MAP01 completion or a general reliability rate. Do not retire a user or shared display on this evidence.
