# Issue #6001: WSLc cross-runtime reproduction check

**Disposition: `PASS_RUNTIME_REPRODUCIBILITY` for the already-retained synthetic T0 only.** This is not a new model-shift scientific result and does not close Issue #6001. It checks whether the exact frozen candidate from merged PR #6104 produces the same bytes under this host's WSLc runtime. The original #6001 allocation STOPs and all earlier results remain unchanged.

## H / T / D / C / U

- **H:** Re-running the exact #6104 frozen source in WSLc will reproduce its deterministic raw bytes and pass the existing independent auditor/tests, without provider calls or changing the frozen design.
- **T:** The canonical frozen-source path has one candidate-like run, one independent raw audit, and one unit/mutation-test run in separate `--rm` containers. Before the canonical source-hash gate, a distinct unfrozen exploratory `candidate.py` was also executed and produced the separately retained excluded raw; it is not part of the canonical comparison. WSL 3.0.1.0 / Arch `archlinux` / WSLc 3.0.1.0; Linux/amd64 cached image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. Network `none`, CPU `1`, declared memory `512M`, source bind mount `:ro`, separate writable output directory. The recorded source SHA values match PR #6104; the package does not independently attest the exact time/process at which the source gate was evaluated.
- **D:** `PASS_RUNTIME_REPRODUCIBILITY` is limited to the canonical recorded run: candidate/auditor/test source SHA values match #6104; WSLc raw SHA-256 equals the prior frozen-source repeat (`0cbd75a36215eda262ec1609e25d905d8816e3392e050d210120a6681d688bb6`); independent audit is `PASS_METHOD_SCOPED`, 21 groups, all seven gates true, zero errors; tests 9/9. The execution record reports exit 0 for all three canonical commands. This PASS does not mean there was only one candidate-like execution overall.
- **C:** The fixture is deterministic and the WSLc image digest differs from the image recorded in #6104. Byte equality is a narrow runtime-reproducibility check, not independent replication of the scientific design or validation of the original image. The source was recorded as fetched from current main and byte-checked; no files in #6104 were edited. The report's command/output record is operator-authored; this package contains no engine/process receipts independently authenticating invocation count, source-gate timing, exit codes, or cleanup.
- **U:** No provider/model, GUI, route-effect, live queue, performance, GPU, product, broad model-identity, power, or false-alarm claim. WSL emitted `kernel does not support swap limit capabilities or the cgroup is not mounted`; the accepted memory option is not evidence of enforced memory/swap isolation. The initial exploratory candidate-like execution is confirmed by its generated excluded raw, but its original console/process receipt is not retained; candidate-like work must not be counted as zero. This run neither consumes nor authorizes a provider allocation and does not change either historical STOP.

## Frozen identities and retained outputs

The three source files under `source/` exactly match PR #6104's recorded SHA-256 values:

| File | SHA-256 |
|---|---|
| `source/simulate.py` | `f71282a98a012499403d01f5310090b1ea4981a608365004eccdb7ad210dc593` |
| `source/audit.py` | `84d97c800928cc3257d50dfa70edbfc98cea33c8ddf94c79d3f4f9d3beb2c537` |
| `source/test_detection.py` | `0d8e2f59f8e08f7fea98f4cb212c655a54c1025135697e9069082690ecde1035` |

| Evidence | SHA-256 |
|---|---|
| `evidence/raw-wslc.json` | `0cbd75a36215eda262ec1609e25d905d8816e3392e050d210120a6681d688bb6` |
| `evidence/audit.json` | `4bfabc994c428cb00009d74d6e6e79f150abaf664885db16126dd51bde622453` |
| `evidence/tests-wslc.txt` (committed Git blob, LF, 1,516 bytes) | `4c27e0a97fd966bd896c043aea90538a80ec3adb0748b0e6ed5c2608df0c22e4` |

The raw is 1,958,696 bytes, contains the same 21 scenario-policy groups, 21,000 route outcomes and 420,000 bracketed probe attempts as #6104, and is byte-identical to its retained repeat output. `SHA256SUMS` hashes committed Git blob bytes. On the Windows checkout with `core.autocrlf=true`, `tests-wslc.txt` expands to 1,531 CRLF bytes with SHA-256 `ef09cdb860b3d8977deb03e187d489a1d2268a7318785603d2ee2ecc8205630c`; that is a checkout representation, not a separately preserved or authenticated original console capture. The committed LF blob is the authoritative published artifact. No line-ending reconstruction is presented as recovery of the original capture.

## Exact runner commands

PowerShell invocation (the actual source/output root was `work/issue6001-wslc-replay`; this PR retains byte-identical copies):

```powershell
$src = 'C:/Users/junny/Documents/Codex/2026-09-19/goal-unjuno-agent-interface-github-mcp-6/work/issue6001-wslc-replay/source:/src:ro'
$out = 'C:/Users/junny/Documents/Codex/2026-09-19/goal-unjuno-agent-interface-github-mcp-6/work/issue6001-wslc-replay/output:/out'
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume $src --volume $out --workdir /src $image python -B simulate.py /out/raw-wslc.json
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume $src --volume $out --workdir /src $image python -B audit.py /out/raw-wslc.json
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume $src --volume $out --workdir /src $image python -B -m unittest -v test_detection.py
```

The retained audit was separately emitted to `evidence/audit.json`; all three invocations returned exit code 0. Each `--rm` invocation was one-shot. The local `wslc ps --format json` check after completion showed no live containers.

## Construction failures retained as exclusions

Before the canonical source-hash gate was applied, an exploratory local file named `candidate.py` was mistaken for the #6104 frozen candidate. It was **not** the canonical source (SHA-256 `d71a647d06d42a37f38f5266e7cc9fce1c8849eae9f31c2bbbc00e7206ad5cc3`); its generated raw SHA was `c38b2f9228407c699b63f5a30103b698fb9ea52e1c692bbef908d6f76b67066a`. Both bytes are retained under `evidence/excluded/` solely as an excluded construction misfire; they are not part of the PASS or any scientific claim. The mismatch was caught; the exact #6104 source was then fetched from GitHub main and all three hashes were verified before the canonical WSLc run. Earlier mount probes also showed that Arch `/home/...` paths were not visible through the shared WSLc bridge and an empty named volume did not seed files; those probes produced no canonical raw. The successful path used a Windows absolute `C:/...` read-only bind source as in the repository's WSLc smoke script.

## Reproduction / limitations

The exact repeated raw bytes support only deterministic cross-runtime replay on this WSLc image/host. They do not rehabilitate the historical allocation-01 or allocation-02 STOP, resolve their previously recorded provenance/timing/statistical qualifications, or authorize a successor live/provider allocation. See [Issue #6001](https://github.com/Unjuno/agent-interface/issues/6001) and the immutable [PR #6104](https://github.com/Unjuno/agent-interface/pull/6104).
