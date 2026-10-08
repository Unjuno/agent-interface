"""Strict receipt-identity wrapper for bounded post-release scorer sampling."""
from __future__ import annotations

from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin


def validate_release_receipt(receipt):
    """Require a complete, nonempty per-key owner key-up identity."""
    if not isinstance(receipt, dict):
        raise ValueError("release_receipt must be a verified release event")
    owner = receipt.get("owner_thread_keyup_receipt")
    release_ns = receipt.get("release_call_returned_ns")
    identity = (receipt.get("id"), receipt.get("step"), receipt.get("key"),
                receipt.get("owner_id"), receipt.get("intent_token"))
    if not (
        receipt.get("event") == "input_release_transition"
        and receipt.get("operation") == "up"
        and isinstance(identity[0], str) and bool(identity[0].strip())
        and type(identity[1]) is int and identity[1] >= 0
        and isinstance(identity[2], str) and bool(identity[2].strip())
        and isinstance(identity[3], str) and bool(identity[3].strip())
        and isinstance(identity[4], str) and bool(identity[4].strip())
        and receipt.get("owner_transition_verified") is True
        and receipt.get("owner_thread_keyup_verified") is True
        and receipt.get("owner_thread_keyup_verified_after_batch") is True
        and receipt.get("owner_identity_matches_after_batch") is True
        and receipt.get("intent_token_matches_after_batch") is True
        and receipt.get("owned_keycodes_after_batch") == []
        and isinstance(owner, dict)
        and owner.get("event") == "owner_explicit_keyup"
        and owner.get("operation") == "up"
        and owner.get("owner_id") == identity[3]
        and owner.get("key") == identity[2]
        and owner.get("intent_token") == identity[4]
        and owner.get("server_sync_completed") is True
        and type(release_ns) is int and release_ns >= 0
    ):
        raise ValueError("release_receipt lacks complete matching owner key-up identity")
    return release_ns


class MainThreadScorerStdin(MainThreadScorerStdin):
    """Preserve V1 polling while binding every tail to a complete release identity."""

    def sample_tail(self, *, release_receipt, max_duration_ns, max_samples,
                    stop_when=None):
        validate_release_receipt(release_receipt)
        return super().sample_tail(
            release_receipt=release_receipt,
            max_duration_ns=max_duration_ns,
            max_samples=max_samples,
            stop_when=stop_when,
        )
