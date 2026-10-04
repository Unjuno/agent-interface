import unittest

from map01_scorer_stdio_adapter_v2 import (
    MainThreadScorerStdin, validate_release_receipt,
)


def verified_release():
    return {
        "event": "input_release_transition", "operation": "up",
        "id": "program-1", "step": 2, "key": "d",
        "owner_id": "owner-1", "intent_token": "token-1",
        "owner_transition_verified": True,
        "owner_thread_keyup_verified": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True,
        "owned_keycodes_after_batch": [],
        "release_call_returned_ns": 10,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "operation": "up",
            "owner_id": "owner-1", "key": "d", "intent_token": "token-1",
            "server_sync_completed": True,
        },
    }


class StrictReleaseIdentityTests(unittest.TestCase):
    def make_adapter(self, clock_ns=10):
        class Loop:
            period_ns = 1

            def clock_ns(self):
                return clock_ns

            def wait_readable(self, *_args):
                return False

        stream = type("Stream", (), {"fileno": lambda _self: 0})()
        return MainThreadScorerStdin(stream, lambda: self.fail("zero-duration tail sampled"),
                                     lambda _row: None, loop=Loop())

    def test_realistic_receipt_passes_and_zero_budget_samples_nothing(self):
        receipt = verified_release()
        self.assertEqual(validate_release_receipt(receipt), 10)
        result = self.make_adapter().sample_tail(
            release_receipt=receipt, max_duration_ns=0, max_samples=1)
        self.assertEqual(result["disposition"], "CENSORED")
        self.assertEqual(result["termination"], "deadline")
        self.assertEqual(result["tail_samples"], 0)

    def test_empty_or_wrongly_typed_identity_is_rejected(self):
        mutations = (
            {"id": ""}, {"step": True}, {"key": ""},
            {"owner_id": None}, {"intent_token": ""},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                receipt = {**verified_release(), **mutation}
                with self.assertRaises(ValueError):
                    validate_release_receipt(receipt)

    def test_nested_key_owner_and_token_must_match(self):
        mutations = (
            {"key": "a"}, {"owner_id": "other"}, {"intent_token": "other"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                receipt = verified_release()
                receipt["owner_thread_keyup_receipt"] = {
                    **receipt["owner_thread_keyup_receipt"], **mutation}
                with self.assertRaises(ValueError):
                    validate_release_receipt(receipt)

    def test_release_timestamp_and_empty_owner_state_are_required(self):
        for mutation in ({"release_call_returned_ns": True},
                         {"owned_keycodes_after_batch": [40]}):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    validate_release_receipt({**verified_release(), **mutation})


if __name__ == "__main__":
    unittest.main()
