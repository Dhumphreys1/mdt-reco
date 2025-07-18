import numpy as np
from numba import njit


def getInitialT0(time_counts, time_centers):
    threshold = time_counts.max() / 10
    nonzero_indices = np.where(time_counts > threshold)[0]

    if nonzero_indices.size > 0:
        return time_centers[nonzero_indices[1]]


def getInitialTMax(time_counts, time_centers):
    threshold = time_counts.max() / 10
    nonzero_indices = np.where(time_counts > threshold)[0]
    if nonzero_indices.size > 0:
        return time_centers[nonzero_indices[-2]]


@njit
def _t0_objective(time_counts, time_centers, min_time, max_time, t0):
    err2: np.float32 = 0
    amplitude: np.float32 = 0
    total_bins = len(time_counts)
    sorted_indices = np.argsort(time_counts)[::-1]
    bins_to_avg = int(total_bins / 10)
    largest_counts = time_counts[sorted_indices[:bins_to_avg]]
    for count in largest_counts:
        amplitude += count
    amplitude /= len(largest_counts)

    center_half_width = 0.5 * (time_centers[1] - time_centers[0])
    for k in range(len(time_centers)):
        center = time_centers[k]
        if (
            center - center_half_width > min_time
            and center + center_half_width < max_time
        ):
            if center + center_half_width <= t0:
                err2 += (2 * time_counts[k] * center_half_width) ** 2
            elif center - center_half_width >= t0:
                err2 += 4 * ((time_counts[k] - amplitude) * center_half_width) ** 2
            else:
                delta_t = t0 - center
                w1 = center_half_width + delta_t
                w2 = center_half_width - delta_t
                err2 += (w1 * time_counts[k]) ** 2
                err2 += (w2 * (time_counts[k] - amplitude)) ** 2
    return err2


@njit
def _tmax_objective(time_counts, time_centers, min_time, max_time, tmax):
    err2: np.float32 = 0
    amplitude: np.float32 = 0

    idx = np.searchsorted(time_centers, tmax)
    running_bins = int(len(time_counts) / 10)
    window = time_counts[idx - running_bins : idx]

    for i in range(len(window)):
        amplitude += window[i]
    amplitude /= len(window)

    center_half_width = 0.5 * (time_centers[1] - time_centers[0])
    for k in range(len(time_centers)):
        center = time_centers[k]
        if (
            center - center_half_width > min_time
            and center + center_half_width < max_time
        ):
            if center - center_half_width >= tmax:
                err2 += (2 * time_counts[k] * center_half_width) ** 2
            elif center + center_half_width <= tmax:
                err2 += (2 * (time_counts[k] - amplitude) * center_half_width) ** 2
            else:
                delta_t = tmax - center
                w1 = center_half_width + delta_t
                w2 = center_half_width - delta_t
                err2 += (w1 * (time_counts[k] - amplitude)) ** 2
                err2 += (w2 * time_counts[k]) ** 2
    return err2


@njit
def _find_t0(time_counts, time_centers, t0_initial, n_steps):
    min_time = t0_initial - 20
    max_time = t0_initial + 80
    delta_time = max_time - min_time
    best_obj = 1e12
    best_t0 = t0_initial
    for n in range(n_steps):
        t0 = min_time + (delta_time * n) / n_steps
        obj = _t0_objective(time_counts, time_centers, min_time, max_time, t0)
        if obj < best_obj:
            best_obj = obj
            best_t0 = t0
    return best_t0


@njit
def _find_tmax(time_counts, time_centers, tmax_initial, n_steps):
    min_time = tmax_initial - 75
    max_time = tmax_initial + 75
    delta_time = max_time - min_time
    best_obj = 1e12
    best_tmax = tmax_initial
    for n in range(n_steps):
        tmax = min_time + delta_time * n / n_steps
        obj = _tmax_objective(time_counts, time_centers, min_time, max_time, tmax)
        if obj < best_obj:
            best_obj = obj
            best_tmax = tmax
    return best_tmax


@njit
def _gaussian(adc_centers, A, mu, sigma):
    return A * np.exp(-0.5 * ((adc_centers - mu) / sigma) ** 2)


@njit
def _adc_objective(params, adc_counts, adc_centers):
    A, mu, sigma = params
    y_fit = _gaussian(adc_centers, A, mu, sigma)
    return np.sum((adc_counts - y_fit) ** 2)


@njit
def _gradient(params, adc_counts, adc_centers, eps=1e-5):
    grad = np.zeros_like(params)
    for i in range(len(params)):
        params_eps = params.copy()
        params_eps[i] += eps
        grad[i] = (
            _adc_objective(params_eps, adc_counts, adc_centers)
            - _adc_objective(params, adc_counts, adc_centers)
        ) / eps
    return grad


@njit
def _adc_fit(
    adc_counts, adc_centers, initial_params, lr=1e-4, max_iter=10000, tol=1e-6
):
    params = initial_params.copy()
    for _ in range(max_iter):
        grad = _gradient(params, adc_centers, adc_counts)
        params -= lr * grad
        if np.linalg.norm(grad) < tol:
            break
    return params


def _hist_params(counts, bin_centers):
    total = np.sum(counts)
    if total == 0:
        return 0.0
    mean = np.sum(bin_centers * counts) / total
    variance = np.sum(counts * (bin_centers - mean) ** 2) / total
    return mean, np.sqrt(variance)


class TDCFitter:
    def fitT0(self, time_counts, time_centers, n_steps=100):
        t0_initial = getInitialT0(time_counts, time_centers)
        return _find_t0(time_counts, time_centers, t0_initial, n_steps)

    def fitTMax(self, time_counts, time_centers, n_steps=100):
        tmax_initial = getInitialTMax(time_counts, time_centers)
        return _find_tmax(time_counts, time_centers, tmax_initial, n_steps)

    def fitADC(self, adc_counts, adc_centers, lr=1e-4, max_iter=10000, tol=1e-7):
        """
        Assume adc curve is normally distributed.
        Set initial amplitude to the average of the 10% largest bins.
        Calculate mean and spread of histogram directly for initial params.
        """

        sorted_indices = np.argsort(adc_counts)[::-1]
        bins_to_avg = int(len(sorted_indices) / 20)
        initial_amplitude = np.mean(adc_counts[sorted_indices[:bins_to_avg]])
        initial_mean, initial_spread = _hist_params(adc_counts, adc_centers)
        initial_params = np.array([initial_amplitude, initial_mean, initial_spread])
        return _adc_fit(adc_counts, adc_centers, initial_params, lr, max_iter, tol)

    def getTDCInfo(self, events):
        tdc_ids = []
        tdc_times = []
        adc_times = []
        tdc_channels = []

        for event in events:
            tdc_ids.append(event["tdc_id"])
            tdc_times.append(event["tdc_time"])
            adc_times.append(event["adc_time"])
            tdc_channels.append(event["channel"])

        tdc_ids = np.concatenate(tdc_ids)
        tdc_times = np.concatenate(tdc_times)
        adc_times = np.concatenate(adc_times)
        tdc_channels = np.concatenate(tdc_channels)

        return tdc_ids, tdc_times, adc_times, tdc_channels

    def getHisto(
        self, tdc_id, tdc_ids, times, time_binning, tdc_channel=None, tdc_channels=None
    ):
        tdc_mask = tdc_ids == tdc_id
        if tdc_channel is None and tdc_channels is None:
            mask = tdc_mask
        elif tdc_channel is None or tdc_channels is None:
            msg = "Missing channel or channel vector"
            raise ValueError(msg)
        else:
            channel_mask = tdc_channels == tdc_channel
            mask = tdc_mask & channel_mask
        times_for_id = times[mask]
        if len(times_for_id) > 0:
            counts, bin_edges = np.histogram(times_for_id, bins=time_binning)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            return counts.astype(np.int32), bin_centers.astype(np.float32)
