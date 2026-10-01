# Evidence index — Issue #4619

Each `seed-N.tar.gz.b64` is base64 of the gzip-compressed tar archive for that seed. It preserves the raw trained package, independently auditable expected rows/predictions/labels, both isolated loader results, corruption-control byte proof and container stdout/stderr. Verify SHA-256 of the decoded `.tar.gz` before extraction.

PowerShell recovery:
```powershell
$b = [Convert]::FromBase64String([IO.File]::ReadAllText("seed-913000.tar.gz.b64"))
[IO.File]::WriteAllBytes("seed-913000.tar.gz", $b)
(Get-FileHash -Algorithm SHA256 "seed-913000.tar.gz").Hash.ToLower()
tar.exe -xzf seed-913000.tar.gz
```

| Seed | Archive SHA-256 | Gzip bytes | Archived evidence |
|---:|---|---:|---|
| 913000 | 268f1445d929a363ae5762f21bbde1dfb278ab8ef5755c692c9e87c902d4e2ec | 937241 | [archive](seed-913000.tar.gz.b64) |
| 913100 | ab344e7ae819c23d231a41440226ba21b6818844c6574059f7099a643802a011 | 937456 | [archive](seed-913100.tar.gz.b64) |
| 913200 | c0cf83587c150f8927fbf1772cf41d2b54623f15eaf7aac304819b5261d3678c | 937404 | [archive](seed-913200.tar.gz.b64) |
| 913300 | 660af95f1d9b6a19758724ce4adceb69493ef6ec7320cd4cac58bb5c4bf1e588 | 937532 | [archive](seed-913300.tar.gz.b64) |
| 913400 | fa75c67021ed32bbd393a0fc911fafb015bf56c92131fb041f06c23a82be80cf | 937006 | [archive](seed-913400.tar.gz.b64) |
| 913500 | babbe345dfaaa982fb3bc4d3a5391391ae04124fcfde8e01bd642745150283dc | 937431 | [archive](seed-913500.tar.gz.b64) |
| 913600 | 511f81e95e0e46dac2a8d4deb1efbea6134718d65079b146eb5cab8f5b3859d8 | 937753 | [archive](seed-913600.tar.gz.b64) |
| 913700 | 00d0ad5c5e6910daf39f975b225644836a1c174f2d9246add8ba54d23a17113a | 937075 | [archive](seed-913700.tar.gz.b64) |
| 913800 | c9376cf6c318887bccdb746b4a5c3bf1ba76fd7f6ca58fc41d43040bb5ca6768 | 937971 | [archive](seed-913800.tar.gz.b64) |
| 913900 | 2982395991c2e56c617ad760f2011c1f8396b4ce9f1ffe799a6c67ccad7a4478 | 937660 | [archive](seed-913900.tar.gz.b64) |

Raw `FORMAL_INVOCATION.json` records the one orchestration, exact command, timestamps and stdout/stderr hashes for all 30 container calls. `AUDIT.json` is the separate audit decision and per-role summaries. Frozen source and contract identities are in the sibling `FREEZE.json` / `FREEZE.sha256`.
