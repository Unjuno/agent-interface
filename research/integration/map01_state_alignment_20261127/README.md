# MAP01 post-turn image and private-state alignment audit

Four previously registered OS-input MAP01 attempts reached `reverse-turn-3`. The table joins each frozen first visual gate with the independent private scorer's next post-turn sample and the owner-thread input receipts. Every scorer sample reports coherent game-state reads and neutral physical input. The scorer started 61–77 ms after the image capture, so image and game state are not simultaneous.

| Trial suffix | Visual gate mean | Gate | X | Y | Angle | Scorer after image |
|---|---:|---|---:|---:|---:|---:|
| 6289b5c7e14b5254 | 17.287 | fail | 779.064 | -192 | 170.508° | 77 ms |
| 46eefb3fb8ce727b | 15.561 | fail | 770.704 | -192 | 181.055° | 61 ms |
| 8be74fd22a808bb6 | 11.874 | pass | 779.064 | -192 | 181.055° | 63 ms |
| 63126e0771551402 | 18.445 | fail | 770.704 | -192 | 184.570° | 64 ms |

The same-angle pair has different X positions and different gate outcomes. This shows that similar orientation alone is insufficient to characterize these observations; it does not prove position caused the gate result, because other rendering and timing factors were not controlled. The 400 ms third-turn case differs from the three 475 ms cases. For all four trials the three owner-timed key releases started within 0.7 ms of their requested deadlines according to retained owner receipts; that is not a measurement of in-game tick-level rotation.

`audit.py` verifies the copied logs against their original seals, joins command and owner release records by intent token, checks neutral and coherent scorer reads, and outputs the unrounded values. `report.json` and `report-optimized.json` are its saved normal and optimized-Python outputs. This is retrospective observational evidence, not a new control attempt, MAP01 completion, proof of causal error, or permission to change the visual gate. Private scorer telemetry is for evaluation and was not supplied to the controller.

Run `python verify.py` to check `evidence.zip`, its seal and all retained source bytes, then replay the audit under normal and optimized Python. The verifier checks the archive digest before extraction into a temporary directory.
