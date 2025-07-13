#python frontmatter
import os
import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
#NOTE TO SELF: these need to be reflected in ../../setup_env.sh so that we have access to 'em

#functions from elsewhere
from Geometry import Chamber

#diagnostic
#print(np.__version__)
#print(pd.__version__)

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.normpath(os.path.join(script_dir, '../../data/events_10k.npy'))

data = np.load(data_path, allow_pickle=True)

all_rows = []
for event_id, event in enumerate(data):
    n_hits = len(event['x'])
    for i in range(n_hits):
        row = {key: event[key][i] for key in event}
        row["event_id"] = event_id
        all_rows.append(row)

df = pd.DataFrame(all_rows)
print(df.head(30))

for i in range(len(df['drift_time'])):
    if df['drift_time'][i] != 0:
        print("Got one!")

#load configs to make geometry plot
with open("../../configs/config.yaml") as f:
    config = yaml.safe_load(f)

#show chamber
chamber = Chamber(config)
#fig, ax = plt.subplots(figsize=(12, 8))
#chamber.Draw(ax=ax, key="channel")  # key="channel" adds text labels per tube

#show hits
x_hits_by_event = {}

for event_id, group in df.groupby("event_id"):
    x_hits_by_event[event_id] = group["x"].tolist()

y_hits_by_event = {}

for event_id, group in df.groupby("event_id"):
    y_hits_by_event[event_id] = group["y"].tolist()

for i in range(10):
    fig, ax = plt.subplots(figsize=(12, 8))
    chamber.Draw(ax=ax, key="channel")  # key="channel" adds text labels per tube
    x_hits = x_hits_by_event[i]
    y_hits = y_hits_by_event[i]
    ax.scatter(x_hits, y_hits, s=200, facecolors='none', edgecolors='red', linewidths=2, label='Hits')
    ax.legend()
    plt.savefig("figures/chamber_geometry_" + str(i) + ".jpg", format='jpg', dpi=300)
    plt.close(fig)
