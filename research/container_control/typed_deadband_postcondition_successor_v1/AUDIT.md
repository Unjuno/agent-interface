# Independent audit — typed deadband successor v1

The downloaded artifact from Actions run `35442937498` was checked independently of the runner:

```text
jq assertions: PASS
controller logs: 6
press events: 38
guard events: 3
all_key_events_balanced: true
all_terminal_empty: true
stale_repress_total: 0
formal_mechanics_pass: true
```

The audit required three pairs, six decisions per arm, at least one guard event, zero stale represses, balanced key events, and empty terminal input. All assertions passed. The earlier syntax-error run produced no scientific rows and remains a retained construction STOP.