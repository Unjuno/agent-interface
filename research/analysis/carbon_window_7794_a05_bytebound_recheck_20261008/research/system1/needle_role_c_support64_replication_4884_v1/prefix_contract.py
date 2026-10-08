"""Shared zero-training/formal prefix contract."""
import torch

def tensor_bytes(t):
    return bytes(t.detach().cpu().contiguous().view(torch.uint8).reshape(-1).tolist())

def verify_prefix(upstream, seed):
    support64=upstream.data(64,seed+3)
    support16=upstream.data(16,seed+3)
    if support64.shape!=(64,upstream.D) or support16.shape!=(16,upstream.D): raise ValueError("shape")
    if support64.dtype!=support16.dtype: raise ValueError("dtype")
    if not torch.equal(support64[:16],support16): raise ValueError("values")
    if tensor_bytes(support64[:16])!=tensor_bytes(support16): raise ValueError("bytes")
    return support64,support16
