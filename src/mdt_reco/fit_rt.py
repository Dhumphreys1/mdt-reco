import os
import numpy as np
import yaml
import matplotlib.pyplot as plt

from numpy.polynomial.chebyshev import Chebyshev
from scipy.ndimage import center_of_mass

from Geometry import Chamber
from TrackFitter import TrackFitter

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.normpath(os.path.join(script_dir, '../../data/e    vents_10k.npy'))
data = np.load(data_path, allow_pickle=True)

for event in data:
    TrackFitter = TrackFitter()
    m, b = TrackFitter.fitCosmic(event["x"], event["y"], event["drift_radius"], normal_form=False)
    print("m: " + str(m))
    print("b: " + str(b))
