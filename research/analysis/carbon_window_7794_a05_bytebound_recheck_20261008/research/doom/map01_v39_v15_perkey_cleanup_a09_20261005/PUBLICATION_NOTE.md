# Public package projection note

Two captured command-output fields contained machine-local absolute paths. This public rescue copy replaces only those paths in `RUN.json` and `results/candidate.stdout.log` with stable placeholders; the candidate result JSON, test output, source files, run identifiers, classifications, and outcome fields are unchanged. The original evidence package remains preserved in the closed predecessor PR's history.

Original SHA-256 values before path normalization:
- `RUN.json`: `fe42d9d720174b1eaf4e6b9857ed541a1e30da8dd10edb2c9b842cb4fc933ec2`
- `results/candidate.stdout.log`: `1d76dcea6263e107ebec2a2e0b8347fc71aa571263da154adfb0ade5468632f6`

The package manifest is regenerated for the normalized public files. No experiment or candidate was rerun.
