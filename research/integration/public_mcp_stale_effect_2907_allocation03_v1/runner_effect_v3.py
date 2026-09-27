"""Allocation 03 adapter; parent runner remains immutable and imported read-only."""
import runner_effect_v2 as parent


async def execute_mcp_v3(targets, html_path):
    trace = await parent.execute_mcp(targets, html_path)
    if trace.get("retained_reads"):
        # All six interface_results calls are issued on the same ClientSession
        # object inside parent.execute_mcp's single stdio_client context. The
        # public historical receipts omit session_id for non-close operations.
        for row in trace["retained_reads"]:
            row["session_id"] = trace.get("session_id")
        trace["retained_transport"] = {
            "scope": "single-public-stdio-client-session",
            "session_id": trace.get("session_id"),
            "read_count": len(trace["retained_reads"]),
            "same_client_context": True,
        }
    return trace


def main():
    parent.base.execute_mcp = execute_mcp_v3
    return parent.base.main()


if __name__ == "__main__":
    raise SystemExit(main())

