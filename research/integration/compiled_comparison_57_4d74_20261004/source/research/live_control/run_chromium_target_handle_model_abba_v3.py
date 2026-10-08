"""Repeat live ABBA with short session aliases backed by private handle IDs."""
import run_chromium_target_handle_model_abba_v1 as shared
import run_chromium_target_handle_model_abba_v2 as host


shared.OUT = shared.HERE / "results/chromium-target-handle-model-abba-03"
host.shared.OUT = shared.OUT

original_popen = shared.subprocess.Popen


def alias_backend_popen(args, **kwargs):
    args = list(args)
    for index, value in enumerate(args):
        if str(value).endswith("target_handle_chromium_socket_v2.py"):
            args[index] = str(shared.HERE / "target_handle_chromium_socket_v3.py")
        elif value == "chromium-target-handle-v2":
            args[index] = "chromium-target-handle-v3"
    return original_popen(args, **kwargs)


shared.subprocess.Popen = alias_backend_popen
original_parse = shared.parse_model


def parse_model(output, mode):
    result = original_parse(output, mode)
    if mode == "handle":
        target = result["typed"].get("target", {})
        result["strict_shape_correct"] = target == {
            "kind": "handle",
            "x": 0,
            "y": 0,
            "target_handle": "save_form",
            "dx": 20,
            "dy": 9,
        }
    return result


shared.parse_model = parse_model
original_model_call = host.model_call


def model_call(root, index, mode, prompt, image):
    return original_model_call(
        root, index, mode, prompt.replace("h_save_form", "save_form"), image
    )


shared.model_call = model_call


if __name__ == "__main__":
    shared.main()
