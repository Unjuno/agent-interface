# Retained native response sizes and existing lossless references

The current compact receipt path already deduplicates identical observation
objects using local JSON references. Before changing presentation further,
native_response_size_v1.py expanded every receipt in two retained primary-use
traces and compared it to its archived source JSON and exact source SHA256.
All reconstructed native_result objects matched. No runtime or frozen artifact
was modified by this measurement.

| Retained trace | Returned text UTF-8 bytes | Text with receipts expanded | Existing bytes saved |
| --- | ---: | ---: | ---: |
| native-calc-visual-finish-01 | 25,630 | 27,848 | 2,218 |
| native-combined-roundtrip-01 | 18,816 | 19,933 | 1,117 |

Both sides use the adapter's actual JSON serialization (including its escaping
and spacing); the script checks that it reproduces the original text exactly.
The totals include status/start context and all returned text in each trace.
PNG payloads are separate blocks; report.json also records decoded PNG sizes and
raw relay-line lengths. Base64 wire length is NOT model image-token usage.

This measures an existing representation, not a newly implemented reduction.
It does not demonstrate tokenizer savings, inference cost, faster reasoning or
equal model utility. The previous primary-use orchestration sometimes presented
selected fields while retaining the full response, so total adapter text is not
proof of the actual text seen by the model. Actual host input/usage accounting
remains necessary before a token-efficiency claim.

Preserve task goal, exact source/image references, continuation, action/feedback/
evaluation/cleanup distinctions, failure details and recovery identity in future
experiments. Field deletion cannot be justified by smaller byte counts alone.
The earlier 104-second inter-call gap is not explained by this measurement.

Reproduce from the repository root:

```sh
python research/live_control/native_response_size_v1.py runtime/results/native-calc-visual-finish-01 runtime/results/native-combined-roundtrip-01
```

The reader fails on missing/mismatched source artifacts or unreconstructable
references rather than treating them as successful compression. report.json
retains trace hashes and per-response numbers. No GUI, sensor, model or container
was launched for this analysis.
