# Formal allocation 01 — STOP

Issue #3827, allocation `issue3827-obstac-json-probe-orbstack-01`, preregistration/source commit `53ec787056ef8262eb2f6b381eb9585fc30e89a1`.

## Result

Exactly one request was submitted through the frozen Obstac/OrbStack allocation. Ollama returned HTTP **400** with the exact body:

```json
{"error":"{\"error\":{\"code\":400,\"message\":\"Failed to load image or audio file\",\"type\":\"invalid_request_error\"}}"}
```

The response body SHA-256 is `55cddbed42e08243ba32e2805d0234886b969f44368c7bccf77dd1458a2dafad`. Model digest before/after matched the freeze; response headers, body and elapsed time (2,303,704,041 ns) were retained. There were **0 completed model responses**, so this is not an answer-quality FAIL or PASS. Classification: `STOP_OBSTAC_OR_MODEL_TRANSPORT`. No retry or fallback was issued.

## Audit

The independent network-none container audit returned exit 2 with decision `STOP_OBSTAC_OR_MODEL_TRANSPORT`. Source hashes, preregistration hash, freeze, OBSTAC provenance variables, image/request/response byte links, response-body hash, model digest, one-request count, and no-action gates all passed. Only HTTP-200/answer gates failed, as expected for the received HTTP 400; no parsed model answer exists. The PNG independently passes macOS `sips` decoding, PNG chunk CRC, and zlib decompression/decoded-dimension checks. Those checks do not establish why the local model runtime rejected it.

## Retained formal bytes

- request: SHA-256 `ffe5bd76570e6ac788920ca85f6088f92a8f00c590b98f81f78c9f0eac87dd98`
- response envelope: `4fa8f4ec0903ec25e58ec35638331bdd0ad2c86eec5c01b86cb8bf31bc729357`
- runner result: `91243ff9d76bbaba544dfc9d3c928d7968ea315f6b845d3de9dcb4e8e045ef67`
- image: `333a60fd9a07bdccc8703c0dd2ecb0726dbfc74351f011851c87ab42c9ca5719`
- bridge summary: `6d678af2a119319209c811ab2deebc9666534f3756f2380eb0e010b5aa9bcba8`
- Obstac execution record: `edc37da236e552c5601acfe041cde9cbbafe5c9a89152cac2314d216441b9176`
- host bridge log: `afa4df22ce09c9f776e4daf5e7abb643a5427c2004a8c4ce58113ed6b8b61701`
- independent audit: `d0ec5dd9936bdc3804357eef37e5bd09d40fa8be803353c04fe37fe5a55a2d51`

No conclusion about epoch-aware composition, task recovery, or model visual status ability follows. The additive evidence is for successor-agent diagnosis only; any new input codec/model/API probe requires a separately preregistered allocation.
