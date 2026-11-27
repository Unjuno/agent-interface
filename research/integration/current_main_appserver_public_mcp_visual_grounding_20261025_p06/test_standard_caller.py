"""No-model public-caller controls for the p06 grounding/effect composition."""

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_owned_process import _compiled_profile_payload
from research.integration.current_main_appserver_public_mcp_visual_grounding_20261025_p06.fake_factory import (
    EFFECT_PIXEL, GREEN_RECT, SUCCESS_RGB, grounding_fake_owner_factory,
)


def body(response):
    return json.loads(response.content[0].text)


class StandardCallerVisualGroundingTests(unittest.IsolatedAsyncioTestCase):
    async def _run_target(self, point, expected_success):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            server = create_server(
                {"app": 20}, root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=grounding_fake_owner_factory)
            try:
                observed = body(await server.call_tool(
                    "interface_guarded_observe", {}))
                self.assertEqual(observed["status"], "observed")
                mint = body(await server.call_tool("interface_guarded_mint", {
                    "alias": "grounded_green",
                    "source_sequence": observed["source"]["sequence"],
                    "point": point, "region_size": [4, 4]}))
                self.assertEqual(mint["status"], "minted", mint)
                payload = _compiled_profile_payload(
                    observed["session"]["compiled_scope"],
                    observed["session"]["compiled_surface"], mint["offset"])
                payload["interface"]["symbols"]["field"]["target_reference"] = "grounded_green"
                payload["bindings"]["enter"]["interaction"] = "click"
                payload["bindings"]["enter"]["tail"] = []
                payload["wait_for_result_ms"] = 10000
                result = body(await server.call_tool(
                    "interface_guarded_compiled", payload))
                receipt = result["method_receipt"]
                self.assertTrue(receipt.get("transitions"), result)
                self.assertEqual(result["task_success"], None)
                self.assertTrue(receipt.get("transitions"), result); self.assertTrue(receipt["transitions"][0]["release_verified"], result)
                click_files = list(root.rglob("synthetic-target-click.json"))
                self.assertEqual(len(click_files), 1)
                click = json.loads(click_files[0].read_text(encoding="utf-8"))
                actual_point = click["event"]["point"]
                inside = (GREEN_RECT[0] <= actual_point[0] <= GREEN_RECT[2] and
                          GREEN_RECT[1] <= actual_point[1] <= GREEN_RECT[3])
                effect_files = list(root.rglob("synthetic-effect-receipt.json"))
                state_files = list(root.rglob("synthetic-application-state.rgb"))
                self.assertEqual(len(effect_files), 1 if expected_success else 0)
                self.assertEqual(len(state_files), 1 if expected_success else 0)
                if expected_success:
                    self.assertTrue(inside)
                    self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
                    raw = state_files[0].read_bytes()
                    pixel = list(Image.frombytes(
                        "RGB", (32, 32), raw, "raw", "BGRX").getpixel(EFFECT_PIXEL))
                    self.assertEqual(pixel, list(SUCCESS_RGB))
                else:
                    self.assertFalse(inside)
                    self.assertNotEqual(receipt["outcome"], "TASK_SUCCEEDED")
            finally:
                await server.call_tool("interface_close", {})

    async def test_public_caller_clicks_minted_target_and_only_target_commits(self):
        await self._run_target([16, 8], expected_success=True)
        await self._run_target([7, 8], expected_success=False)


if __name__ == "__main__":
    unittest.main()
