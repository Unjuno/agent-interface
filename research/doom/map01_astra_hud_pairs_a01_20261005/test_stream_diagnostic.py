import unittest
from stream_diagnostic import analyze


class StreamDiagnosticTests(unittest.TestCase):
    def test_joins_intermediate_full_frame_hashes_to_waits(self):
        events = [
            {"event":"observation","sequence":1,"capture_ns":100,"image":"/runtime/001.png","exact":True},
            {"event":"observation","sequence":2,"capture_ns":120,"image":"/runtime/002.png","exact":True},
            {"event":"observation","sequence":3,"capture_ns":130,"image":"/runtime/003.png","exact":True},
        ]
        decisions = [{"controller_model_started_ns":110,"controller_model_ended_ns":140,"fresh_sequence_at_plan":3}]
        manifest = {"frames":[
            {"file":"001.png","sha256":"a"},
            {"file":"002.png","sha256":"b"},
            {"file":"003.png","sha256":"b"},
        ]}
        result = analyze(events, decisions, manifest, image_root_present=False)
        wait = result["waits"][0]
        self.assertEqual(wait["observation_count"],2)
        self.assertEqual(wait["first_observation_latency_ms"],0.00001)
        self.assertEqual(wait["first_different_full_frame_hash_ms"],0.00001)
        self.assertEqual(wait["max_capture_gap_ms"],0.00001)
        self.assertTrue(wait["return_sequence_matches_latest_observation"])
        self.assertFalse(result["intermediate_image_bytes_present"])

    def test_unmapped_or_nonexact_observation_fails_integrity(self):
        events = [{"event":"observation","sequence":1,"capture_ns":100,"image":"/runtime/missing.png","exact":False}]
        decisions = [{"controller_model_started_ns":101,"controller_model_ended_ns":110,"fresh_sequence_at_plan":1}]
        result = analyze(events, decisions, {"frames":[]}, image_root_present=False)
        self.assertEqual(result["integrity_mismatches"],4)


if __name__ == "__main__":
    unittest.main()
