# Producer contract review correction (2026-10-05)

The first adapter fix required the release object to contain exactly three keys. A source-path review of the task wrapper showed that this would reject the real upstream record even when release verification succeeded:

1. `mindustry_three_arm_interactive_v1.py` installs `mindustry_receipt_session_v1.Backend` for the task child.
2. `cause_servo_session_v1.Backend` composes `session_v21.Backend`, whose backend chain reaches `session_v5.Backend.release_all`.
3. `session_v5.Backend.release_all` returns the input-owner record directly.
4. `input_owner_v10` constructs that record with `event: owner_release`, `reason`, strict `verified`, empty `keys_down`/`buttons_down`, `verified_ns`, and `valid_until_ns`.
5. `executor_v3` places this return value unchanged in the terminal event's `release` field.

The adapter now requires the three safety fields and their strict types/empty values, permits only the four named producer metadata fields, validates their values, and rejects unknown fields. A test using the producer-shaped envelope was added, plus malformed metadata/unknown-field controls. This is static source inspection plus synthetic contract testing; the live runtime and physical input were not invoked.
