# R01 result

Status: `HOLD_TRANSPORT_IDENTITY`.

The WSL host could run an authenticated TCP-only Xvfb on display `:88`; a
python-xlib client connected through `127.0.0.1:199`. The shared
`/tmp/.X11-unix` remained mode 0777 with its existing WSLg X0 socket and was
not modified.

The frozen normal-mode XRes test reached the server and started its exact
owned XTEST child. It then failed at `client_is_connected` with
`missing or ambiguous X-Resource process identity`. The run had not yet
recorded the held-key readback or confirmed the disconnect, so it is not a
queue-order result. Cleanup killed only the test's child and independently
verified final keys A/B up. The server used X.Org Xvfb `2:21.1.12-1ubuntu1.8`,
release 12101011, XRes 1.2 and XTEST 2.2. Its SHA-256 is retained in
`runs/normal/result.json`.

The optimized attempt was not run: the normal attempt failed a transport
identity prerequisite before the selected discriminator, and `-O` cannot
change whether XRes supplies a unique local-client PID over TCP. Repeating
the same host transport would not advance the evidence. The next isolated
attempt uses a Docker container's private Unix socket, where local XRes PID
identity is available, without altering WSLg state.

No physical input, target GUI, provider, Docker container, or WSLg socket was
used in this WSL attempt. This packet does not establish queue drainage,
release reliability, task success, or live MAP01.
