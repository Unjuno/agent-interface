"""Load the pinned PyTorch/AutoGluon Mitra runtime in safe import order."""


def load_mitra_runtime():
    import torch
    import torch._dynamo.external_utils  # noqa: F401

    import autogluon.tabular.models.mitra.sklearn_interface as mitra_interface
    from autogluon.tabular.models.mitra.sklearn_interface import MitraClassifier

    return torch, mitra_interface, MitraClassifier

