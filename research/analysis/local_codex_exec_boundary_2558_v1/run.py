"""Host-local Codex exec adapter; model output remains non-authoritative."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def run(prompt: str, image: Path, schema: Path, *, model: str = "gpt-5.6-luna") -> dict:
    cli = os.environ.get("CODEX_EXE", "codex.exe")
    command = [cli, "exec", "--ephemeral", "--sandbox", "read-only",
               "--skip-git-repo-check", "--json", "--model", model,
               "--output-schema", str(schema), "--image", str(image), "-"]
    completed = subprocess.run(command, input=prompt + "\n", text=True,
                               capture_output=True, check=True)
    events = [json.loads(line) for line in completed.stdout.splitlines()
              if line.startswith("{")]
    message = next(row["item"]["text"] for row in reversed(events)
                   if row.get("type") == "item.completed")
    usage = next((row.get("usage") for row in reversed(events)
                  if row.get("type") == "turn.completed"), None)
    answer = json.loads(message)
    return {"answer": answer, "usage": usage, "authority_granted": False,
            "model": model, "image": str(image)}


if __name__ == "__main__":
    here = Path(__file__).parent
    print(json.dumps(run(
        "Inspect the attached current observation only. Return READY if it is a "
        "visible editable fixture with an input field; otherwise return YIELD. "
        "Do not run commands, edit files, or claim task success.",
        Path("runtime/results/native-docker-integration-2558-v2/before.png"),
        here / "schema.json"), sort_keys=True))
