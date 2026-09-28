import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runtime.cli_v1.public_summary import SCHEMA, encoded, summarize_public_dispatch
from runtime.cli_v1.receipt_references import expand_receipt


def fixture(name):
    return json.loads((Path(__file__).parent / "fixtures" / name).read_text())


class PublicSummaryTests(unittest.TestCase):
    def test_paced_and_nonpaced_keep_outcomes_and_native_evidence(self):
        for name in ("paced_dispatch_review.json", "nonpaced_dispatch_review.json"):
            with self.subTest(name=name):
                full = fixture(name)
                original = copy.deepcopy(full)
                brief = summarize_public_dispatch(full)
                self.assertEqual(full, original)
                self.assertEqual(brief["receipt"]["schema"], SCHEMA)
                self.assertLess(len(encoded(brief)), len(encoded(full)))
                for key in ("outcome_summary", "image_reference", "session", "call_id"):
                    self.assertEqual(brief[key], full[key])
                execution = full["receipt"]["source"]["raw_report"]["result"]["execution"]
                summary = brief["receipt"]["execution_summary"]
                for key in ("observations", "releases", "activations", "started_ns", "ended_ns", "program_emissions"):
                    self.assertEqual(summary[key], execution[key])
                self.assertEqual(summary["completed_operation_count"], len(execution["completed_ops"]))
                self.assertEqual(summary["wait_summary"]["requested_ms_total"], sum(w["requested_ms"] for w in execution["waits"]))
                self.assertIsNone(summary["wait_summary"]["update_observed"])
                with self.assertRaises(ValueError):
                    expand_receipt(brief["receipt"])

    def test_failures_extensions_and_inconsistent_receipts_stay_full(self):
        for mutation in ("failed", "recovery", "release", "capture", "wait_error", "wait_extension", "wait_order", "wait_time", "completed", "receipt_extension", "raw_extension", "execution_extension", "normalization_extension", "normalization_program", "normalization_indices", "session", "authority", "persistence", "mapping", "image"):
            with self.subTest(mutation=mutation):
                view = fixture("paced_dispatch_review.json")
                raw = view["receipt"]["source"]["raw_report"]
                ex = raw["result"]["execution"]
                if mutation == "failed": raw["result"]["status"] = "execution_failed"
                elif mutation == "recovery": raw["result"]["recovery_required"] = True
                elif mutation == "release": ex["releases"][0]["verified"] = False
                elif mutation == "capture": ex["observations"][0]["artifact_error"] = "lost"
                elif mutation == "wait_error": ex["waits"][0]["completed"] = False
                elif mutation == "wait_extension": ex["waits"][0]["new_evidence"] = "keep"
                elif mutation == "wait_order": ex["waits"].reverse()
                elif mutation == "wait_time": ex["waits"][0]["ended_ns"] = -1
                elif mutation == "completed": ex["completed_ops"].pop()
                elif mutation == "receipt_extension": view["receipt"]["new_evidence"] = "keep"
                elif mutation == "raw_extension": raw["new_evidence"] = "keep"
                elif mutation == "execution_extension": ex["new_evidence"] = "keep"
                elif mutation == "normalization_extension": raw["normalization"]["new_evidence"] = "keep"
                elif mutation == "normalization_program": raw["normalization"]["source_program"]["program_id"] = "different"
                elif mutation == "normalization_indices": raw["normalization"]["source_operation_indices"] = []
                elif mutation == "session": view["session"]["binding_revision"] += 1
                elif mutation == "authority": view["receipt"]["authority"] = "unknown"
                elif mutation == "persistence": view["persistence_error"] = "write failed"
                elif mutation == "mapping": raw["compilation"]["operation_sources"].pop()
                elif mutation == "image": view["image_status"] = "missing"
                self.assertEqual(summarize_public_dispatch(view), view)

    def test_preserved_native_extensions_and_literal_reference_shapes(self):
        view = fixture("nonpaced_dispatch_review.json")
        raw = view["receipt"]["source"]["raw_report"]
        raw["result"]["execution"]["observations"][0]["extra"] = {"report_ref": "literal"}
        result = summarize_public_dispatch(view)
        self.assertEqual(result["receipt"]["execution_summary"]["observations"], raw["result"]["execution"]["observations"])


class PublicSummaryMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_opt_in_and_full_retrieval_do_not_change_persisted_report_or_replay(self):
        from runtime.cli_v1.mcp_server import create_server
        full = fixture("nonpaced_dispatch_review.json")
        raw = full["receipt"]["source"]["raw_report"]
        args = {"program": raw["normalization"]["source_program"], "current_observation_seq": 1,
                "current_binding_revision": 1, "compact": True, "report_refs": True}
        with tempfile.TemporaryDirectory() as td:
            server = create_server({"left": 1}, td)
            with patch("runtime.cli_v1.mcp_server.dispatch", return_value=raw) as dispatch, patch("runtime.cli_v1.mcp_server.present_result", side_effect=lambda *a, **k: copy.deepcopy(full)):
                default = json.loads((await server.call_tool("interface_dispatch", args)).content[0].text)
                self.assertEqual(default["receipt"], full["receipt"])
                short = json.loads((await server.call_tool("interface_dispatch", dict(args, detail="summary"))).content[0].text)
                self.assertEqual(short["receipt"]["schema"], SCHEMA)
                path = Path(td, short["call_id"], "report.json")
                original_bytes = path.read_bytes()
                retrieve = short["presentation"]["retrieve"]
                restored = json.loads((await server.call_tool(retrieve["tool"], retrieve["arguments"])).content[0].text)
                self.assertFalse(restored["operation_invoked"])
                self.assertEqual(restored["receipt"]["source"]["raw_report"], raw)
                self.assertEqual(path.read_bytes(), original_bytes)
                again = json.loads((await server.call_tool("interface_results", dict(retrieve["arguments"], detail="summary"))).content[0].text)
                self.assertEqual(again["receipt"]["schema"], SCHEMA)
                self.assertEqual(dispatch.call_count, 2)
                self.assertNotIn("detail", dispatch.call_args.kwargs)
