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
    def test_malformed_top_level_values_keep_full_fallback(self):
        for value in [None, [], 'invalid', {}]:
            self.assertEqual(summarize_public_dispatch(value), value)

    def test_cli_summary_requires_exact_retained_report_and_keeps_image(self):
        import hashlib
        from runtime.cli_v1.public_summary import summarize_cli_dispatch
        full = fixture('paced_dispatch_review.json')
        full.pop('call_id');full.pop('call_directory')
        full['image'] = {'type': 'image', 'mimeType': 'image/png', 'data': 'unchanged'}
        raw = json.dumps(full['receipt']['source']['raw_report']).encode()
        full['receipt']['source'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertEqual(summarize_cli_dispatch(full, root), full)
            (root/'report.json').write_bytes(raw)
            brief = summarize_cli_dispatch(full, root)
            self.assertEqual(brief['receipt']['schema'], SCHEMA)
            self.assertEqual(brief['image'], full['image'])
            self.assertEqual(brief['outcome_summary'], full['outcome_summary'])
            self.assertNotIn('call_id', brief)
            retrieve = brief['presentation']['retrieve']
            self.assertEqual(retrieve['command'], 'review')
            self.assertTrue(retrieve['arguments']['no_image'])
            self.assertEqual(retrieve['arguments']['expected_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(retrieve['arguments']['report'], str(root/'report.json'))
            (root/'report.json').write_bytes(raw+b' ')
            self.assertEqual(summarize_cli_dispatch(full, root), full)

    def test_arbitrary_retained_report_summary_keeps_exact_retrieval_and_image(self):
        import hashlib
        from runtime.cli_v1.public_summary import summarize_retained_dispatch
        full = fixture('paced_dispatch_review.json')
        full.pop('call_id'); full.pop('call_directory')
        full['image'] = {'type': 'image', 'mimeType': 'image/png', 'data': 'unchanged'}
        raw = json.dumps(full['receipt']['source']['raw_report']).encode()
        full['receipt']['source'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            report = Path(td)/'002-raw.json'
            report.write_bytes(raw)
            before = copy.deepcopy(full)
            summary = summarize_retained_dispatch(full, report, td)
            self.assertEqual(full, before)
            self.assertEqual(summary['receipt']['schema'], SCHEMA)
            self.assertEqual(summary['image'], full['image'])
            self.assertEqual(summary['outcome_summary'], full['outcome_summary'])
            args = summary['presentation']['retrieve']['arguments']
            self.assertEqual(args['report'], str(report))
            self.assertEqual(args['expected_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(args['run_directory'], td)
            self.assertTrue(args['no_image'])
            self.assertFalse((Path(td)/'report.json').exists())
            report.write_bytes(raw+b' ')
            self.assertEqual(summarize_retained_dispatch(full, report, td), full)
            report.unlink()
            self.assertEqual(summarize_retained_dispatch(full, report, td), full)

    def test_arbitrary_retained_report_failure_preserves_full_evidence(self):
        import hashlib
        from runtime.cli_v1.public_summary import summarize_retained_dispatch
        full = fixture('paced_dispatch_review.json')
        full.pop('call_id'); full.pop('call_directory')
        full['receipt']['source']['raw_report']['result']['recovery_required'] = True
        raw = json.dumps(full['receipt']['source']['raw_report']).encode()
        full['receipt']['source'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            report = Path(td)/'failed.json'; report.write_bytes(raw)
            self.assertEqual(summarize_retained_dispatch(full, report, td), full)

    def test_cli_presentation_keeps_retention_and_falls_back_on_persistence_failure(self):
        import hashlib,io
        from runtime.cli_v1.__main__ import _present_result
        full = fixture('nonpaced_dispatch_review.json')
        full.pop('call_id');full.pop('call_directory')
        raw = json.dumps(full['receipt']['source']['raw_report']).encode()
        full['receipt']['source'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'report.json').write_bytes(raw)
            for persisted in [True, False]:
                retention = {'directory':td,'request_persisted':True,'report_persisted':persisted,'replay_allowed':False}
                output = io.StringIO()
                with patch('runtime.cli_v1.__main__.present_result',return_value=copy.deepcopy(full)), patch('sys.stdout',output):
                    code = _present_result({},with_review=True,capture_directory=td,exit_code=0,
                        compact=True,report_refs=True,retention=retention,detail='summary')
                row = json.loads(output.getvalue())
                self.assertEqual(row['retention'], retention)
                self.assertEqual(row['outcome_summary'], full['outcome_summary'])
                self.assertEqual(row['receipt']['schema'], SCHEMA if persisted else full['receipt']['schema'])
                self.assertEqual(code,0 if persisted else 2)

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

    def test_inconsistent_wait_timeline_stays_full(self):
        for mutation in ("before_execution", "after_execution", "overlap", "reversed_timeline"):
            with self.subTest(mutation=mutation):
                view = fixture("paced_dispatch_review.json")
                execution = view["receipt"]["source"]["raw_report"]["result"]["execution"]
                waits = execution["waits"]
                if mutation == "before_execution":
                    waits[0]["started_ns"] = execution["started_ns"] - 1
                elif mutation == "after_execution":
                    waits[-1]["ended_ns"] = execution["ended_ns"] + 1
                elif mutation == "overlap":
                    waits[1]["started_ns"] = waits[0]["ended_ns"] - 1
                else:
                    for key in ("started_ns", "ended_ns"):
                        waits[0][key], waits[1][key] = waits[1][key], waits[0][key]
                original = copy.deepcopy(view)
                self.assertEqual(summarize_public_dispatch(view), original)
                self.assertEqual(view, original)

    def test_post_dispatch_inspection_preserved_or_full_on_failure_and_mismatch(self):
        inspection = {'status':'needs_review', 'input_dispatched':False,
                      'authority_granted':False, 'expires_at_ns':123,
                      'review_request':{'tool':'interface_review_target','arguments':{'review_id':'one-use'}},
                      'extension':{'report_ref':'literal'}}
        for mode in ('normal','retained','error','skipped','mismatch','missing_outer','missing_raw'):
            with self.subTest(mode=mode):
                view=fixture('nonpaced_dispatch_review.json')
                raw=view['receipt']['source']['raw_report']
                view['post_dispatch_inspection']=copy.deepcopy(inspection)
                raw['post_dispatch_inspection']=copy.deepcopy(inspection)
                if mode=='retained': view.pop('session')
                if mode=='error':
                    raw['post_dispatch_inspection']['error']='unavailable'
                    view['post_dispatch_inspection']['error']='unavailable'
                if mode=='skipped':
                    raw['post_dispatch_inspection']['status']='skipped'
                    view['post_dispatch_inspection']['status']='skipped'
                if mode=='mismatch': view['post_dispatch_inspection']['expires_at_ns']+=1
                if mode=='missing_outer': view.pop('post_dispatch_inspection')
                if mode=='missing_raw': raw.pop('post_dispatch_inspection')
                original=copy.deepcopy(view)
                result=summarize_public_dispatch(view)
                if mode in ('normal','retained'):
                    self.assertEqual(result['receipt']['schema'],SCHEMA)
                    self.assertEqual(result['post_dispatch_inspection'],inspection)
                else: self.assertEqual(result,original)
                self.assertEqual(view,original)

    def test_retained_report_without_live_session_keeps_historical_session(self):
        view = fixture("nonpaced_dispatch_review.json")
        session = view.pop("session")  # Actual interface_results shape: no live owner snapshot.
        summary = summarize_public_dispatch(view)
        self.assertEqual(summary["receipt"]["schema"], SCHEMA)
        self.assertNotIn("session", summary)
        self.assertEqual(summary["receipt"]["reported_session"], session)

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
        full.pop("session")  # Match retained presentation rather than the live-owner wrapper.
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
