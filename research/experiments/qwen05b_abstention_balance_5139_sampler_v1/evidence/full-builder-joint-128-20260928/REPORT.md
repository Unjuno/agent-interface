# #5139 full-builder joint-matched construction probe

## H / T / D / C / U

- **H:** An alternate selector injected at the existing dataset-builder boundary can produce complete 32-row balanced and imbalanced support arms whose set-class template×field joint composition matches, while preserving the held-out rows across support seeds.
- **T:** Fetch exact prepared branch source files (protocol.py, sampler.py, make_dataset.py), patch only make_dataset.select_support in memory to a separately implemented joint-cell selector, and call the actual make_dataset.build for 128 synthetic support-seed sentinels (1–128) using fixed formal-seed fixture 990000017. Independently reconstruct exact selected IDs/content with a second implementation that imports neither the candidate selector nor candidate rank function; audit a retained full synthetic JSON document in a separate Python process.
- **D:** PASS_FULL_BUILDER_JOINT_MATCHED_CONSTRUCTION_ONLY. All 128 full builds passed the independent in-memory audit. Each arm had 32 rows; set supports used the same four cells, with one versus four rows/cell. The held-out digest was identical across all 128 support seeds. A separate raw-only audit of the retained 803,927-byte dataset exited 0 with errors=[]; raw SHA-256 849d99c4324e62fe053b8a825596e4647f4ab77d9c68e33d1dc7922df843304c.
- **C:** Same fetched protocol/generator, same fixed held-out/formal-seed sentinel, same deterministic class rank, and distinct predetermined four-cell matching derived from each support seed. The independent auditor duplicates the schedule/rank contract and verifies exact support IDs and full row content. No outcome or quality-based seed choice.
- **U:** The candidate selector was injected at runtime; make_dataset.py, its default SHA-ranked sampler, and any frozen predecessor remain unchanged. The data are synthetic. This is not a container test, formal allocation, model/LoRA result, causal estimate, or full independent task-effect audit. The matched support still compares distinct rows and 1-vs-4 row multiplicity within each selected cell. The source branch is based on e74f0ba20f7b7476ab9b3e62f8533ec53d216daf; at intake current main was 50e542eda5bcb6a5ddbc62c7400ec36b0dbcc8c2, so this preparation branch requires a fresh current-main freeze before formal use.

## Harness STOP retained

Two first runner attempts stopped before any builder execution with ModuleNotFoundError because the script was outside the fetched package's import path; the first path fix did not match Windows newline encoding. Exact disposition is in FIRST_ATTEMPT_SETUP_STOP.txt. After locating the package ancestor explicitly, the exact GitHub-read-back runner completed 128/128 and the separate auditor passed. No formal allocation was consumed.

## Exact source identity

Fetched from research/qwen5139-current-main-prep-20260928:

- protocol.py Git blob d5073b51d38fb9f649ed799eafcaa5e0eda5fc18; SHA-256 3d324897c9e99abe453ed500c486780243efe9fcff87441197471b5b47d665b6
- sampler.py Git blob 11286aecaac16ec5effb9b3ed5924f49c0a39d7e; SHA-256 0cdbe3e5b61202ec6ea5bd8810f4734a85141e7a7cbaf22ce886568b0f2c23a6
- make_dataset.py Git blob bae077ce166fe0f6415d02eb42196e32c3c462d6; SHA-256 2aae4ddfa3e01ec2b1d2c4091a8be901070a3167b86aec9f45e74456e64d876f

Host CPython 3.11.9, Windows PowerShell, CPU only. GitHub-read-back script SHA-256s: runner 8afea5d43574475a815e294fda951bc325cbccc89a5408b67d9aa38e594ecb4b; independent audit 879f54ccc93360215b7a3fc31f90d22dcf58d94007c8062556716889760cf33b; candidate selector d80e78583fee6a0382bb9810f1816ba72a0c6d1b00813d38cec8a2f584d111dd; separate raw audit CLI c0909ca929bb196b794b949c4e1c3133dee57699903c26ee49df0b707e690b0a. The retained result.json SHA-256 is 5e2fbb37f5b9185a657a0a5d53411bf4ca2f131b46e62321642af544662eb9b7; rerun stdout SHA-256 is b799652ce6b17af27aa490392c6e8a56cf47893f3dffd3035adc8e997a423a45. Their JSON values match after line-ending normalization. Empty runner stderr SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

The full raw JSON is retained losslessly as deterministic gzip/base64 for a compact GitHub path. Raw SHA-256 is 849d99c4324e62fe053b8a825596e4647f4ab77d9c68e33d1dc7922df843304c (803,927 bytes); gzip SHA-256 fb1c64788af538be6ebf98c94099c1778658dd238effe36f7323bc318e68c986 (46,620 bytes); encoded file SHA-256 54f8e745f1ae7f2eddcdaac58649bbef4a33c76faf498f540dc7ad32ec719b84.

## Reproduction

From repository root:

    python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/run_full_builder_probe.py > research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/result.json 2> research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/stderr.txt
    python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/restore_raw.py
    python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/audit_saved_dataset.py research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/full-builder-joint-128-20260928/construction_sentinel_1.json

The first command exits 0 and regenerates the retained raw JSON. The second decodes the compressed fixture. The third is a separate raw-only process and exits 0 with errors=[].

## Allocation and resource disposition

No model weights, CUDA context, GPU, Docker container, training job, adapter, or formal seed allocation was opened or used. #5139 remains unleased; the #5085 queue reports the unrelated OrbStack Docker client/container unresolved and no transfer to this allocation. This experiment does not satisfy the pinned-image construction, fresh main/model/tokenizer/source freeze, output/seed collision review, historical sad_cannon attribution disposition, or exclusive GPU/Docker lease. Do not use the formal-seed fixture or sentinel support seeds as allocation seeds.
