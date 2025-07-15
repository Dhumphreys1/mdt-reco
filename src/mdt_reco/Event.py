import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
from .Geometry import Chamber

class Event:
    def __init__(self):

        """
        The event container must store all detector information of the event.
        x, y, and drift radius can technically be computed at a later time. This
        would reduce the memory footprint, but should be evaluated at a later time.
        """

        self._data_types = {
            "csm_id": np.uint8,
            "tdc_id": np.uint8,
            "channel": np.uint8,
            "tdc_time": np.float32,
            "pulseWidth": np.float32,
            "x": np.float32,
            "y": np.float32,
            "drift_time": np.float32,
            "drift_radius": np.float32,
            }

        self.data = {
            key: np.array([], dtype = dtype)
            for key, dtype in self._data_types.items()
        }

        self._protected_keys = set(self.data.keys())

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if key in self._data_types:
            expected_dtype = np.dtype(self._data_types[key])
            actual_dtype = np.asarray(value).dtype
            if actual_dtype != expected_dtype:
                raise TypeError(
                    f"Invalid dtype for key '{key}': expected {expected_dtype}, got {actual_dtype}"
                )
        self.data[key] = value  # Allow setting both protected and new keys

    def __delitem__(self, key):
        if key in self._protected_keys:
            raise KeyError(f"Cannot delete protected key: '{key}'")
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __contains__(self, key):
        return key in self.data

    def __repr__(self):
        return repr(self.data)

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def draw(self, chamber: Chamber, title = None, save = False, file_dir=None, file_name=None, file_ext=".pdf"):
        fig, ax = plt.subplots(figsize=(10, 10))
        chamber.Draw(ax=ax)
        patches = []
        for hit_id, _ in enumerate(self['x']):
            center = (self['x'][hit_id], self['y'][hit_id])
            radius = chamber.GetRadius(self["tdc_id"][hit_id])
            circle = Circle(center, radius, fill=True, facecolor='lime', ec='black', lw=1)
            patches.append(circle)
        collection = PatchCollection(patches, match_original=True)
        ax.add_collection(collection)

        legend_circle = Line2D([0], [0],
                           marker='o',
                           color='w',
                           markerfacecolor='lime',
                           markeredgecolor='black',
                           markersize=10,
                           label='Hit')
        ax.legend(handles=[legend_circle], loc='upper right')

        ax.set_xlabel('x[mm]')
        ax.set_ylabel('y[mm]')
        ylims = ax.get_ylim()
        ax.set_ylim(ylims[0], ylims[1] + 40)
        if title is not None:
            ax.set_title(title)
        if save:
            if file_dir is None or file_name is None:
                raise ValueError("file_dir and file_name must be provided when save=True")
            if not file_ext.startswith('.'):
                file_ext = '.' + file_ext
            _, ext = os.path.splitext(file_name)
            if not ext:
                file_name = file_name + file_ext
            file_path = os.path.join(file_dir, file_name)
            plt.savefig(file_path)
        else:
            plt.show()
