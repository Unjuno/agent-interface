import unittest

from policy import choose_edge


class SoftRevisitPolicyTests(unittest.TestCase):
    def test_visible_revision_hint_can_reopen_an_incompletely_inspected_branch(self):
        observation = {
            "source_epoch": 4,
            "edges": [
                {
                    "id": "profile",
                    "label": "Profile",
                    "nearby": "recently changed",
                    "saliency": 0,
                    "reversible": True,
                    "revision_hint": True,
                },
                {
                    "id": "help",
                    "label": "Help",
                    "nearby": "",
                    "saliency": 70,
                    "reversible": True,
                    "revision_hint": False,
                },
            ],
        }
        memory = {
            "profile": {"visits": 1, "last_epoch": 4, "inspection_complete": False},
            "help": {"visits": 0, "last_epoch": None, "inspection_complete": False},
        }

        self.assertEqual(choose_edge(observation, "open profile", memory, "soft"), "profile")

    def test_hard_policy_never_revisits_a_branch_in_the_same_epoch(self):
        observation = {
            "source_epoch": 4,
            "edges": [
                {"id": "profile", "label": "Profile", "nearby": "", "saliency": 1, "reversible": True},
                {"id": "help", "label": "Help", "nearby": "", "saliency": 90, "reversible": True},
            ],
        }
        memory = {"profile": {"visits": 1, "last_epoch": 4, "inspection_complete": False}}
        self.assertEqual(choose_edge(observation, "open profile", memory, "hard"), "help")

    def test_new_epoch_invalidates_visit_memory(self):
        observation = {
            "source_epoch": 5,
            "edges": [
                {"id": "profile", "label": "Profile", "nearby": "", "saliency": 90, "reversible": True},
                {"id": "help", "label": "Help", "nearby": "", "saliency": 1, "reversible": True},
            ],
        }
        memory = {"profile": {"visits": 1, "last_epoch": 4, "inspection_complete": True}}
        self.assertEqual(choose_edge(observation, "open profile", memory, "hard"), "profile")

    def test_nonreversible_edges_are_never_selected(self):
        observation = {
            "source_epoch": 4,
            "edges": [
                {"id": "unsafe", "label": "Profile", "nearby": "", "saliency": 100, "reversible": False},
                {"id": "safe", "label": "Help", "nearby": "", "saliency": 1, "reversible": True},
            ],
        }
        self.assertEqual(choose_edge(observation, "open profile", {}, "stateless"), "safe")

    def test_soft_policy_does_not_revisit_a_complete_stable_branch(self):
        observation = {
            "source_epoch": 4,
            "edges": [
                {"id": "profile", "label": "Profile", "nearby": "", "saliency": 90, "reversible": True, "revision_hint": False},
                {"id": "help", "label": "Help", "nearby": "", "saliency": 1, "reversible": True, "revision_hint": False},
            ],
        }
        memory = {"profile": {"visits": 1, "last_epoch": 4, "inspection_complete": True}}
        self.assertEqual(choose_edge(observation, "open profile", memory, "soft"), "help")


if __name__ == "__main__":
    unittest.main()
