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

#load configs to make geometry plot
with open("../../configs/ci_config.yaml") as f:
    config = yaml.safe_load(f)

#show chamber
chamber = Chamber(config)

def plotEvents(events_list): #takes list of events to generate plots for
    for event in events_list:
        fig, ax = plt.subplots(figsize=(12, 8))
        chamber.Draw(ax=ax, key="channel")  # key="channel" adds text labels per tube
        x_hits = df[event]["x"]
        y_hits = df[event]["y"]
        ax.scatter(x_hits, y_hits, s=200, facecolors='none', edgecolors='red', linewidths=2, label='Hits')
        ax.legend()
        plt.savefig("figures/chamber_geometry_" + str(event) + ".jpg", format='jpg', dpi=300)
        plt.close(fig)

# prompt user for input
if __name__ == "__main__":
    print("\n\nHowdy!")
    events_list = input("Which event(s) would you like to image (separate by commas)?    ")
    events_list = [int(n) for n in events_list.split(',')]
    plotEvents(events_list)
    print("\nFinished.\nYour output files have been written to the figures/ directory.")


