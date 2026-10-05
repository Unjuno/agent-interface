import unittest

from inventory_producer import certify_from_pages


def page(epoch, items, *, page_index, page_count=1, complete=True, writers=True):
    return {
        "schema": "inventory.v1",
        "surface_id": "surface-A",
        "epoch": epoch,
        "page_index": page_index,
        "page_count": page_count,
        "universe_complete": complete,
        "writer_coverage": writers,
        "predicate_version": "text-exact.v1",
        "items": items,
    }


class InventoryProducerTests(unittest.TestCase):
    def test_complete_same_epoch_pages_can_certify_scoped_no_match(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0, page_count=2),
             page(7, [{"id": "b", "label": "Cancel"}], page_index=1, page_count=2)],
            query="Delete",
        )
        self.assertEqual(result["status"], "NO_MATCH_WITHIN_CERTIFIED_SCOPE")
        self.assertEqual(result["scope"]["surface_id"], "surface-A")
        self.assertEqual(result["scope"]["epoch"], 7)

    def test_partial_virtualized_universe_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "visible", "label": "Save"}], page_index=0,
                     page_count=5, complete=False)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_missing_writer_coverage_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0, writers=False)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_epoch_drift_across_pages_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0,
                   page_count=2),
             page(8, [{"id": "b", "label": "Cancel"}], page_index=1,
                   page_count=2)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_matching_item_is_never_a_negative_certificate(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Delete"}], page_index=0)],
            query="Delete",
        )
        self.assertEqual(result["status"], "MATCH_FOUND")
        self.assertEqual(result["match"]["id"], "a")

    def test_missing_page_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0,
                   page_count=2)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_duplicate_page_index_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0,
                   page_count=2),
             page(7, [{"id": "b", "label": "Cancel"}], page_index=0,
                   page_count=2)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_surface_or_predicate_drift_must_abstain(self):
        first = page(7, [{"id": "a", "label": "Save"}], page_index=0,
                     page_count=2)
        second = page(7, [{"id": "b", "label": "Cancel"}], page_index=1,
                      page_count=2)
        second["surface_id"] = "surface-B"
        result = certify_from_pages([first, second], query="Delete")
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")

    def test_duplicate_object_identity_must_abstain(self):
        result = certify_from_pages(
            [page(7, [{"id": "a", "label": "Save"}], page_index=0,
                   page_count=2),
             page(7, [{"id": "a", "label": "Cancel"}], page_index=1,
                   page_count=2)],
            query="Delete",
        )
        self.assertEqual(result["status"], "UNKNOWN_INCOMPLETE_COVERAGE")


if __name__ == "__main__":
    unittest.main()
