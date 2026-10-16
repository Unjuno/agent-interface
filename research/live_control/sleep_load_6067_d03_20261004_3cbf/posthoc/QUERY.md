# Saved raw extraction

Read-only descriptors; producer and official saved-auditor primary rules unchanged. The first verbose extraction exceeded tool output limits and was not parsed or retained as a result; the compact extraction below read all12cell files and preserved all192 rows.

```sh
/usr/bin/jq -c -s '[.[] | select(has("rows")) | {id,arm,pair,children:[.children[]|{exit_code,cpu_ns:.finish.cpu_ns}],rows:[.rows[] | [(.return_ns-.due_ns),.requested_ns,(.cpu_end_ns-.cpu_start_ns),(.post.cpu.nr_throttled-.pre.cpu.nr_throttled),(.post.cpu.throttled_usec-.pre.cpu.throttled_usec),.post.schedstat.available,.post.schedstats_enabled.available]],first_cpu:.rows[0].pre.cpu,last_cpu:.rows[-1].post.cpu}]' native-raw/*.json
```

Each row tuple is [lateness_ns,requested_ns,process_cpu_bracket_ns,leaf_throttle_count_delta,leaf_throttled_usec_delta,schedstat_available,schedstats_enabled_available]. Median is sorted middle or mean of two middle values; counts >10ms and maximums are POSTHOC only. Brackets include surrounding telemetry overhead and counters shared by sibling burners. No exact syscall/descheduling attribution.
