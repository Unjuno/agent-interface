# Portable unified runtime zipapp v1

This package builds one deterministic `agent-interface-runtime.pyz` containing the promoted execution modules only:

- `runtime/core_v1`;
- `runtime/selector_v1`;
- `runtime/cli_v1`;
- X11, Win32 and Quartz promoted backend/session modules.

The archive contains no tests, fixtures, research tree or retained evidence. It is built from exact committed Git blob bytes with fixed ZIP timestamps/mode/order, so Windows checkout newline conversion cannot change the artifact.

## Build from the current checkout

From the repository root, choose a new output directory:

```sh
python -m runtime.distribution_v2.build \
  --out results-local/my-runtime/agent-interface-runtime.pyz \
  --manifest results-local/my-runtime/manifest.json \
  --sums results-local/my-runtime/sha256.txt
```

The builder resolves committed `HEAD` once when the source has `.git`, then reads
every included source file from that object ID even if the branch moves during
the build. Uncommitted source edits are not packaged. The manifest and internal
`BUILD.json` record `source_revision` and each included source file's digest.
This revision identifies the included files, not uncommitted builder settings.
For a source directory without Git, `source_revision` is null and the per-file
hashes describe the files read; no commit pin is claimed. A failed Git lookup
does not fall back to working files. Keep the manifest and checksum beside the
executable. This is a local build, not publication of a GitHub Release.

For a Windows-managed checkout, run the builder with Windows Python/Git, then
run the resulting `.pyz` with WSL Python for Linux/X11. Linux Git cannot resolve
a worktree `.git` file containing a Windows drive path. A native Linux checkout
can build and run entirely in Linux. The built archive needs Python and the
selected backend dependencies; it does not need a repository checkout or Git.

Inspect the packaged commands before supplying target mappings or programs:

```sh
python agent-interface-runtime.pyz observe --help
python agent-interface-runtime.pyz dispatch --help
python agent-interface-runtime.pyz review --help
```

Usage:

```bash
python agent-interface-runtime.pyz doctor
python agent-interface-runtime.pyz dispatch \
  --program program.json \
  --targets targets.json \
  --current-observation-seq 7 \
  --current-binding-revision 3
```

Requirements:
- Python 3.12+;
- Linux/X11: `python-xlib` plus a usable `DISPLAY`;
- Windows: promoted Win32 backend, explicit HWND targets;
- macOS: promoted Quartz backend, explicit PID targets, Accessibility + Screen Recording permissions;
- Wayland-only Linux: not promoted and fails closed.

The archive does not discover targets or request permissions automatically.


For an explicit X11 target, return the capture and its image in one invocation:

```sh
python agent-interface-runtime.pyz observe --targets targets.json --target fixture \
  --frame window_client --region 0 0 400 180 --capture-directory images \
  --review --compact > review.json
```

An explicit dispatch can likewise add `--capture-directory images --review
--compact`; include an `observe` operation in the supplied program if it should
return an image. The caller still supplies the program's current source, binding
and lease; these options do not generate or renew them. The result uses the last
capture in execution order and does not perform an extra capture or input replay.

`--compact` requires `--review` on live commands. It uses reversible local event
references only when their JSON is smaller; otherwise the original receipt view
is returned. This is not a guarantee of model-token, cost or latency savings.

To review a retained **raw** result instead, omit `--review` during the initial
command and later use `review --report observation.json --run-directory .`.
That command also supports `--compact` and `--report -` for raw JSON on stdin.
An already returned review envelope is ready for the host to consume; it is not
another raw result to pass through the review command.

`targets.json` maps the caller's target name to its X11 window ID. Select the
intended display with `--display` on observe when necessary. PNG capture requires
Pillow in addition to python-xlib. Review needs only the Python standard library
and does not connect to a display. Its image block contains base64 PNG data for
the host to forward as an image input; do not paste it as model-visible text.
Check both the retained receipt status and image_status: successful image
presentation does not mean the application task or cleanup succeeded.

An action capture may precede the application's redraw even when a saved effect
is already correct. The existing X11 `wait_update` is a fixed delay, not a redraw
confirmation. Its `execution.waits` records backend wait intervals, not time until
the model can use the screen. If the image is incomplete, the agent can choose
one new read-only `observe`; it must not infer that the earlier input needs replay.

On WSL, filesystem and abstract X11 sockets may coexist. For owned Xvfb tests,
verify the display is unused before launch and verify the connected screen;
do not assume automatic display-number allocation identifies the intended server.
The actual zipapp route is recorded in [the retained portable run](https://github.com/Unjuno/agent-interface/blob/873ecdafd/runtime/results/public-portable-review-01/README.md).
