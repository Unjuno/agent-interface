# Setup attempt 01 — output directory missing

The first two test invocations did not reach unittest discovery or execute a case. PowerShell reported `Could not find a part of the path` for package `results/` log files because the package directory had not persisted when only an empty directory was created. No scientific outcome was produced. The tracked README was added first, the directory then persisted, and the six recorded invocations in `results/` ran afterward. This setup failure is retained without relabeling it as a test result.
