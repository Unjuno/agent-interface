"""Offline stand-in for the Codex CLI; records argv/stdin and returns JSONL."""
import json
import os
import sys

argv = sys.argv[1:]
prompt = sys.stdin.read()
with open(os.environ["FAKE_CLI_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps({"argv": argv, "prompt": prompt}, sort_keys=True) + "\n")
mode = "resume" if argv[:2] == ["exec", "resume"] else "initial"
print(json.dumps({"type": "thread.started", "thread_id": "fixture-thread-5791"}), flush=True)
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"fixture": True, "mode": mode})}}), flush=True)
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 2}}), flush=True)
