"""Deterministic alias controls for scoped target-handle v3."""
from PIL import Image

from scoped_target_handle_v3 import TargetHandleStore


def observation(sequence=1, capture_ns=1_000_000, geometry=None):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": {"focus": 10, "surface": 20,
                                "geometry": geometry or [0, 0, 100, 100]}}


def main():
    image = Image.new("RGB", (100, 100), "white")
    for index in range(10):
        image.putpixel((20 + index, 20 + index % 3), (index * 20, 10, 255 - index))
    store = TargetHandleStore("test", id_factory=iter(["private-a", "private-b"]).__next__)
    minted = store.mint("save_form", "window_content", [20, 20, 12, 8],
                        observation(), image, 1_000_100, 1000, 1000, 0,
                        ("window_translation",))
    assert minted["handle"] == "save_form"
    assert minted["private_registry_id_exposed"] is False
    assert "private-a" not in repr(minted)
    resolved = store.resolve_point("save_form", [3, 3], observation(), image,
                                   1_000_200, session_scope="test")
    assert resolved["status"] == "VALID" and resolved["point"] == [23, 23]
    assert resolved["handle"] == "save_form"
    assert "private-a" not in repr(resolved)
    unknown = store.resolve_point("other", [3, 3], observation(), image,
                                  1_000_200, session_scope="test")
    assert unknown["status"] == "MISSING"
    assert unknown["reason"] == "unknown_session_alias"
    try:
        store.mint("save_form", "window_content", [20, 20, 12, 8],
                   observation(), image, 1_000_300, 1000, 1000, 0,
                   ("window_translation",))
    except ValueError as error:
        assert str(error) == "target alias already exists in this session"
    else:
        raise AssertionError("duplicate alias accepted")
    for invalid in ("", "Save", "a-b", "a" * 33):
        candidate = TargetHandleStore("invalid-" + (invalid or "empty"),
                                      id_factory=lambda: "private")
        try:
            candidate.mint(invalid, "window_content", [20, 20, 12, 8],
                           observation(), image, 1_000_300, 1000, 1000, 0,
                           ("window_translation",))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid alias accepted: " + repr(invalid))
    print("scoped_target_handle_v3_probe_passed")


if __name__ == "__main__":
    main()
