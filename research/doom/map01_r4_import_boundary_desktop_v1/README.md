# Docker Desktop MAP01 import-boundary audit

This directory preserves one source-only AST classification allocation for Issue #3903. It analyzes two historical Python files at commit `8652f6a3527d55610185d1103b87d5d9fd8fa985`; neither file nor any dependency is imported, compiled, or executed. The only formal computation is parsing these bytes and eight synthetic strings using Python's standard-library `ast` module.

The target contains a module-level `session_map01_v13.main()` call and therefore must be refused by an import-boundary gate. This is not a claim that the target or its dependency graph is runtime-safe or unsafe beyond that static fact.

Run the unit controls outside the formal allocation with `python -m unittest discover -s tests`. After freezing hashes in `SOURCE_MANIFEST.json`, run `run_formal.ps1` exactly once. Docker invocation disables networking, uses a read-only root/source, bounded resources, and a dedicated evidence directory. Do not rerun the formal allocation.
