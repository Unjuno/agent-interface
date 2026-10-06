# Lossless evidence archive

Concatenate `EVIDENCE.b64.part-00` through `EVIDENCE.b64.part-08` in numeric order, base64-decode, and verify SHA-256:

`3d87ee44e14c5ebfb84759c9f9031bda5fc08461d45ae5a02a98be80918f579a`

Expected decoded size: 360664 bytes. The resulting file is `EVIDENCE.tar.xz`; extract it with an XZ-capable tar implementation. It contains the exact executed candidate/auditor/control source, frozen plan/environment, 90-row RAW.jsonl, RESULT, process stdout/stderr/exit receipts, AUDIT, CONTROLS and an internal SHA256SUMS.

Part SHA-256 values:
- 00 18994e92fc60c50da07c711f4427726866855ad260848a81836e79c9c1fd4d4f
- 01 160fad0c7380817628ef3b7c19e091a7a6178a8af82aee0e8d97688cfc5cd429
- 02 b735488c06e22c1b2e5e2ddf7586ae875f89dbbb469f2afdefac116ab77384c5
- 03 3b06f4f9669d378bbf0d2c116ee8baff6f7e6c609cec527487c54a4dcaab24b3
- 04 1e58a487e6dc043b4391dc2793a6cb2e7c6dd03c1bb98864292f14712b51b3dc
- 05 59cd7454a2f3fcc3ff56505c5313aac0fab4c29d74240f97d2225d1fb1a94cf9
- 06 5d96882a54e0dc23b15ed804f9a7343ea171625d82b5107b50ead20f9650fcc8
- 07 8571e546e4749508368b6ac3591a0a2c8f280532459aa4109630d7bf7b5f1a45
- 08 be06ad1a6bf94c9182a728965699c2f13fc08fe7a314be9ab02445a1e98a8945
