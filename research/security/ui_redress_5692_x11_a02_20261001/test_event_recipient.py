import unittest
from types import SimpleNamespace


class EventRecipientTest(unittest.TestCase):
    def test_button_event_recipient_is_the_xlib_window_field(self):
        from candidate import button_event_record

        event = SimpleNamespace(type=4, window=SimpleNamespace(id=0x1234), root_x=10, root_y=20, detail=1)
        record = button_event_record(event, overlay_window_id=0x9999)

        self.assertEqual(record, {
            "type": "ButtonPress",
            "window_id": 0x9999,
            "event_window": 0x1234,
            "root_x": 10,
            "root_y": 20,
            "button": 1,
        })


if __name__ == "__main__":
    unittest.main()
