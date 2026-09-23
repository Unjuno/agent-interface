import unittest

from source_pixel_transform_v1 import to_window_content


class MintPointTransformTests(unittest.TestCase):
    def test_source_pixels_are_rebased_to_window_content_origin(self):
        source = {"sequence": 6, "pointer_binding": {"geometry": [10, 10, 1050, 780]}}
        grounding = {"field_point": [234, 402], "submit_point": [386, 402]}
        self.assertEqual(to_window_content(grounding["field_point"],
                                          source["pointer_binding"]["geometry"]),
                         [224, 392])
        self.assertEqual(to_window_content(grounding["submit_point"],
                                          source["pointer_binding"]["geometry"]),
                         [376, 392])


if __name__ == "__main__":
    unittest.main()
