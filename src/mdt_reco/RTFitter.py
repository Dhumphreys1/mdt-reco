import os
import numpy as np
import matplotlib.pyplot as plt
from numba import njit
import mdt_reco
from scipy.ndimage import center_of_mass

@njit
def compute_drift_time(tdc_time):
    return (tdc_time - 70) / 830

@njit
def filter_ridge_points(H, xcenters, ycenters):
    filtered_x = []
    filtered_y = []

    for i in range(H.shape[0]):
        column = H[i, :]
        total = np.sum(column)
        if total == 0:
            continue

        max_idx = np.argmax(column)
        y_val = ycenters[max_idx]

        filtered_x.append(xcenters[i])
        filtered_y.append(y_val)

    return np.array(filtered_x), np.array(filtered_y)

@njit
def evaluate_poly(coeff, x):
    y = np.zeros_like(x)
    for i in range(len(coeff)):
        y += coeff[i] * x**(len(coeff) - i - 1)
    return y

class RTFitter:
    def __init__(self, config_path, data=None):
        self.config = mdt_reco.configParser(config_path)
        self.chamber = mdt_reco.geo(self.config)
#        self.data = self._load_data()
        self.output_dir = f"../output/{self.config['General']['run_name']}"
        self.figure_dir = os.path.join(self.output_dir, "figures")
        os.makedirs(self.figure_dir, exist_ok=True)
        self.iterations = self.config["RTFitter"]["iterations"]
        self.degree = self.config["RTFitter"]["degree"]
#        self.events = self._prepare_events()

        if data is not None:
            self.events = data
        else:
            raise ValueError

    def _load_data(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.normpath(os.path.join(script_dir, '../data/events_10k.npy'))
        return np.load(data_path, allow_pickle=True)

    def _prepare_events(self):
        events = []
        for event in self.data:
            e = mdt_reco.event()
            e['tdc_id'] = event['tdc'].astype(np.uint8)
            e['channel'] = event['channel'].astype(np.uint8)
            e['tdc_time'] = event['tdc_time'].astype(np.float32)
            e['drift_time'] = compute_drift_time(e['tdc_time'])
            e['x'] = event['x'].astype(np.float32)
            e['y'] = event['y'].astype(np.float32)
            events.append(e)
        return events

    def fitRTCurve(self):
        TrackFitter = mdt_reco.trackFitter()

        for iteration in range(self.iterations):
            distances = []
            times = []

            for event in self.events:
                r = np.full_like(event['x'], 15.0, dtype=np.float32) if iteration == 0 else event["drift_radius"]
                theta, d = TrackFitter.fitCosmic(event["x"], event["y"], r, 50)
                event["theta"] = theta
                event["d"] = d

                dist = event.getTrackDist()
                time = event["drift_time"]
                distances = np.concatenate((distances, dist))
                times = np.concatenate((times, time))

            fig, ax = plt.subplots()
            H, xedges, yedges = np.histogram2d(times, distances, bins=50)
            xcenters = 0.5 * (xedges[:-1] + xedges[1:])
            ycenters = 0.5 * (yedges[:-1] + yedges[1:])
            pcm = ax.pcolormesh(xedges, yedges, H.T, cmap='plasma')
            fig.colorbar(pcm, ax=ax, label='Counts')

            filtered_x, filtered_y = filter_ridge_points(H, xcenters, ycenters)
            ax.scatter(filtered_x, filtered_y, s=8, color='cyan', alpha=0.6, label='Filtered ridge points')

            coeff = np.polyfit(filtered_x, filtered_y, self.degree)
            file_path = os.path.join(self.output_dir, f"rt_coefficients_degree_{self.degree}.npy")
            np.save(file_path, coeff)

            x_fit = np.linspace(0, max(filtered_x), 200)
            y_fit = evaluate_poly(coeff, x_fit)

            ax.plot(x_fit, y_fit, color='white', linewidth=2, label='Polynomial fit')
            ax.legend()
            ax.set_xlabel("Time")
            ax.set_ylabel("Distance of closest approach")
            plt.savefig(os.path.join(self.figure_dir, f"rt_iteration_{iteration}.jpg"), format='jpg', dpi=300)
            plt.close(fig)

            for event in self.events:
                drift_time = event["drift_time"]
                drift_radius = evaluate_poly(coeff, drift_time)
                event["drift_radius"] = np.float32(drift_radius)
