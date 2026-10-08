# Construction checks — Issue #5862 T0

Construction-only command:

```powershell
python -B -m unittest research.analysis.robust_recourse_5862_t0_v1.test_t0 -v
```

The current local run is Python 3.12. Construction tests exercise all seven finite stop histories and six mutation controls (10 test methods total). They do not consume a formal allocation and must not be described as empirical recourse or live recovery.

The local Docker Desktop CLI is installed but `docker version --format '{{.Server.Version}}'` did not return within the local command timeout. As permitted by the current research direction, the frozen formal runner uses GitHub-hosted Docker and preserves runner/image/container evidence; it never starts or modifies the local daemon.
