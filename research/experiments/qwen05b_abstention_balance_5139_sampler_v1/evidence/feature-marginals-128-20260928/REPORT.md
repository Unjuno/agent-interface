# #5139 constrained set-sampler marginal feasibility probe

## H / T / D / C / U

- **H:** Matching the four template and four field marginals for the set class is constructible for balanced (4 set rows) and imbalanced (16 set rows) support arms without changing the total 32-row budget or the other class quotas.
- **T:** On synthetic support pools from the prepared #5139 current-main generator, use a separate SHA-256 row rank within each template × field cell. Select one row from each of 16 cells for imbalanced and one row per template/field using a predetermined seed-derived permutation for balanced. Run 128 fixed construction sentinels (1–128); check quota nesting per class and the declared marginal counts.
- **D:** PASS_STRATIFIED_SUPPORT_MARGINAL_FEASIBILITY_ONLY: exit 0; 128/128 sentinel pools passed the per-class nesting and marginal assertions. Both arms have 32 rows. For set, balanced has one row per template and field; imbalanced has four per template and field. Balanced covers 4/16 joint cells; imbalanced covers 16/16. Each source pool has four rows per joint cell.
- **C:** Fixed protocol/generator and synthetic construction sentinels; deterministic same rank rule; selection/audit code in this file does not import the candidate sampler.select. The generator and protocol still construct the input pool, so this is not a fully independent dataset audit. The first version's arm-wide subset assertion failed at seed 1 because yield-class quotas run in the opposite direction; that assertion was invalid. The corrected test checks containment separately for each class. No seed was chosen by output quality.
- **U:** Feasibility only. It does not remove joint-cell or individual-row differences, estimate a causal effect, test model quality, or constitute preregistered randomization inference. The fixed balanced cell permutation leaves joint support content different. No model, CUDA, GPU, Docker, or formal allocation was used.

## Reproduction

Host CPython 3.11.9, local CPU. The exact PowerShell invocation was:

    python $branch 1> $out 2> $err

Here $branch is the GitHub-read-back feature_design_probe.py, $out is the retained result.json stdout capture, and $err is the retained empty stderr capture. Exit code: 0.

## Provenance

Prepared source files (SHA-256):

- protocol.py: 3d324897c9e99abe453ed500c486780243efe9fcff87441197471b5b47d665b6
- sampler.py: 0cdbe3e5b61202ec6ea5bd8810f4734a85141e7a7cbaf22ce886568b0f2c23a6
- make_dataset.py: 2aae4ddfa3e01ec2b1d2c4091a8be901070a3167b86aec9f45e74456e64d876f

The GitHub-read-back script executed locally had SHA-256 85ac657bd0afaf8a0c2636156204821a723c69755c85704892639686b16c05a4. The exact stdout bytes had SHA-256 42e3e0e353c824570c8bf71491f25afa89f9dd30a0d48d5295ee3e79ee160a25; stderr was empty (SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855). The script and JSON result are retained beside this report.

## Disposition

This diagnostic can inform a revised preregistration; it does not amend the frozen #5014 protocol or authorize #5139's formal run. A future comparison must predeclare how to handle the different joint-cell and individual-row support content (or use multiple preregistered support seeds and suitable inference) before examining model outcomes. Pinned-image construction, the complete independent raw-output audit, fresh source/data/model/tokenizer freeze, collision checks, historical sad_cannon disposition, and an exact exclusive GPU/Docker lease remain separate gates.
