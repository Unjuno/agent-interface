import unittest

from terminal_window_reconstruction import analyze


class TerminalWindowTests(unittest.TestCase):
    def setUp(self):
        self.report = {"decisions": [
            {},
        ] * 11 + [{
            "source_image": "/runtime/459.png",
            "model_ns": 10613874802,
            "controller_model_started_ns": 1_000_000_000,
            "controller_model_ended_ns": 11_692_805_184,
            "execution_trace": [
                {"command": {"action": action}, "accepted_ns": 11_720_929_250,
                 "receipt": {"after_sequence": sequence, "effect_observed_ns": timestamp}}
                for action, sequence, timestamp in zip(("backward", "turn_left", "turn_left"),
                                                       (498, 501, 504),
                                                       (12_090_000_000, 12_125_000_000, 12_774_997_309))
            ]
        }, {"source_image": "/runtime/504.png", "action": {"state": "dead"}}]}
        self.events = [
            {"event": "observation", "sequence": seq, "capture_ns": ts, "image": f"/runtime/{seq}.png", "exact": True}
            for seq, ts in ((459, 616_846_794), (498, 12_090_000_000), (501, 12_125_000_000), (504, 12_774_997_309))
        ]
        self.manifest = [{"iteration": i, "sha256": f"frame-{i}"} for i in range(13)]
        self.failure = {"visual_transcription": {"health": list(range(13))}}

    def test_reconstructs_final_window_and_receipt_order(self):
        self.failure["visual_transcription"]["health"][11:] = [4, 0]
        result = analyze(self.report, self.events, self.manifest, self.failure)
        self.assertEqual(result["observation_sequences"], [459, 498, 501, 504])
        self.assertEqual(result["observed_health_labels_manual"], [4, 0])
        self.assertAlmostEqual(result["timing_ms"]["precall_capture_to_terminal_capture"], 12158.150515)
        self.assertEqual(result["actions"], [{"action": "backward"}, {"action": "turn_left"}, {"action": "turn_left"}])

    def test_rejects_wrong_terminal_source_sequence(self):
        self.report["decisions"][12]["source_image"] = "/runtime/999.png"
        with self.assertRaisesRegex(ValueError, "TERMINAL_SOURCE_SEQUENCE_MISMATCH"):
            analyze(self.report, self.events, self.manifest, self.failure)


if __name__ == "__main__":
    unittest.main()
