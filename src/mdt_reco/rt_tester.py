#python frontmatter
import os
import numpy as np
#import pandas as pd
import yaml
import matplotlib.pyplot as plt

from numpy.polynomial.chebyshev import Chebyshev
from scipy.ndimage import center_of_mass

#NOTE TO SELF: these need to be reflected in ../../setup_env.sh so that we have access to 'em

#functions from elsewhere
from Geometry import Chamber


script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.normpath(os.path.join(script_dir, '../../data/events_10k.npy'))

df = np.load(data_path, allow_pickle=True)


#compute first order r(t) curve
def linearFit(data, event):
    hits_x = data[event]["x"]
    hits_y = data[event]["y"]

    #find radii
    linear = np.polynomial.polynomial.Polynomial.fit(hits_x, hits_y, 1)
    return linear


# perpendicular distances to line of best fit
def findPerpDists(data, event):
    linear = linearFit(data, event)
    b, m = linear.convert().coef

    hits_x = data[event]["x"]
    hits_y = data[event]["y"]
    hits_t = data[event]["tdc_time"]  #is this right?
    dists = []
    for i in range(len(hits_x)):
        x_0 = hits_x[i]
        y_0 = hits_y[i]
        dist = np.abs(m * x_0 - y_0 + b) / np.sqrt(m**2 + 1)
        dists.append(dist)

    return dists, hits_t


def aggregatePerpDists(data):
    aggregated_dists = []
    aggregated_times = []

    for event in range(len(data)):
        fPD = findPerpDists(data, event)
        dists = fPD[0]
        times = fPD[1]
        aggregated_dists = np.concatenate((aggregated_dists, dists))
        aggregated_times = np.concatenate((aggregated_times, times))

    return aggregated_dists, aggregated_times


#load configs to make geometry plot
with open("../../configs/ci_config.yaml") as f:
    config = yaml.safe_load(f)

#show chamber
chamber = Chamber(config)


def generatePlots(events_list): #takes list of events to generate plots for
    for event in events_list:

        # display tube hits and line of best fit
        fig, ax = plt.subplots(figsize=(12, 8))
        chamber.Draw(ax=ax, key="channel")  # key="channel" adds text labels per tube
        x_hits = df[event]["x"]
        y_hits = df[event]["y"]
        ax.scatter(x_hits, y_hits, s=200, facecolors='none', edgecolors='red', linewidths=2, label='Hits')
        ax.legend()

        linear_fit = linearFit(df, event)
        x_vals = np.linspace(0,1000,100)
        y_vals = linear_fit(x_vals)
        ax.plot(x_vals, y_vals)

        plt.savefig("figures/chamber_geometry_" + str(event) + ".jpg", format='jpg', dpi=300)
        plt.close(fig)

        # display perpendicular distances for each event
        fPD = findPerpDists(df, event)
        dists = fPD[0]
        hits_t = fPD[1]
        fig2, ax2 = plt.subplots()
        ax2.scatter(dists, hits_t)
        ax2.set_xlabel("Distance of closest approach")
        ax2.set_ylabel("tdc_time")
        plt.savefig("figures/rt_0_order_event_" + str(event) + ".jpg", format='jpg', dpi=300)
        plt.close(fig2)
        
        break

    # display aggregated perpendicular distances over all events
    aPD = aggregatePerpDists(df)
    aggd_dists = aPD[0]
    aggd_times = aPD[1]
    fig3, ax3 = plt.subplots()
    x_cutoff = 25 #cut out non-signal domain
    mask = aggd_dists <= x_cutoff
    filtered_dists = aggd_dists[mask]
    filtered_times = aggd_times[mask] - 70 #TDC->Drift
    
    # Create 2D histogram manually
    H, xedges, yedges = np.histogram2d(filtered_dists, filtered_times, bins=50)
    H_normalized = H / H.sum(axis=1, keepdims=True)

    # Midpoints of bins
    xcenters = 0.5 * (xedges[:-1] + xedges[1:])
    ycenters = 0.5 * (yedges[:-1] + yedges[1:])

    pcm = ax3.pcolormesh(xedges, yedges, H.T, cmap='plasma')
    fig3.colorbar(pcm, ax=ax3, label='Counts')

    # Find ridge (max y-bin index for each x column)
    ridge_y_indices = np.argmax(H, axis=1)
#    ridge_y_values = ycenters[ridge_y_indices]
    ridge_y_values = []
    
    filtered_x = []
    filtered_y = []

    for i in range(H.shape[0]):
        column = H_normalized[i, :]
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

#    ax3.scatter(filtered_x, filtered_y, s=8, color='cyan', alpha=0.6, label='Filtered ridge pts')

    # Fit Chebyshev polynomial of degree N
    degree = 4
    cheb_fit = Chebyshev.fit(filtered_x, filtered_y, degree)

    # Shift to satisfy y(0)=0
    def fit_with_constraint(x):
        return cheb_fit(x) - cheb_fit(0)

    x_fit = np.linspace(0, x_cutoff, 200)
    y_fit = fit_with_constraint(x_fit)

    ax3.plot(x_fit, y_fit, color='white', linewidth=2, label='Chebyshev fit')
    ax3.legend()

#    h = ax3.hist2d(aggd_dists, aggd_times, bins=50, cmap='plasma')  # Adjust bins and cmap as needed
#    fig3.colorbar(h[3], ax=ax3)

#    ax3.set_xlabel("Distance of closest approach")
#    ax3.set_ylabel("Time")
    ax3.set_xlim(0, x_cutoff)
    ax3.set_ylim(yedges[0], yedges[-1])
    plt.savefig("figures/rt_0_order_all_events.jpg", format='jpg', dpi=300)
    plt.close(fig3)


# prompt user for input
if __name__ == "__main__":
    print("\n\nHowdy!")
    events_list = input("Which event(s) would you like to image (separate by commas)?    ")
    events_list = [int(n) for n in events_list.split(',')]
    generatePlots(events_list)
    print("\nFinished.\nYour output files have been written to the ./figures/ directory.")
