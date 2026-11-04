from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LEDGER = REPO / "research" / "integration" / "standard_mcp_task_ledger_57_v1"
sys.path.insert(0, str(LEDGER))

from app_server_file_spool_v1 import publish_request  # noqa: E402
from app_server_spool_worker_v1 import process_one_request, command as safe_command  # noqa: E402

ATTEMPT_ID = "issue57-r93-a01"
MODEL = "gpt-6-luna"
EFFORT = "medium"
TIMEOUT = 90
SOURCE_IMAGE = (REPO / "research" / "integration" / "issue57_calc_sameframe_live_20261104_r91"
    / "r91-a01" / "server-output" / "ee25a3f96572450dbf94164898859032"
    / "calc-review" / "images" / "79aec2607b494109aabdc5b563f3c26b.png")
EXPECTED_IMAGE_SHA256 = "a236f067e223e6f069dbdc3a8663813cef4bba209c87247a9a16f124d3975803"
EXPECTED_CLI_PATH = r"C:\Users\user\AppData\Local\OpenAI\Codex\bin\22cfb1d302613eae\codex.exe"
EXPECTED_CLI_SHA256 = "3097c909fb6d5cd63510d44aceb1d42df9f6e85722a3e447e477def1ecf60e16"
ROOT = HERE / "r93-a01"
SPOOL = ROOT / "spool"
IMAGE = SPOOL / "input" / "calc-review.png"

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["visible_sheet", "selected_cell", "cells_blank", "proposed_actions",
                 "confidence", "visual_note"],
    "properties": {
        "visible_sheet": {"type": "string", "enum": ["Sheet1", "unknown"]},
        "selected_cell": {"type": "string", "enum": ["A1", "A2", "other", "unknown"]},
        "cells_blank": {"type": "boolean"},
        "proposed_actions": {"type": "array", "minItems": 1, "maxItems": 4,
            "items": {"type": "string", "enum": ["enter_731_in_A1", "enter_864_in_A2",
                "save", "abstain"]}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "visual_note": {"type": "string", "maxLength": 220},
    },
}
PROMPT = (
    "Inspect the attached Calc screenshot. It shows the state before any task input. "
    "The requested task is to enter 731 in A1, enter 864 in A2, and save the workbook. "
    "Return only the required structured plan: identify the visible sheet and selected "
    "cell, say whether cells are blank, and list the safe action order. Do not claim that "
    "any action has happened or that the task is complete. If uncertain, include abstain."
)


def main() -> int:
    if ROOT.exists():
        raise RuntimeError("attempt packet already exists; refusing a second generation")
    source_bytes = SOURCE_IMAGE.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != EXPECTED_IMAGE_SHA256:
        raise RuntimeError("frozen source image hash mismatch")
    cli = shutil.which("codex.exe") or shutil.which("codex")
    if not cli:
        raise RuntimeError("Codex CLI is unavailable; no model attempt was started")
    cli_path = Path(cli).resolve(strict=True)
    if str(cli_path).lower() != EXPECTED_CLI_PATH.lower():
        raise RuntimeError("Codex CLI path differs from the frozen executable")
    cli_digest = hashlib.sha256(cli_path.read_bytes()).hexdigest()
    if cli_digest != EXPECTED_CLI_SHA256:
        raise RuntimeError("Codex CLI digest differs from the frozen executable")
    ROOT.mkdir(parents=True)
    IMAGE.parent.mkdir(parents=True)
    IMAGE.write_bytes(source_bytes)
    (ROOT / "cli.json").write_text(json.dumps({
        "path": str(cli_path),
        "sha256": cli_digest,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    published = publish_request(SPOOL, attempt_id=ATTEMPT_ID, prompt=PROMPT,
        output_schema=SCHEMA, image_path=IMAGE, model=MODEL, effort=EFFORT)
    (ROOT / "published-request.json").write_text(json.dumps(published,
        sort_keys=True, indent=2) + "\n", encoding="utf-8")

    # Do not pass the active desktop thread/tool-pipe identity into the isolated
    # read-only App Server process. Authentication remains the configured Codex
    # login; no credential values are read or copied into the evidence packet.
    for name in ("CODEX_APP_TOOLS_PIPE_PATH", "CODEX_SESSION_ID", "CODEX_THREAD_ID",
                 "CODEX_TOOL_CALL_ID", "CODEX_TASK_WORKSPACE_VERIFYING_IDENTITY",
                 "CODEX_MCP_NODE_PATH", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE"):
        os.environ.pop(name, None)

    try:
        record = process_one_request(SPOOL,
            command=safe_command(cli_path),
            cwd=str(REPO), model=MODEL, effort=EFFORT,
            expected_schema_sha256=published["output_schema_sha256"],
            turn_timeout=TIMEOUT)
    except BaseException as exc:
        record = {"status": "unknown", "answer_eligible": False, "usage": None,
            "answer": None, "error": {"type": type(exc).__name__, "message": str(exc)},
            "completed_agent_messages": 0}
        (ROOT / "worker-error.json").write_text(json.dumps(record,
            sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (ROOT / "worker-result.json").write_text(json.dumps(record,
        sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"attempt_id": ATTEMPT_ID, "status": record.get("status"),
        "answer_eligible": record.get("answer_eligible"),
        "usage": record.get("usage"),
        "completed_agent_messages": record.get("completed_agent_messages")},
        sort_keys=True))
    return 0 if record.get("status") == "completed" and record.get("answer_eligible") else 2


if __name__ == "__main__":
    raise SystemExit(main())


