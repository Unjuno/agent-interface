# Capture-path stop

The 9-test host construction suite passed. Before candidate launch, shell output redirection failed because `results/host-run-04/` did not yet exist (`zsh: no such file or directory: results/host-run-04/raw.json`). The shell did not invoke the candidate; candidate=0, audit=0. This is a capture-setup failure, not a scientific result. The next host capture uses a fresh `host-run-05` directory.
