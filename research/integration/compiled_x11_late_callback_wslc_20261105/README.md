# Compiled X11 late-callback WSLc construction check — 2026-11-05

## Question and scope

Does the current guarded-X11 adapter composition preserve a returned neutral
release receipt and the unresolved effect when its synchronous input callback
returns after the graph's method deadline, without requesting a follow-up
observation or dispatching another input?

This is a local software-construction regression check. It uses the in-memory
`Bridge` fixture and injected delay in
`runtime.guarded_x11_v1.test_compiled.CompiledX11Tests`; it does not open an X
server, GUI application, model/provider, WSLc GUI target, or MAP01. It establishes
no physical release timing, OS-level preemption, application effect, recovery
success, live WSLc portability of the GUI path, or efficiency result.

## Frozen execution conditions

- Source revision: `8080f4c0a98aa99d9a35f3edb7c6cb0180994107`.
- WSLc: `3.0.3.0`.
- Image: local immutable image ID
  `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`
  (`agent-interface-calc-ocr:20261030-a02` at inspection). The image was already
  present; no image pull occurred. Its Node entrypoint was overridden to
  `python3` for the test invocation.
- Source bind: current checkout mounted at `/src:ro`.
- Network: none; CPU request: 1; container removed with `--rm`.
- Command:

  ```text
  wslc.exe run --rm --pull never --network none --cpus 1 --volume "<checkout>:/src:ro" --workdir /src --entrypoint python3 sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25 -B -m unittest -v runtime.guarded_x11_v1.test_compiled.CompiledX11Tests.test_late_input_callback_retains_release_and_effect_without_continuation
  ```

## Attempts and disposition

1. **Construction error, exit 1:** the first invocation used the cached
   `agent-interface-xvfb-mcp:late-input-r19` image without overriding its Node
   entrypoint. Node tried to load `/src/python`. Raw command, stdout, stderr and
   exit code are retained in this directory. This was not counted as a test
   failure or retried with that command.
2. **Dependency preflight, exit 1:** the guide's cached
   `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
   image was checked for Pillow, required by the adapter fixture. Pillow was
   absent; no dependencies were downloaded. The exact command and streams are
   retained as `pillow-preflight-*`.
3. **Regression test, PASS, exit 0:** the pre-existing local Calc OCR image was
   inspected, found to contain the Python environment, and its entrypoint was
   explicitly overridden. The single targeted test passed in 0.401 s. Exact
   command, stdout, stderr and exit code are in `attempt-02/`.

The post-run `wslc container list --all` showed only containers created four
days earlier; the `--rm` invocation left no new container visible. The host's
Docker Desktop daemon independently returned version `29.8.1`; this check used
WSLc, not Docker Engine.

## Result

PASS for this one constructed callback ordering: method budget 200 ms, injected
callback delay 400 ms, one dispatch, one retained observation, a retained raw
release array with `verified=true` and empty key/button sets, `SAFE_YIELD /
budget_exhausted`, and the `enter` effect left pending. No effect verifier or
second input ran.

The same focused test and the combined core-graph/X11-adapter suite passed
locally under normal Python and `python -O` (83 tests each; see the local run
output in the task record). These runs and this WSLc test are correlated checks
of synthetic software behavior, not independent live samples.

`manifest.txt` records the source/image/tool identities and source hashes.
Failed construction attempts remain preserved and are not silently excluded.
