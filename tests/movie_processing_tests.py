import sys

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

import numpy as np
import pyvista as pv

from library import movie_processing as MovProc


def test_generate_flythrough_path():
    p = pv.Plotter()
    key_frames = []
    for i in range(3):
        pos = np.random.rand(3, 3)
        p.camera_position = pos
        key_frames.append(p.camera_position)

    path = MovProc.generate_flythrough_path(key_frames)
    assert path.shape == (300, 3, 3)
    path = MovProc.generate_flythrough_path(key_frames, path_type="smoothed")
    return


test_generate_flythrough_path()
