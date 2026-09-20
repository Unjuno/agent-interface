# Issue #3370 — direct host image, bounded Inkscape task

## H / T / D / C / U

**H.** A fresh native MCP image can be delivered as the current model's image
input, used to ground one bounded action, and lead to a saved, independently
scored Inkscape effect with verified input release.

**T.** Frozen main: `71c712eb6dd11dc3cc167fd7a0588a85c89822ce`. Runtime:
OrbStack `linux/arm64`, image
`sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`.
Formal-05 used seed `991122`, one persistent MCP stdio session, one initial
image, one model decision, and one `native_submit`. The exact MCP PNG was
forwarded unchanged as a model image item (SHA-256
`505c17b695d2c4a71b8ae5b0e52a1c90261d25764ca4d3ae9b19b2933e1abec9`). The
single action clicked the visible rectangle, waited 50 ms, sent 18 Right
chords, waited 50 ms, saved, and waited 300 ms. Container runtime had
`--network none`, a read-only root/source, private Xvfb, and a dedicated
evidence mount.

**D.** `PASS_DIRECT_HOST_IMAGE_SINGLE_TASK_SCOPED`. The independent SVG oracle
passed: x=86 (>50.5), y=50, width=40, height=30, no transform. One native action
was recorded; its release ledger verified `keys_down=[]` and
`buttons_down=[]`. The managed task process and container exited 0. The separate
audit program reported zero failures. Formal-04 is retained as a FAIL: the
action completed and release was verified, but the saved SVG stayed at x=50.
Formal-03 is retained as a pre-dispatch flat-region refusal and client STOP.
Formal-01/02 are setup/input-channel STOPs; none are overwritten or presented
as successful task trials.

**C.** Same model handled the returned PNG and authored the source-sequence-1
decision; the client verified immutable request/decision hash linkage, one
submit, zero resumes, one action, cleanup, and saved effect. The runner's
independent check is `evidence/formal-05/audit.json`; final task report is
`evidence/formal-05/allocation/run/reply-1.json`.

**U.** This is a narrow single-task result. It does not timestamp host
presentation or model interpretation, compare against saved-file/view-tool
delivery, exercise stale/delayed/no-image/disconnect controls, measure provider
tokens/cost, or establish latency/speed benefit. Full Issue #3370 remains open.
The result is component-level evidence for later integration workers to
revalidate, not a general host image boundary guarantee.

## Trial ledger

| Trial | Outcome | Preserved finding |
|---|---|---|
| formal-01 | STOP | Container lacked `wmctrl`; GUI window discovery failed before image return. |
| formal-02 | STOP | Attached stdin closed before a decision could return to the live MCP session. |
| formal-03 | STOP | Exact image reached the model; click was safely refused as a flat target before input; client exited before bounded recovery. |
| formal-04 | FAIL | One accepted click/key/save action, verified release and cleanup, but no saved geometry effect (x remained 50). |
| formal-05 | PASS, scoped | One grounded MCP image action; saved geometry x=86 and all preregistered gates passed. |

## Revalidation

From repository root, with Docker context `orbstack` and the retained image:

```sh
docker --context orbstack image inspect issue-3370-native-mcp-orbstack:20260920-r2
docker --context orbstack run --rm --network none --read-only \
  --mount type=bind,src="$PWD",dst=/workspace,readonly \
  --mount type=bind,src="$PWD/research/integration/issue_3370_host_image_boundary_v1/evidence/formal-05",dst=/evidence \
  --entrypoint /opt/mcp/bin/python issue-3370-native-mcp-orbstack:20260920-r2 \
  /workspace/research/integration/issue_3370_host_image_boundary_v1/audit.py \
  /evidence
```

The image digest and source/runner/auditor hashes are retained in
`evidence/formal-05/source-freeze.json`; `manifest.json` hashes all trial files.
