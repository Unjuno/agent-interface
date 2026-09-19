"""Receipt-revalidated one-tile fixture behind the private stopped-event socket."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
import stopped_socket_v1 as bridge

entry = HERE / "mindustry_single_tile_interactive_v3.py"
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, value in enumerate(args) if str(value).endswith("interactive_v27.py"))
    args[index] = str(entry)
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
if __name__ == "__main__":
    bridge.main()
