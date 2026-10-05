# Post-hoc frozen-gate application (not a second formal audit)

After the candidate and raw-only auditor terminated, a read-only PowerShell calculation applied the already-frozen null calibration gate to the auditor-verified Wilson interval and selected the first N grid point meeting the already-frozen lower-bound rule. It did not change `candidate_raw.json`, rerun the candidate, or modify the auditor's output.

```powershell
$r = Get-Content candidate_raw.json -Raw | ConvertFrom-Json
$n = $r.null_control.replicates
$p = $r.null_control.power
$z = 1.959963984540054
$den = 1 + $z*$z/$n
$center = ($p + $z*$z/(2*$n))/$den
$half = $z*[Math]::Sqrt($p*(1-$p)/$n + $z*$z/(4*$n*$n))/$den
$lo = $center - $half
$hi = $center + $half
```

Observed gate: 238/20,000 = .0119; Wilson 95% `[.01048814,.01349933]`; alpha `.0125`; contained: `True`.

Frozen first qualifying grid points: ceiling d=.35 → n=180, 212 recruits/arm; ceiling d=.50 → n=100, 118/arm; floor-skew d=.35 → n=220, 259/arm; floor-skew d=.50 → n=100, 118/arm; middle d=.35 → n=220, 259/arm; middle d=.50 → n=100, 118/arm.

This is post-hoc gate application to raw values already reconstructed by the frozen independent auditor. It is transparently separated from the raw reconstruction itself and is not a candidate/auditor rerun or new inferential result.
