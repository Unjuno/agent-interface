# GPU supervisor transfer break-even — allocation 07

Fresh one-shot successor to #5882 allocation-06, which stopped before candidate launch because disk free capacity decreased. No a06 candidate/CUDA/audit was run. This package uses fresh seed 49720261007 and independent outputs.

Start with PREREGISTRATION.md and FREEZE.json. The synthetic workload compares transfer-inclusive CPU/CUDA hint cost; the CPU final gate remains authoritative. This is a microbenchmark, not model inference or an end-to-end Agent Interface result.

Allocation: GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-07  
Issue: #6308  
Branch: research/gpu-supervisor-transfer-breakeven-4972-a07-20261002  
Evidence path: research/analysis/gpu_supervisor_transfer_breakeven_4972_a07_20261002/
