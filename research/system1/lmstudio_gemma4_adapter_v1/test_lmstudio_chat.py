import base64
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError

from lmstudio_chat import call_local


class _StubServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, status=200, response=None, redirect=None):
        self.status = status
        self.response = response or {}
        self.redirect = redirect
        self.requests = []
        super().__init__(("127.0.0.1", 0), _Handler)


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers["Content-Length"])
        self.server.requests.append(json.loads(self.rfile.read(size)))
        if self.server.redirect:
            self.send_response(302)
            self.send_header("Location", self.server.redirect)
            self.end_headers()
            return
        body = json.dumps(self.server.response).encode("utf-8")
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


class LMStudioChatContractTests(unittest.TestCase):
    def setUp(self):
        self.answer = {
            "decision": "TARGET",
            "target": "Publish",
            "container": "Project Atlas",
            "state": "ENABLED",
            "reason": None,
        }
        self.schema = {
            "type": "object",
            "properties": {"decision": {"type": "string"}},
            "required": ["decision"],
            "additionalProperties": False,
        }
        self.response = {
            "id": "chatcmpl-local-1",
            "model": "google/gemma-4-e4b@q4_k_m",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(self.answer)},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 77,
                "completion_tokens": 21,
                "total_tokens": 98,
                "prompt_tokens_details": {"cached_tokens": 4},
                "completion_tokens_details": {"reasoning_tokens": 2},
            },
        }
        self.server = _StubServer(response=self.response)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def invoke(self, endpoint=None, schema=None):
        return call_local(
            endpoint_url=endpoint or self.endpoint,
            model="google/gemma-4-e4b",
            system_prompt="Return only the declared grounded decision.",
            intent="Select Publish in Project Atlas if enabled.",
            image_bytes=b"\x89PNG\r\n\x1a\nfixture",
            schema=self.schema if schema is None else schema,
            timeout_s=3,
        )

    def test_sends_one_schema_constrained_image_request_without_tools(self):
        result = self.invoke()
        self.assertEqual(len(self.server.requests), 1)
        request = self.server.requests[0]
        self.assertEqual(request["model"], "google/gemma-4-e4b")
        self.assertEqual(request["temperature"], 0)
        self.assertEqual(request["top_p"], 1)
        self.assertEqual(request["max_tokens"], 256)
        self.assertIs(request["stream"], False)
        self.assertNotIn("tools", request)
        self.assertEqual(request["response_format"], {
            "type": "json_schema",
            "json_schema": {"name": "grounded_decision", "strict": True, "schema": self.schema},
        })
        user_content = request["messages"][1]["content"]
        self.assertEqual(user_content[0], {
            "type": "text", "text": "Select Publish in Project Atlas if enabled."
        })
        image_url = user_content[1]["image_url"]["url"]
        self.assertEqual(image_url, "data:image/png;base64," + base64.b64encode(
            b"\x89PNG\r\n\x1a\nfixture"
        ).decode("ascii"))
        self.assertEqual(result["decision"], self.answer)
        self.assertEqual(result["requested_model"], "google/gemma-4-e4b")
        self.assertEqual(result["actual_model"], "google/gemma-4-e4b@q4_k_m")
        self.assertEqual(result["usage"]["input_tokens"], 77)
        self.assertEqual(result["usage"]["output_tokens"], 21)
        self.assertEqual(result["usage"]["cached_input_tokens"], 4)
        self.assertEqual(result["usage"]["reasoning_output_tokens"], 2)
        self.assertGreater(result["latency_ns"], 0)

    def test_missing_usage_counters_remain_unavailable_not_zero(self):
        del self.response["usage"]["completion_tokens"]
        del self.response["usage"]["total_tokens"]
        del self.response["usage"]["prompt_tokens"]
        del self.response["usage"]["prompt_tokens_details"]
        del self.response["usage"]["completion_tokens_details"]
        result = self.invoke()
        self.assertIsNone(result["usage"]["input_tokens"])
        self.assertIsNone(result["usage"]["output_tokens"])
        self.assertIsNone(result["usage"]["total_tokens"])
        self.assertIsNone(result["usage"]["cached_input_tokens"])
        self.assertIsNone(result["usage"]["reasoning_output_tokens"])
        self.assertIsNone(result["usage"]["cost_usd"])

    def test_rejects_non_loopback_endpoint_before_sending_image(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            self.invoke("http://example.com:1234/v1/chat/completions")
        self.assertEqual(self.server.requests, [])

    def test_rejects_open_schema_before_sending_image(self):
        open_schema = dict(self.schema)
        open_schema["additionalProperties"] = True
        with self.assertRaisesRegex(ValueError, "closed object"):
            self.invoke(schema=open_schema)
        self.assertEqual(self.server.requests, [])

    def test_rejects_redirect_instead_of_forwarding_private_image(self):
        self.server.redirect = "http://example.com/collect"
        with self.assertRaises(HTTPError):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)

    def test_rejects_invalid_json_content_without_retry(self):
        self.server.response["choices"][0]["message"]["content"] = "not json"
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)

    def test_rejects_non_success_http_status_without_retry(self):
        self.server.status = 503
        with self.assertRaises(HTTPError):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)

    def test_rejects_malformed_token_counter_instead_of_coercing_it(self):
        self.response["usage"]["prompt_tokens"] = "77"
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)

    def test_rejects_truncated_generation_without_parsing_partial_json(self):
        self.server.response["choices"][0]["finish_reason"] = "length"
        with self.assertRaisesRegex(ValueError, "did not finish normally"):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)

    def test_rejects_multiple_choices_instead_of_silently_selecting_one(self):
        self.server.response["choices"].append(self.server.response["choices"][0])
        with self.assertRaisesRegex(ValueError, "exactly one choice"):
            self.invoke()
        self.assertEqual(len(self.server.requests), 1)


if __name__ == "__main__":
    unittest.main()
