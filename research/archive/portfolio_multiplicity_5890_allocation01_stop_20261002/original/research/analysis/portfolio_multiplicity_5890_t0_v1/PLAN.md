# Allocation 01 — frozen source bundle

Base main 5865c5e74842b5bba6a6291e141afae75ca4a147. Allocation PORTFOLIO-MULTIPLICITY-5890-T0-20261001-01. This is a host-only deterministic method test; see Issue #5890 comment #5927439711 for H/T/D/C/U and exact decision gates.

Candidate: runner.ps1. Independent raw-only auditor: audit.ps1. Both use only PowerShell/.NET standard libraries and write no files. Candidate stdout is a JSON envelope containing gzip-base64 raw bytes and exact raw/gzip SHA-256. Run the auditor in a separate pwsh process and provide only gzip-base64 via stdin.

Protocol: 32 portfolios ×13 rows =416; seed 58901001; per-portfolio type schedule is embedded in both sources. Null p-values are discrete super-uniform integers [1,1000000]/1000000. Alternative p-values are floor(U^5*999999)+1. There are 224 eligible tests. Global alpha spend is .05/[i(i+1)] in registered order; completion permutation is not decision order. No time-performance claim.
