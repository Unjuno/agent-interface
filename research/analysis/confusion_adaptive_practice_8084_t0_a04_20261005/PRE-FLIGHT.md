# A04 pre-formal setup note

The first attempt to invoke the deterministic fixture generator did not start a WSLc process: PowerShell could not open the intended stdout file because the newly created empty `results/` directory had not survived a Git stash/pop. The error was `Could not find a part of the path .../results/fixture-generator.stdout.json`; no generator, candidate, or auditor output was produced by that attempt. The missing directory was then recreated explicitly before fixture generation. This was a host orchestration setup error, not a candidate/auditor outcome.
