"""Whitelist a small, path-free summary of private App Server stderr."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: redact_stderr.py PRIVATE_STDERR PUBLIC_SUMMARY")
    raw_path, output_path = map(Path, sys.argv[1:])
    raw = raw_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    summary = {
        "private_stderr_sha256": hashlib.sha256(raw).hexdigest(),
        "private_stderr_bytes": len(raw),
        "unknown_mock_model_warning_count": text.count("Unknown model mock-model"),
        "curated_plugin_git_sync_failed": "git sync failed for curated plugin sync" in text,
        "git_sync_error_mentions_local_xcode_license": "You have not agreed to the Xcode license agreements" in text,
        "external_featured_plugin_request_attempted":
            "https://chatgpt.com/backend-api/plugins/featured?platform=codex" in text,
        "external_featured_plugin_response": "401 Unauthorized" if
            "401 Unauthorized" in text else "not observed",
        "external_request_response_body_summary": "Unauthorized" if
            '"detail":"Unauthorized"' in text or '"detail": "Unauthorized"' in text else "not observed",
        "authorization_headers_retained": False,
        "scope_note": "This summary is parsed from local stderr only. The request headers were not captured, so it does not establish whether an authorization header was sent."
    }
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
