from __future__ import annotations

import json
import unittest

from audit import validate_schema


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["format", "point"],
    "properties": {
        "format": {"type": "string", "const": "typed-v1"},
        "point": {
            "type": "object",
            "additionalProperties": False,
            "required": ["x", "y"],
            "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        },
    },
}


class SchemaAuditControls(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual([], validate_schema({"format": "typed-v1", "point": {"x": 1, "y": 2}}, SCHEMA))

    def test_unknown_field_rejected(self):
        self.assertTrue(validate_schema({"format": "typed-v1", "point": {"x": 1, "y": 2}, "extra": 1}, SCHEMA))

    def test_boolean_is_not_integer(self):
        self.assertTrue(validate_schema({"format": "typed-v1", "point": {"x": True, "y": 2}}, SCHEMA))

    def test_required_field_enforced(self):
        self.assertTrue(validate_schema({"format": "typed-v1", "point": {"x": 1}}, SCHEMA))

    def test_const_enforced(self):
        self.assertTrue(validate_schema({"format": "other", "point": {"x": 1, "y": 2}}, SCHEMA))


if __name__ == "__main__":
    unittest.main()

