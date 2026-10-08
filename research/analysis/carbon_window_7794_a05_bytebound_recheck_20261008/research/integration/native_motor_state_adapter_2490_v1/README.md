# Native result → MotorState mapping gate (#2490)

H: current native result fields can map into the merged MotorState contract without inventing confirmation.
T: synthetic records cover confirmed observation, missing observation, unknown focus and failed release.
D: retain mapped uncertainty, release transition and ack status for each case.
C: pure standard-library mapping audit; no runtime/backend modification, GUI, model or lease mutation.
U: scoped mapping only; backend coverage and live pointer observation remain open.
