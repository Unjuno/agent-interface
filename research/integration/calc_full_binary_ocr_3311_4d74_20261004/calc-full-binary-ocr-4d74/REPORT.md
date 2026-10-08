# G20 full-cell binary OCR integration blocker diagnostic

Disposition REJECT_FULL_BINARY_CANDIDATE; HOLD_INTEGRATION_RECOGNITION. One fixed candidate, no tuning/retries: full cell grayscale threshold130, nearest4x, white20 border, TesseractPSM7 eng numeric whitelist. All original eleven G08-G12 images from G13 copied literally; host-only scoring truth never mounted to candidate.

Candidate ran once in WSLc, exit0. Independent saved-data reader ran once in a separate WSLc process, hashes/crop/clock errors[], exit0. Numeric exact1/5; blank unknown6/6; overall7/11. Errors include899->99 and713->15;43/47/2021 and19/29/551 unavailable.33 OCR attempts3107756292ns. Complete argv/start/end/exit/stdout/stderr/crop hashes and actual crop images retained. Audit process exit0 means custody/scoring completed, not candidate success.

This is a known-image development diagnostic, no heldout/general accuracy claim, no new native GUI/input or model call. Source SHA2562bb3ad8c3b542a52016c7b2e6f29f6c8a527c701b68e234bf19331422452a228. Prior tight-crop/raw/graded outcomes unchanged. The new route fails even before fresh live qualification and is excluded from prospective composed path; do not replace consensus or rerun consumed allocations to obtain a favorable sample.

Candidate command: wslc run --rm --network none --cpus1 --memory512m --user65534:65534 with candidate-input only mounted read-only at /src, fresh out at /out; image sha256:86edd8e13599b0e4e035b5865e4fee340740d349308a2a24a1304aa1cb41dde2 python3 -B /src/candidate.py. Auditor same image/user/network with entire saved data read-only /data and fresh audit-out /audit, python3 -B /data/audit.py. CLI spelling in this prose abbreviates CPU/memory options; actual invocation uses --cpus 1 --memory 512m. Swap-limit warning reported both times. Effective limits not sampled, no memory-enforcement certificate. Physical GPU unnecessary for this CPU OCR diagnostic.

Frozen H/T/D/C/U in PLAN. Full source/input hashes, original candidate output and separate audit retained. Overall #3311/#57/ROADMAP remain incomplete; failure is an integration decision rather than evidence for broad feature expansion.
