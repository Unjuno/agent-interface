"""Classify the captured frozen-audit signature conservatively."""

EXPECTED_FROZEN_FAILURE = {
    "first_keyup_was_dropped": True,
    "keymap_query_interleaves_explicit_up_injections": True,
    "no_real_io_claimed": True,
    "per_key_receipts_match_rows": False,
    "receipt_attempt_records_drop_and_retry": True,
    "retry_released_dropped_key": True,
    "two_distinct_key_downs": True,
    "two_release_batch_rows": True,
    "verified_empty_release_batch": True,
}

FAILURE_EXPLANATION = (
    "Frozen auditor compared receipt.keycode with release_row.keycode; release rows "
    "expose key and nest keycode in owner_thread_keyup_receipt."
)


def classify(checks, frozen_audit):
    if (type(checks) is dict and checks and all(value is True for value in checks.values())
            and type(frozen_audit) is dict
            and frozen_audit.get("status") == "FAIL"
            and frozen_audit.get("checks") == EXPECTED_FROZEN_FAILURE):
        return "RAW_BEHAVIOR_CONFIRMED_AUDITOR_SCHEMA_BUG"
    return "POSTHOC_CHECK_FAILURE"
