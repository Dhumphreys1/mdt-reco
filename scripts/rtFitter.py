import argparse
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import center_of_mass

import mdt_reco


# NEEDS TO BE REFACTORED
def main():  # noqa: PLR0915
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file"
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "../configs", args.config)
    config = mdt_reco.configParser(config_path)
    output_dir = f"{script_dir}/../output/{config['General']['run_name']}"
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(figure_dir, exist_ok=True)

    iterations = config["RTFitter"]["iterations"]

    input_file = f"{output_dir}/{config['General']['input_file']}.pkl"
    with open(input_file, "rb") as f:
        events = pickle.load(f)

    TrackFitter = mdt_reco.trackFitter()
    for iteration in range(iterations):
        distances = []
        times = []

        for event in events:
            if iteration == 0:
                r = np.full_like(event["x"], 15.0, dtype=np.float32)
            else:
                r = event["drift_radius"]
            theta, d = TrackFitter.fitCosmic(event["x"], event["y"], r)
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
        pcm = ax.pcolormesh(xedges, yedges, H.T, cmap="plasma")
        fig.colorbar(pcm, ax=ax, label="Counts")

        # Find ridge (max y-bin index for each x column)
        filtered_x = []
        filtered_y = []
        for i in range(H.shape[0]):
            column = H[i, :]
            total = column.sum()
            if total == 0:
                continue
            probs = column / total
            com_idx = center_of_mass(probs)[0]
            var_idx = np.sum(probs * (np.arange(len(probs)) - com_idx) ** 2)
            std_idx = np.sqrt(var_idx)
            y_com = ycenters[round(com_idx)]
            y_std = std_idx * (ycenters[1] - ycenters[0])

            k = 1.0  # standard deviation threshold
            y_min = y_com - k * y_std
            y_max = y_com + k * y_std

            x_val = xcenters[i]
            for j in range(len(ycenters)):
                y_val = ycenters[j]
                if y_min <= y_val <= y_max and H[i, j] > 0:
                    filtered_x.append(x_val)
                    filtered_y.append(y_val)

        filtered_x = np.array(filtered_x)
        filtered_y = np.array(filtered_y)
        ax.scatter(
            filtered_x,
            filtered_y,
            s=8,
            color="cyan",
            alpha=0.6,
            label="Filtered ridge points",
        )

        degree = config["RTFitter"]["degree"]
        coeff = np.polyfit(filtered_x, filtered_y, degree)
        file_name = f"/rt_coefficients_degree_{degree}.npy"
        file_path = output_dir + file_name
        np.save(file_path, coeff)
        poly = np.poly1d(coeff)
        x_fit = np.linspace(0, max(filtered_x), 200)
        y_fit = poly(x_fit)

        ax.plot(x_fit, y_fit, color="white", linewidth=2, label="Chebyshev fit")
        ax.legend()
        ax.set_xlabel("Time")
        ax.set_ylabel("Distance of closest approach")
        plt.savefig(
            figure_dir + f"/rt_iteration_{iteration}.jpg", format="jpg", dpi=300
        )
        plt.close(fig)

        for event in events:  # set the drift radius for the next iteration
            drift_time = event["drift_time"]
            drift_radius = poly(drift_time)
            drift_radius = np.float32(drift_radius)
            event["drift_radius"] = drift_radius
    return 0


if __name__ == "__main__":
    main()
