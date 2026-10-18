"""Create a whitelist-only public request receipt from the local raw capture."""
import json
import sys
from pathlib import Path

MARKER = "UNTRUSTED CURRENT OBSERVATION: ammo=37"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: redact_requests.py PRIVATE_RAW PUBLIC_REDACTED")
    source, destination = map(Path, sys.argv[1:])
    rows = json.loads(source.read_text(encoding="utf-8"))
    safe = []
    for index, row in enumerate(rows):
        body = row.get("body", {})
        item = {
            "request_index": index,
            "endpoint": "POST /v1/responses" if row.get("path", "").endswith("/responses") else "unexpected",
            "loopback_peer": row.get("client_address", [None])[0] == "127.0.0.1",
            "request_monotonic": row.get("at"),
            "model": body.get("model"),
            "stream": body.get("stream"),
        }
        if index == 0:
            item["initial_request_present"] = True
        if index == 1:
            marker_found = False
            image_urls = []
            for message in body.get("input", []):
                if message.get("role") != "user":
                    continue
                for part in message.get("content", []):
                    if part.get("type") == "input_text" and MARKER in part.get("text", ""):
                        marker_found = True
                        item.setdefault("observation_text", MARKER)
                    if part.get("type") == "input_image":
                        value = part.get("image_url") or part.get("url")
                        if isinstance(value, dict):
                            value = value.get("url")
                        if isinstance(value, str) and value.startswith("data:image/png;base64,"):
                            image_urls.append(value)
            item["observation_marker_present"] = marker_found
            item["observation_images"] = image_urls
        safe.append(item)
    destination.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
