import json
import unittest

from ammo_video_timeline import ANNOTATIONS, DATA, build, decode_crops


class AmmoVideoTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotations = json.loads(ANNOTATIONS.read_text())
        cls.report = json.loads((DATA / "report.json").read_text())
        cls.events = [json.loads(line) for line in (DATA / "events.jsonl").read_text().splitlines()]
        cls.sidecar = json.loads((DATA / "video.json").read_text())
        cls.video = DATA / cls.sidecar["file"]
        frames = {row["video_frame"] for row in cls.annotations["endpoint_samples"]}
        for row in cls.annotations["decrements"]:
            frames.update((row["before_frame"], row["after_frame"]))
        _, cls.frame_data = decode_crops(cls.video, frames, cls.annotations["ammo_roi_xyxy"])

    def test_all_video_ammo_transitions_overlap_cover_space_holds(self):
        import hashlib

        result = build(self.report, self.events, self.sidecar, self.annotations, self.frame_data,
                       hashlib.sha256(self.video.read_bytes()).hexdigest())
        self.assertEqual(result["ammo_decrement_count"], 11)
        self.assertEqual([result["ammo_decrements_before_plan4_model_start"],
                          result["ammo_decrements_straddling_plan4_model_start"],
                          result["ammo_decrements_during_plan4_model_window"]], [1, 1, 9])
        self.assertTrue(result["all_transition_intervals_overlap_cover4_space_hold_lifecycle"])
        self.assertEqual(len(result["firing_steps"]), 5)

    def test_selected_video_frames_align_with_raw_observations(self):
        import hashlib

        result = build(self.report, self.events, self.sidecar, self.annotations, self.frame_data,
                       hashlib.sha256(self.video.read_bytes()).hexdigest())
        self.assertEqual([row["video_frame"] for row in result["endpoint_alignment"]], [176, 220, 285])
        self.assertLess(max(abs(row["video_minus_capture_ms"]) for row in result["endpoint_alignment"]), 100)

    def test_metadata_speed_mismatch_is_rejected(self):
        import hashlib

        sidecar = dict(self.sidecar, source_playback_speed=1.0)
        with self.assertRaisesRegex(ValueError, "VIDEO_TIMING_METADATA_MISMATCH"):
            build(self.report, self.events, sidecar, self.annotations, self.frame_data,
                  hashlib.sha256(self.video.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
