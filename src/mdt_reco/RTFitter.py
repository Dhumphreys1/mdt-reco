import os
import numpy as np
import yaml
import matplotlib.pyplot as plt
import mdt_reco

from numpy.polynomial.chebyshev import Chebyshev
from scipy.ndimage import center_of_mass

#from .Geometry import Chamber
#from .TrackFitter import TrackFitter
#from .Event import Event

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.normpath(os.path.join(script_dir, '../../data/events_10k.npy'))
data = np.load(data_path, allow_pickle=True)

with open("../../configs/ci_config.yaml") as f:
    config = yaml.safe_load(f)
chamber = mdt_reco.geo(config)

iterations = 50

events = []
events = []
for event in data:
    empty_event = mdt_reco.event()
    empty_event['tdc_id'] = event['tdc'].astype(np.uint8)
    empty_event['channel'] = event['channel'].astype(np.uint8)
#    empty_event['drift_time'] = event['drift_time'].astype(np.float32)
    empty_event['tdc_time'] = event['tdc_time'].astype(np.float32)
    empty_event['drift_time'] = ((event['tdc_time'] - 70)/830).astype(np.float32)
    empty_event['x'] = event['x'].astype(np.float32)
    empty_event['y'] = event['y'].astype(np.float32)
    events.append(empty_event)

TrackFitter = mdt_reco.trackFitter()
for iteration in range(iterations):
    distances = []
    times = []

    for event_num, event in enumerate(events):
        if iteration == 0:
            r = np.full_like(event['x'], 15.0, dtype=np.float32)
        else:
            r = event["drift_radius"]
       
        theta, d = TrackFitter.fitCosmic(event["x"], event["y"], r)
        event["theta"] = theta
        event["d"] = d

                
        dist = event.getTrackDist()
        time = event["drift_time"]
        distances = np.concatenate((distances, dist))
        times = np.concatenate((times, time))
#        if event_num == 127:
#            event.drawTrack(chamber, save=True, file_dir="./figures", file_name=f"debug_it_{iteration}_ev_{event_num}")
#            print(f"Dist : {dist}")
#            print(f"Time : {time}")

    fig, ax = plt.subplots()
    H, xedges, yedges = np.histogram2d(times, distances, bins=50)
    xcenters = 0.5 * (xedges[:-1] + xedges[1:])
    ycenters = 0.5 * (yedges[:-1] + yedges[1:])
    pcm = ax.pcolormesh(xedges, yedges, H.T, cmap='plasma')
    fig.colorbar(pcm, ax=ax, label='Counts')

    # Find ridge (max y-bin index for each x column)
    ridge_y_indices = np.argmax(H, axis=1)
    ridge_y_values = []
    filtered_x = []
    filtered_y = []
    for i in range(H.shape[0]):
        column = H[i, :]
        total = column.sum()
        if total == 0:
            continue
        probs = column / total
        com_idx = center_of_mass(probs)[0]
        var_idx = np.sum(probs * (np.arange(len(probs)) - com_idx)**2)
        std_idx = np.sqrt(var_idx)
        y_com = ycenters[int(round(com_idx))]
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
    ax.scatter(filtered_x, filtered_y, s=8, color='cyan', alpha=0.6, label='Filtered ridge points')

    # fit Chebyshev polynomials
#    degree = 4
#    cheb_fit = Chebyshev.fit(filtered_x, filtered_y, degree)
#    x_fit = np.linspace(0, max(filtered_x), 200)
#    def fit_with_constraint(x): # y(0) = 0
#        return cheb_fit(x) - cheb_fit(0)
#    y_fit = fit_with_constraint(x_fit)

    degree = 4
    coeff = np.polyfit(filtered_x, filtered_y, degree)
    poly = np.poly1d(coeff)
    x_fit = np.linspace(0, max(filtered_x), 200)
    y_fit = poly(x_fit)

    ax.plot(x_fit, y_fit, color='white', linewidth=2, label='Chebyshev fit')
    ax.legend()
    ax.set_xlabel("Time")
    ax.set_ylabel("Distance of closest approach")
    plt.savefig(f"figures/rt_iteration_{iteration}.jpg", format='jpg', dpi=300)
    plt.close(fig)

    for event_num, event in enumerate(events): # set the drift radius for the next iteration
        drift_time = event["drift_time"]
#        print(f"Iteration {iteration} / {iterations - 1}")
        drift_radius = poly(drift_time)
        drift_radius = np.float32(drift_radius)
        event["drift_radius"] = drift_radius
 #       if event_num == 127:
 #           print(f"Drift radius : {drift_radius}")
