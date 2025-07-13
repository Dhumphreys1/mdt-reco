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
for event in data:
    n_hits = len(event['x'])
    for i in range(n_hits):
        row = {key: event[key][i] for key in event}
        all_rows.append(row)

df = pd.DataFrame(all_rows)
for i in range(len(df['drift_time'])):
    if df['layer'][i] != 0:
        print("Got one!")

#load configs to make geometry plot
with open("../../configs/config.yaml") as f:
    config = yaml.safe_load(f)

#show chamber
chamber = Chamber(config)
fig, ax = plt.subplots(figsize=(12, 8))
chamber.Draw(ax=ax, key="channel")  # key="channel" adds text labels per tube

#show hits
x_hits = df['x']
y_hits = df['y']
ax.scatter(x_hits, y_hits, s=200, facecolors='none', edgecolors='red', linewidths=2, label='Hits')
ax.legend()

plt.savefig("figures/chamber_geometry.jpg", format='jpg', dpi=300)
plt.close(fig)
