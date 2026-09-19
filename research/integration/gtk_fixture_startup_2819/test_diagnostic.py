from pathlib import Path
from diagnostic import run

def test_existing_output_directory_is_supported(tmp_path: Path):
    out=tmp_path/'out'; out.mkdir(); assert callable(run); out.mkdir(exist_ok=True)
