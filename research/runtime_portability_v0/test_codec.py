import unittest

from codec import (
    CodecError, WorkflowDictionary, decode_c0, decode_c1, decode_c2_reference,
    encode_c0, encode_c1, encode_c2_reference,
)


def sample_program(program_id="p1", seq=7):
    return {
        "schema": "agent-interface/program-v0",
        "program_id": program_id,
        "source": {"observation_seq": seq, "binding_revision": 3},
        "authority": {"lease_id": "lease-1", "expires_at_ns": 2_000_000},
        "ops": [
            {"op": "focus", "target": "editor"},
            {"op": "text", "text": 'a;"b\\c'},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 500},
            {"op": "verify", "predicate": "document_saved"},
            {"op": "release_all"},
        ],
        "terminal": {"release_all_required": True},
    }


class CodecTests(unittest.TestCase):
    def test_c0_round_trip(self):
        p = sample_program()
        self.assertEqual(decode_c0(encode_c0(p)), p)

    def test_c1_round_trip(self):
        p = sample_program()
        self.assertEqual(decode_c1(encode_c1(p)), p)

    def test_c1_is_smaller_for_representative_program(self):
        p = sample_program()
        self.assertLess(len(encode_c1(p).encode()), len(encode_c0(p).encode()))

    def test_unknown_opcode_fails_closed(self):
        payload = encode_c1(sample_program()).replace("K:CTRL+S", "Q:CTRL+S")
        with self.assertRaises(CodecError):
            decode_c1(payload)

    def test_malformed_text_fails_closed(self):
        payload = encode_c1(sample_program()).replace('T:"a;\\"b\\\\c"', 'T:"unterminated')
        with self.assertRaises(CodecError):
            decode_c1(payload)

    def test_dictionary_reference_round_trip(self):
        p = sample_program()
        dictionary = WorkflowDictionary.build(4, {"save": p["ops"]})
        payload = encode_c2_reference(p, dictionary, "save")
        self.assertEqual(decode_c2_reference(payload, dictionary), p)

    def test_stale_dictionary_epoch_digest_fails_closed(self):
        p = sample_program()
        d1 = WorkflowDictionary.build(4, {"save": p["ops"]})
        d2 = WorkflowDictionary.build(5, {"save": p["ops"]})
        payload = encode_c2_reference(p, d1, "save")
        with self.assertRaises(CodecError):
            decode_c2_reference(payload, d2)

    def test_dictionary_wrong_expansion_not_encodable(self):
        p = sample_program()
        dictionary = WorkflowDictionary.build(1, {"save": [{"op": "release_all"}]})
        with self.assertRaises(CodecError):
            encode_c2_reference(p, dictionary, "save")

    def test_dictionary_definition_has_digest(self):
        p = sample_program()
        dictionary = WorkflowDictionary.build(1, {"save": p["ops"]})
        self.assertIn(dictionary.digest, dictionary.definition_payload())


if __name__ == "__main__":
    unittest.main()
