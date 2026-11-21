# Current-main loopback TCP Xvfb queue-recheck R01

The earlier WSL real-X recheck was blocked because Xvfb's default Unix
listener requires `/tmp/.X11-unix` mode 1777, while WSLg owns an X0 socket in
that directory at mode 0777. This packet tests the supported alternative
transport without changing that shared directory: an owned Xvfb on display
`:88`, TCP only, loopback client `127.0.0.1:88`, and a temporary MIT-MAGIC-
COOKIE authority file. The server uses `-auth`; it does not use `-ac`.

The existing XRes held-key disconnect test sends one delayed synthetic XTEST
KeyPress. It independently reads the held key, terminates the test owner,
confirms XRes disconnection, releases the first key from an independent client,
then observes the delayed key after the 8.5 s horizon. Its unittest PASS means
required observations and cleanup completed; the `late_keypress_observed`
field is the evidence about queue drainage and must be interpreted separately.

Two finite attempts are frozen: normal Python and optimized `-O`, one each.
The runner owns only its exact Xvfb child and temporary auth directory.

Run from the repository root in Ubuntu WSL:

```sh
sh research/integration/standard_mcp_task_ledger_57_v1/current_main_xvfb_tcp_queue_recheck_20261121_r01/run_probe.sh normal
sh research/integration/standard_mcp_task_ledger_57_v1/current_main_xvfb_tcp_queue_recheck_20261121_r01/run_probe.sh optimized
```

This remains synthetic Xvfb evidence, not physical input, standard MCP
recovery, live GUI task effect, provider economics, or reliability.
