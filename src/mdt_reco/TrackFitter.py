import numpy as np
from numba import njit


@njit
def _compute_d_opt(x, y, theta):
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    return np.mean(x * cos_t + y * sin_t)


@njit
def _objective(theta, x, y, r):
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # Inline _compute_d_opt
    d = 0.0
    for i in range(x.shape[0]):
        d += x[i] * cos_t + y[i] * sin_t
    d /= x.shape[0]

    # Compute residuals
    err_sum = 0.0
    for i in range(x.shape[0]):
        dist = x[i] * cos_t + y[i] * sin_t - d
        err = abs(dist) - r[i]
        if err > 0:
            err_sum += err * err
    return err_sum


@njit
def _find_best_theta(x, y, r, n_steps=100):
    best_obj = 1e12
    best_theta = 0.0
    for i in range(n_steps):
        theta = i * np.pi / n_steps
        obj = _objective(theta, x, y, r)
        if obj < best_obj:
            best_obj = obj
            best_theta = theta
    return best_theta


@njit
def _line_from_normal(theta, d):
    tolerance = 1e-5
    if np.abs(np.sin(theta)) < tolerance:
        return 1e10, d / np.cos(theta)
    m = -np.cos(theta) / np.sin(theta)
    b = d / np.sin(theta)
    return m, b


class TrackFitter:
    def fitCosmic(self, x, y, r, n_steps, normal_form=True):
        theta = _find_best_theta(x, y, r, n_steps)
        d = _compute_d_opt(x, y, theta)
        if normal_form:
            return np.float32(theta), np.float32(d)
        return _line_from_normal(theta, d)
