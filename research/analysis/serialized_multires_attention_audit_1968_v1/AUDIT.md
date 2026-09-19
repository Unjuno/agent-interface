# Independent audit

The runner asserts exact raw recovery from the reduced package, checks both duplicate labels by contextual identity, and compares actual zlib-compressed serialized package bytes. The raw fallback is required for exact recovery; without it, the package is smaller but not authoritative. Therefore the preregistered size gate is not met and the first outcome is retained as HOLD_NO_SIZE_GAIN. Formal=1, reruns=0, tuning=0.

Result digest: 9efa3fd039778b34f95856668f314a502acc47534008ee53425bd874bb15cf1d.
