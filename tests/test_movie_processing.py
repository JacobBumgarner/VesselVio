import sys

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

import numpy as np
import pyvista as pv

from library import input_classes as IC, movie_processing as MovProc


def test_generate_flythrough_path():
    p = pv.Plotter()
    key_frames = []
    for i in range(5):
        pos = np.random.rand(3, 3)
        p.camera_position = pos
        key_frames.append(p.camera_position)

    path = MovProc.generate_flythrough_path(key_frames)
    assert path.shape == (300, 3, 3)
    path = MovProc.generate_flythrough_path(key_frames, path_type="smoothed")
    assert path.shape == (300, 3, 3)
    return


def test_import():
    save_path = "/Users/jacobbumgarner/Desktop/Movie Options.json"
    movie_options = MovProc.load_options(save_path)
    assert isinstance(movie_options.key_frames.list)


def test_export():
    p = pv.Plotter()
    key_frames = []
    for i in range(3):
        pos = np.random.rand(3)
        p.camera_position = pos
        key_frames.append(p.camera_position)
    options = IC.MovieOptions("Flythrough", key_frames)
    save_path = "/Users/jacobbumgarner/Desktop/Movie Options.json"
    MovProc.export_options(save_path, options)
    return
