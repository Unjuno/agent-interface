import unittest

from audit_policy import expected_schedule, policy_errors


META = {
    "window_id": "window-5459-t1-01",
    "generation": 17,
    "manifest_ids": [0, 1, 2, 3],
    "manifest_hash": "sha256:5459-t1-manifest-0-1-2-3",
    "auth_ok": True,
    "payload_hash_ok": True,
}
VALUES = (0x11, 0x23, 0x45, 0x89)


def source(slot, lost=False):
    return {
        **META,
        "slot": slot,
        "kind": "source",
        "symbol_id": slot,
        "mask": 1 << slot,
        "label": f"s{slot}",
        "value": VALUES[slot],
        "sent_round": 0,
        "lost": lost,
        "delay": 0,
        "arrival_round": None if lost else 0,
        "delivered": not lost,
    }


def row(arm, lost_source=None, followups=()):
    packets = [source(i, i == lost_source) for i in range(4)]
    packets.extend(followups)
    return {
        "arm": arm,
        "loss_mask": 0 if lost_source is None else 1 << lost_source,
        "delay_mask": 0,
        "packets": packets,
    }


def repair(slot, pair, sent_round=0):
    left = pair * 2
    right = left + 1
    mask = (3, 12)[pair]
    return {
        **META,
        "slot": slot,
        "kind": "repair",
        "symbol_id": None,
        "mask": mask,
        "label": f"p{pair}",
        "value": VALUES[left] ^ VALUES[right],
        "sent_round": sent_round,
        "lost": False,
        "delay": 0,
        "arrival_round": sent_round,
        "delivered": True,
    }


def retransmission(slot, source_id, sent_round=1):
    result = source(source_id)
    result.update({
        "slot": slot,
        "sent_round": sent_round,
        "arrival_round": sent_round,
    })
    return result


class IndependentPolicyAuditTests(unittest.TestCase):
    def test_fixed_sends_both_repairs_proactively(self):
        result = expected_schedule(row("fixed", lost_source=0))
        self.assertEqual([(p["kind"], p["symbol_id"], p["sent_round"]) for p in result[4:]],
                         [("repair", None, 0), ("repair", None, 0)])

    def test_retransmit_resends_first_missing_source_after_feedback_cut(self):
        result = expected_schedule(row(
            "retransmit", lost_source=0,
            followups=(retransmission(4, 0),),
        ))
        self.assertEqual([(p["kind"], p["symbol_id"], p["sent_round"]) for p in result[4:]],
                         [("source", 0, 1)])

    def test_adaptive_uses_pair_repair_for_single_missing_member(self):
        result = expected_schedule(row(
            "adaptive", lost_source=0,
            followups=(repair(4, 0, sent_round=1),),
        ))
        self.assertEqual([(p["kind"], p["mask"], p["sent_round"]) for p in result[4:]],
                         [("repair", 3, 1)])

    def test_adaptive_uses_no_repair_on_clean_window(self):
        result = expected_schedule(row("adaptive"))
        self.assertEqual(len(result), 4)

    def test_wrong_arm_schedule_is_detected(self):
        # Retransmission policy is labeled correctly, but emits fixed parity.
        wrong = row("retransmit", lost_source=0,
                    followups=(repair(4, 0), repair(5, 1)))
        self.assertTrue(policy_errors(wrong))

    def test_wrong_followup_policy_is_detected_after_valid_sloting(self):
        # Same packet count as retransmit; contents and timing violate its policy.
        wrong = row("retransmit", lost_source=0,
                    followups=(repair(4, 0, sent_round=1),))
        self.assertTrue(policy_errors(wrong))

    def test_forged_initial_delivery_is_detected(self):
        forged = row("adaptive")
        forged["packets"][0]["delay"] = 2
        self.assertTrue(any("channel_mismatch" in error for error in policy_errors(forged)))


if __name__ == "__main__":
    unittest.main(verbosity=2)

