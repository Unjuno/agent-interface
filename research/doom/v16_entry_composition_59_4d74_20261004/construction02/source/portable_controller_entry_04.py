from pathlib import Path
import hashlib
import portable_controller_entry_03 as previous
EXPECTED_SESSION_SHA = "526f6ef9f07953c053cc3eed136b1c1144e071dd35c0b9493b0c9820889ddefe"
def install():
    controller = previous.install()
    target = controller.HERE / "session_map01_v16.py"
    if hashlib.sha256(target.read_bytes()).hexdigest() != EXPECTED_SESSION_SHA:
        raise ValueError("V16 session source hash mismatch")
    original = controller.session_command
    def session_command(args, runtime):
        argv = original(args, runtime)
        if Path(argv[1]) != controller.HERE / "session_map01_v12.py":
            raise ValueError("unexpected original session selection")
        return [argv[0], str(target), *argv[2:]]
    controller.session_command = session_command
    return controller
