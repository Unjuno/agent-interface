from __future__ import annotations

import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def forward_logits(x, model, extent=False, cache=False):
    kernel, bias, dense, output_bias = model
    windows = np.lib.stride_tricks.sliding_window_view(x[:, 0], (3, 3), axis=(1, 2))
    pre = np.einsum("nhwij,fij->nhwf", windows, kernel, optimize=True) + bias
    activations = np.maximum(pre, 0)
    flat = activations.reshape(len(x), -1, 4)
    maxima = np.max(flat, axis=1)
    pooled = np.concatenate((maxima, np.mean(flat, axis=1)), axis=1) if extent else maxima
    logits = pooled @ dense + output_bias
    if cache:
        argmax = np.argmax(flat, axis=1)
        return logits, (windows, pre, activations.shape, argmax, flat.shape)
    return logits


def initialize(seed, extent=False):
    rng = np.random.default_rng(seed)
    kernel = rng.normal(0, 0.04, (4, 3, 3)).astype(np.float32)
    bias = np.zeros(4, np.float32)
    dense = np.zeros(8 if extent else 4, np.float32)
    dense[:4] = rng.normal(0, 0.04, 4).astype(np.float32)
    return kernel, bias, dense, np.float32(0)


def loss_and_gradients(x, y, model, extent=False):
    logits, (windows, pre, activation_shape, argmax, flat_shape) = forward_logits(x, model, extent, True)
    probabilities = sigmoid(logits)
    dz = (probabilities - y) / len(y)
    flat = np.maximum(pre, 0).reshape(flat_shape)
    maxima = np.max(flat, axis=1)
    dense_max = model[2][:4]
    dense_mean = model[2][4:] if extent else None
    dense_gradient = np.zeros_like(model[2])
    dense_gradient[:4] = maxima.T @ dz
    if extent:
        dense_gradient[4:] = np.mean(flat, axis=1).T @ dz
    output_bias_gradient = np.sum(dz)

    activation_gradient = np.zeros(flat_shape, np.float32)
    activation_gradient[
        np.arange(len(x))[:, None], argmax, np.arange(4)[None, :]
    ] = dz[:, None] * dense_max[None, :]
    if extent:
        activation_gradient += dz[:, None, None] * dense_mean[None, None, :] / flat_shape[1]
    activation_gradient = activation_gradient.reshape(activation_shape) * (pre > 0)
    kernel_gradient = np.einsum("nhwij,nhwf->fij", windows, activation_gradient, optimize=True)
    bias_gradient = np.sum(activation_gradient, axis=(0, 1, 2))
    loss = np.mean(np.logaddexp(0.0, logits.astype(np.float64)) - y * logits.astype(np.float64))
    gradients = (kernel_gradient, bias_gradient, dense_gradient, np.asarray(output_bias_gradient, dtype=np.float32))
    return loss, gradients


def fit(x, y, seed, steps=1000, lr=0.2, extent=False):
    model = list(initialize(seed, extent))
    for _ in range(steps):
        _, gradients = loss_and_gradients(x, y, model, extent)
        for index, gradient in enumerate(gradients):
            model[index] -= lr * gradient
    return tuple(model)
