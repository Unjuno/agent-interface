# Executed commands and deviations

All commands were local. No image was pulled, package installed, remote
workflow run, model/provider called, or GUI input submitted.

## Obstac probe image

```sh
docker image inspect issue-3300-obstac-probe:v1 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src=<historical-source-tree>,dst=/repo,readonly \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint python issue-3300-obstac-probe:v1 \
  -c 'import session_v4'
```

Image ID `sha256:57ad79ade1fc4d961017fb46575af305b12dc552fa54ea9369c32733cc2017f9`,
linux/arm64. STOP before route import completed: `ModuleNotFoundError: No
module named 'PIL'`. No install or replacement image was attempted in this
probe.

## Historical route startup instance

The actual startup-only command was:

```sh
printf '%s\n' '{"op":"finish"}' | docker run --rm -i --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=128m \
  --mount type=bind,src=<historical-source-tree>,dst=/repo,readonly \
  --mount type=bind,src=<evidence-output>,dst=/evidence \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint /usr/bin/xvfb-run issue-2849-task1-runtime:v3-20260921 \
  -a /usr/bin/python3 /repo/research/live_control/session_v4.py \
  --app chromium --seed 992922 --out /evidence/ready-gate-01 \
  --chromium /usr/bin/chromium
```

This invocation produced no output in the initial 30-second wait. The same
container remained alive with only `xvfb-run` and `Xvfb`; its output directory
did not yet exist. `xdpyinfo -display :99` then independently returned display
metadata. One `docker kill --signal=USR1 <container-id>` was sent to release
the wrapper's documented Xvfb-ready wait. The session then emitted `ready`,
one initial observation, processed the already-piped `finish`, and exited;
the `--rm` container disappeared and wrote the evidence bundle. This signal
intervention is the reason for the HOLD disposition. It is not hidden or
relabelled as a clean run.

The output was not a task result. The screenshot shows `about:blank`; the
`finish` evaluator found no submitted output file, as expected with zero task
commands. The setup-only allocation/output identity is consumed.

## Independent audit CI

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src=<package-tree>,dst=/repo,readonly \
  --workdir /repo/research/integration/golden_ipc_source_closure_2922_v1 \
  --entrypoint python issue-3300-obstac-probe:v1 -m unittest -v test_audit
```

Result after recording the no-GUI and direct-Xvfb rungs: 10/10 tests passed.
This consists of the baseline, five historical-event mutation controls, two
import-only contract tests, and two direct-Xvfb contract tests. The raw-only
audit checks both four-event logs, eight source files, image/source receipts,
and both later result contracts. No experiment output was regenerated for
this audit.

## Direct-Xvfb pre-task ready rung

Allocation `issue2922-direct-xvfb-ready-20260927-r1`; seed `992924`;
namespace `ready-gate-03`. The container invoked the retained script directly:

```sh
docker run --rm -i --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=128m \
  --mount type=bind,src=<package>/source_snapshot/research,dst=/repo/research,readonly \
  --mount type=bind,src=<fresh-evidence-parent>,dst=/evidence \
  --mount type=bind,src=<package>/ready_gate_03/run-direct-xvfb.sh,dst=/experiment/run.sh,readonly \
  --workdir /repo/research/live_control \
  --env PYTHONPATH=/repo/research/live_control:/repo/research/observation_gating \
  --entrypoint /bin/bash issue-2849-task1-runtime:v3-20260921 /experiment/run.sh
```

Exit code 0; stdout contains `X_DISPLAY_READY` followed by the four retained
events. The first attempted allocation seed 992923 stopped before session
startup because its output directory had been pre-created; see
`READY_GATE_03_SETUP_STOP.txt`. Both seed identities are consumed.

## Host-side GET-handler component probe

One host Python 3.14.5 invocation AST-extracted only the exact
`fixture_server` function from the hash-pinned `gui_suite.py`, started its
loopback server, issued one HTTP GET, and checked that the response contained
`AI FORM READY` while the fresh `submitted.txt` path remained absent before
and after. It returned HTTP 200 / 187 bytes / `text/html; charset=utf-8` and
exit 0. No POST was sent. This did not import the full GUI suite, run in a
container, or launch `session_v4`; see `FIXTURE_GET_HOST_COMPONENT.md` and
`FIXTURE_GET_HOST_RESULT.json`. This component result is not evidence that the
integrated session endpoint was requested.

Executed command (from the historical source worktree):

```sh
python3 -B -c 'import ast,http.server,json,pathlib,tempfile,threading,urllib.request; src=pathlib.Path("research/observation_gating/gui_suite.py"); tree=ast.parse(src.read_text()); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="fixture_server"); ns={"http":http,"threading":threading,"Path":pathlib.Path}; exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),"exec"),ns); d=tempfile.TemporaryDirectory(); output=pathlib.Path(d.name)/"submitted.txt"; server=ns["fixture_server"](output); result={"source":str(src),"source_sha256":__import__("hashlib").sha256(src.read_bytes()).hexdigest(),"python":__import__("sys").version.split()[0],"method":"GET","endpoint":"http://127.0.0.1:%d/"%server.server_port,"output_exists_before":output.exists()};
try:
 response=urllib.request.urlopen(result["endpoint"],timeout=3); body=response.read(); result.update({"status":response.status,"content_type":response.headers.get("Content-Type"),"body_contains_ready":b"AI FORM READY" in body,"body_bytes":len(body),"output_exists_after":output.exists(),"disposition":"PASS_GET_HANDLER_NO_OUTPUT_MUTATION" if response.status==200 and b"AI FORM READY" in body and not output.exists() else "FAIL"})
finally:
 server.shutdown();server.server_close();d.cleanup()
print(json.dumps(result,sort_keys=True)); raise SystemExit(result["disposition"]!="PASS_GET_HANDLER_NO_OUTPUT_MUTATION")'
```
