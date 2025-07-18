#python frontmatter
import os
import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
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

#by residual, I mean perpendicular distance
def findResiduals(data, event):
    linear = linearFit(data, event)
    b, m = linear.convert().coef

    hits_x = data[event]["x"]
    hits_y = data[event]["y"]
    hits_t = data[event]["tdc_time"]  #is this right?
    residuals = []
    for i in range(len(hits_x)):
        x_0 = hits_x[i]
        y_0 = hits_y[i]
        dist = np.abs(m * x_0 - y_0 + b) / np.sqrt(m**2 + 1)
        residuals.append(dist)

    return residuals

#load configs to make geometry plot
with open("../../configs/ci_config.yaml") as f:
    config = yaml.safe_load(f)

#show chamber
chamber = Chamber(config)

def generatePlots(events_list): #takes list of events to generate plots for
    for event in events_list:
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

        hits_t = df[event]["tdc_time"] 
        residuals = findResiduals(df, event)
        #print("Residuals:")
        #for residual in residuals:
        #    print(residual)
        fig2, ax2 = plt.subplots()
        ax2.scatter(residuals, hits_t)
        ax2.set_xlabel("Distance of closest approach")
        ax2.set_ylabel("tdc_time")
        plt.savefig("figures/rt_0_order_event_" + str(event) + ".jpg", format='jpg', dpi=300)
        plt.close(fig2)

# prompt user for input
if __name__ == "__main__":
    print("\n\nHowdy!")
    events_list = input("Which event(s) would you like to image (separate by commas)?    ")
    events_list = [int(n) for n in events_list.split(',')]
    generatePlots(events_list)
    print("\nFinished.\nYour output files have been written to the ./figures/ directory.")
