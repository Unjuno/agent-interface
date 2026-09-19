"""Optional stdio MCP adapter for one explicitly attached native research run."""
import argparse
import json
from pathlib import Path
import threading

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import StrictInt

from agent_review import review_native
from native_exchange_v1 import run


def content(result):
    """Keep metadata complete; return image once as an MCP image block."""
    metadata = dict(result)
    image = metadata.pop('image', None)
    blocks = [TextContent(type='text', text=json.dumps(metadata, allow_nan=False))]
    if image is not None:
        blocks.append(ImageContent(**image))
    return CallToolResult(content=blocks)


def create_server(run_directory):
    root = Path(run_directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('explicit existing native run directory required')
    server = FastMCP('Agent Interface native research session')
    lock = threading.Lock()

    def invoke(operation):
        # One bound run, no concurrent submit/resume processing or automatic retry.
        with lock:
            try:
                return content(operation())
            except Exception as error:
                return CallToolResult(isError=True, content=[TextContent(type='text', text=json.dumps({
                    'status':'client_error', 'error':str(error), 'authority':'none',
                    'program_attempted':None,
                    'recovery':'Inspect the selected stage request/reply. An error does not prove no input; do not replay.'}))])

    @server.tool(structured_output=False)
    def native_observe(stage: StrictInt) -> CallToolResult:
        """Read the retained source for an explicit stage; no recapture or input.

        View its image before choosing an action. A historical frame is not fresh
        authority. No latest-stage guessing and no session allocation.
        """
        def observe():
            if not 1 <= stage <= 64:
                raise ValueError('stage 1..64 required')
            return review_native(root/f'source-{stage}.json', root, compact=True)
        return invoke(observe)

    @server.tool(structured_output=False)
    def native_submit(stage: StrictInt, decision: dict, timeout: float = 5) -> CallToolResult:
        """Submit one explicit decision against its viewed source_sequence.

        Uses existing guarded click/keyboard tail and immutable stage publication.
        Never retry submit after timeout/error. Pending returns decision_sha256:
        use native_resume. Task success is separate from input completion.
        """
        return invoke(lambda: run(root, stage, decision, timeout=timeout, compact=True))

    @server.tool(structured_output=False)
    def native_resume(stage: StrictInt, decision_sha256: str, timeout: float = 5) -> CallToolResult:
        """Read/wait for an exact committed request without publishing input.

        Supply the original pending response's stage and SHA256. Missing/changed
        requests refuse. Owner loss requires reconciliation, never restart/replay.
        """
        return invoke(lambda: run(root, stage, resume=True, decision_sha256=decision_sha256,
                                  timeout=timeout, compact=True))
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory', required=True)
    args = parser.parse_args()
    create_server(args.run_directory).run(transport='stdio')
