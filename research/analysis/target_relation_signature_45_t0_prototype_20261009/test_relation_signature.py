import unittest

try:
    from relation_signature import revalidate
except ImportError:
    def revalidate(*args, **kwargs):
        raise AssertionError("relation-signature revalidation is not implemented")


class RelationSignatureTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            "surface": "surface-1",
            "container": "document-pane",
            "role": "button",
            "label": "Save",
            "relations": ["before:status-anchor", "inside:toolbar-anchor"],
            "generation": 4,
            "complete": True,
        }

    def test_translation_and_reorder_rebind_unique_relational_match(self):
        current = [{**self.source, "generation": 5, "coordinates": [800, 200]}]
        result = revalidate(self.source, current, generation=5, complete=True)
        self.assertEqual("REVALIDATED", result.status)
        self.assertEqual(0, result.candidate_index)
        self.assertEqual("none", result.authority)

    def test_same_label_in_another_container_is_not_rebound(self):
        current = [{**self.source, "container": "settings-pane", "generation": 5}]
        result = revalidate(self.source, current, generation=5, complete=True)
        self.assertEqual("NO_MATCH", result.status)

    def test_relation_order_does_not_change_signature(self):
        current = [{**self.source, "relations": list(reversed(self.source["relations"])),
                    "generation": 5}]
        result = revalidate(self.source, current, generation=5, complete=True)
        self.assertEqual("REVALIDATED", result.status)

    def test_duplicate_same_signature_is_ambiguous(self):
        current = [
            {**self.source, "generation": 5},
            {**self.source, "generation": 5, "coordinates": [10, 10]},
        ]
        result = revalidate(self.source, current, generation=5, complete=True)
        self.assertEqual("AMBIGUOUS", result.status)
        self.assertIsNone(result.candidate_index)

    def test_unique_container_candidate_with_changed_relations_is_unknown(self):
        current = [{**self.source, "relations": ["after:status-anchor"], "generation": 5}]
        result = revalidate(self.source, current, generation=5, complete=True)
        self.assertEqual("UNKNOWN", result.status)
        self.assertIsNone(result.candidate_index)

    def test_incomplete_or_stale_observation_fails_closed(self):
        current = [{**self.source, "generation": 5}]
        self.assertEqual(
            "UNKNOWN", revalidate(self.source, current, generation=5, complete=False).status
        )
        self.assertEqual(
            "STALE", revalidate(self.source, current, generation=6, complete=True).status
        )

    def test_contradictory_source_signature_is_rejected(self):
        source = {**self.source, "relations": ["inside:toolbar-anchor", "inside:toolbar-anchor"]}
        result = revalidate(source, [], generation=5, complete=True)
        self.assertEqual("INVALID", result.status)


if __name__ == "__main__":
    unittest.main()
