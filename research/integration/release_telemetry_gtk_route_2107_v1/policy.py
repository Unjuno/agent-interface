"""Frozen task policy: release receipts are telemetry, never effect authority."""

WAIT_NS = 50_000_000
RETRY_AFTER_NS = 500_000_000
ABORT_AFTER_RETRY_NS = 500_000_000


def choose(*, action_returned: bool, receipt_status: str, visible_state: str | None,
           key_down: bool | None, elapsed_ns: int, retries: int) -> str:
    """Choose one action from the declared task observations only."""
    if not action_returned:
        return "WAIT"
    if visible_state == "DONE" and key_down is False:
        return "CONTINUE"
    if key_down is True:
        return "WAIT"
    if elapsed_ns < 0:
        return "ABORT"
    if visible_state is None or key_down is None:
        return "QUERY"
    if retries == 0 and elapsed_ns >= RETRY_AFTER_NS:
        return "RETRY"
    if retries > 0 and elapsed_ns >= RETRY_AFTER_NS + ABORT_AFTER_RETRY_NS:
        return "ABORT"
    return "WAIT"
