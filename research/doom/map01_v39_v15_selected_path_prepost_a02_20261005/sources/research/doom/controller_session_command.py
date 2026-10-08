def session_command(args, runtime):
    # Keep the established v12 session as the default. The opt-in v15 wrapper
    # adds scorer-only progress sampling and per-key release telemetry without
    # exposing scorer state through the controller event stream.
    session = ("session_map01_v15.py"
               if getattr(args, "measurement_session", False)
               else "session_map01_v12.py")
    return [sys.executable, str(HERE / session),
            "--out", str(runtime), "--seed", str(args.seed),
            "--timeout-seconds", "600", "--skill", "1",
            "--load-fixture-manifest", str(args.load_fixture_manifest.resolve())]

