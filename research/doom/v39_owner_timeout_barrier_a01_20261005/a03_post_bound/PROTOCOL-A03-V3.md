# Late cleanup beyond the A02 post-timeout wait bound — A03 v3

Same scientific protocol as A03, with a runner correction after retained construction failures. The timeout handler schedules fake-gate release 1.75 s after timeout, records the gate-open timestamp, and leaves the candidate's 1.5 s owner-stop wait unchanged. A pre-run source assertion verifies the timer exists and immediate release is absent.
