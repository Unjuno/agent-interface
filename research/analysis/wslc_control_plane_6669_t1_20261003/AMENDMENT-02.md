# Amendment 02: no-pressure stop comparator

After the amended 640 MiB pressure repeat, the control plane returned success for info/list/stats/logs/stop/remove and verified absence. The stop command took 10.159 seconds for --time 10; list showed Exited (137), so graceful shutdown is unproven. Before interpreting causality, run a matched no-pressure control in the same 1 GiB SDK session, same pinned image, --memory 768M, --cpus 1, network none, 32 MiB touched then 60 second hold. Sample logs and stop --time 10; verify status and remove. No concurrent candidate. See issue #6669 amendment 3.
