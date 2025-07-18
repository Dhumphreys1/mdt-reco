import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

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
            "theta": np.float32,
            "d": np.float32,
        }

        self.data = {
            key: np.array([], dtype=dtype) for key, dtype in self._data_types.items()
        }

        self._protected_keys = set(self.data.keys())

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if key in self._data_types:
            expected_dtype = np.dtype(self._data_types[key])
            actual_dtype = np.asarray(value).dtype
            if actual_dtype != expected_dtype:
                msg = f"Invalid dtype for key '{key}': \
                      expected {expected_dtype}, got {actual_dtype}"
                raise TypeError(msg)
        self.data[key] = value  # Allow setting both protected and new keys

    def __delitem__(self, key):
        if key in self._protected_keys:
            msg = f"Cannot delete protected key: '{key}'"
            raise KeyError(msg)
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

    def getTrackDist(self, theta=None, d=None):
        if theta is None:
            theta = self["theta"]
        if d is None:
            d = self["d"]
        if theta is None:
            msg = "Missing or empty parameter(s): theta"
            raise ValueError(msg)
        if d is None:
            msg = "Missing or empty parameter(s): d"
            raise ValueError(msg)

        return abs(self["x"] * np.cos(theta) + self["y"] * np.sin(theta) - d)

    def getTrackResid(self, theta=None, d=None):
        return self["drift_radius"] - self.getTrackDist(theta=theta, d=d)

    def draw(
        self,
        chamber: Chamber,
        ax=None,
        title=None,
        save=False,
        file_dir=None,
        file_name=None,
        file_ext=".pdf",
    ):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))
        chamber.draw(ax=ax)
        patches = []
        for hit_id, _ in enumerate(self["x"]):
            center = (self["x"][hit_id], self["y"][hit_id])
            radius = chamber.getRadius(self["tdc_id"][hit_id])
            circle = Circle(
                center, radius, fill=True, facecolor="lime", ec="black", lw=1
            )
            patches.append(circle)
        collection = PatchCollection(patches, match_original=True)
        ax.add_collection(collection)

        legend_circle = Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="lime",
            markeredgecolor="black",
            markersize=10,
            label="Hit",
        )
        ax.legend(handles=[legend_circle], loc="upper right")

        ax.set_xlabel("x[mm]")
        ax.set_ylabel("y[mm]")
        ylims = ax.get_ylim()
        ax.set_ylim(ylims[0], ylims[1] + 40)
        if title is not None:
            ax.set_title(title)
        if save:
            if file_dir is None or file_name is None:
                msg = "file_dir and file_name must be provided when save=True"
                raise ValueError(msg)
            if not file_ext.startswith("."):
                file_ext = "." + file_ext
            _, ext = os.path.splitext(file_name)
            if not ext:
                file_name = file_name + file_ext
            file_path = os.path.join(file_dir, file_name)
            plt.savefig(file_path)
        else:
            plt.show()

    def drawTrack(
        self,
        chamber: Chamber,
        ax=None,
        title=None,
        save=False,
        file_dir=None,
        file_name=None,
        file_ext=".pdf",
        **kwargs,
    ):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))
        cos_t = np.cos(self["theta"])
        sin_t = np.sin(self["theta"])
        tolerance = 1e-5
        if np.abs(sin_t) > tolerance:
            # Not vertical
            x_vals = np.linspace(self["x"].min() - 20, self["x"].max() + 20, 10)
            y_vals = (self["d"] - x_vals * cos_t) / sin_t
            ax.plot(x_vals, y_vals, label="Track", **kwargs)
        else:
            # Vertical line: x = d / cos(θ)
            x_line = self["d"] / cos_t
            y_vals = np.linspace(self["y"].min() - 50, self["y"].max() + 50, 10)
            ax.plot(np.full_like(y_vals, x_line), y_vals, label="Track", **kwargs)
        self.draw(
            chamber=chamber,
            ax=ax,
            title=title,
            save=save,
            file_dir=file_dir,
            file_name=file_name,
            file_ext=file_ext,
        )
