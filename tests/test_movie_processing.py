import json
import os

import numpy as np
import pyvista as pv

from library import input_classes as IC, movie_processing as MovProc
from pytest import raises


def test_path_actor_scaling():
    position = np.ones((3, 3, 3))
    resize_factor = MovProc.path_actor_scaling(position)
    assert resize_factor == 1
    return


def test_load_path_basis():
    seed_position = ((1, 5, 1), (2, 2, 2), (0, 1, 0))
    b1, b2, b3 = MovProc.load_path_basis(seed_position)
    assert np.all(np.isclose(b1, [0.30151134, -0.90453403, 0.30151134]))
    assert np.all(np.isclose(b2, [0, 1, 0]))
    assert np.all(np.isclose(b3, [-0.70710678, 0.0, 0.70710678]))
    return


def test_generate_orbital_path():
    # test without position
    with raises(TypeError, match="Please pass a PyVista.Plotter.camera_position"):
        path = MovProc.generate_orbital_path([[1, 1, 1], [1, 1, 1], [1, 1, 1]])

    p = pv.Plotter()
    path = MovProc.generate_orbital_path(p.camera_position)
    assert path.shape == (100, 3, 3)
    return


def test_generate_orbital_path_actors():
    # Just make sure that we get the appropriate class of actors back
    p = pv.Plotter()
    path = np.random.randint(-10, 10, (10, 3, 3))

    actors = MovProc.generate_orbit_path_actors(p, path)
    assert isinstance(actors, IC.OrbitActors)
    assert actors.path.GetProperty().GetColor() == (1, 0, 0)
    return


def test_generate_flythrough_actors():
    p = pv.Plotter()
    key_frames = [p.camera_position for _ in range(3)]

    actors = MovProc.generate_flythrough_actors(p, key_frames, path_type="Linear")
    assert isinstance(actors, IC.FlyThroughActors)
    return


def test_generate_3D_spline_path():
    path = np.random.randint(0, 10, (10, 3))
    path = MovProc.generate_3D_spline_path(path)
    assert path.shape == (40, 3)
    path = MovProc.generate_3D_spline_path(path.tolist(), 50)
    assert path.shape == (50, 3)
    return


def test_interpolate_linear_path():
    pos_a = np.random.randint(0, 10, (3, 3, 3))
    pos_b = np.random.randint(0, 10, (3, 3, 3))
    with raises(TypeError, match="n_points must be"):
        MovProc.interpolate_linear_path(pos_a, pos_b, 4.5)

    path = MovProc.interpolate_linear_path(pos_a, pos_b, 10)
    assert path.shape == (10, 3, 3, 3)
    return


def test_post_path_plotter_update():
    p = pv.Plotter()
    seed_position = np.array(((200, 200, 200), (0, 0, 0), (0, 1, 0)))

    MovProc.post_path_plotter_update(p, seed_position, orbit=True)
    pos1_test = [(400.0, 469.28203230275506, 400.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    assert p.camera_position == pos1_test

    MovProc.post_path_plotter_update(p, seed_position, orbit=False)
    pos2_test = [
        (257.7350269189626, 277.7350269189626, 257.7350269189626),
        (0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    ]

    assert p.camera_position == pos2_test
    return


def test_generate_flythrough_path():
    p = pv.Plotter()
    key_frames = []
    for i in range(5):
        pos = np.random.rand(3, 3)
        p.camera_position = pos
        key_frames.append(p.camera_position)

    with raises(TypeError, match="path_type"):
        MovProc.generate_flythrough_path(key_frames, path_type=1)
    path = MovProc.generate_flythrough_path(key_frames)
    assert path.shape == (300, 3, 3)
    path = MovProc.generate_flythrough_path(key_frames, path_type="smoothed")
    assert path.shape == (300, 3, 3)
    return


def test_export():
    p = pv.Plotter()
    key_frames = []
    for i in range(3):
        pos = np.random.rand(3)
        p.camera_position = pos
        key_frames.append(p.camera_position)
    options = IC.MovieExportOptions("Flythrough", key_frames)
    save_path = "Movie Options.json"
    MovProc.export_options(save_path, options)
    return


def test_import():
    file_path = "Movie Options.json"
    movie_options = MovProc.load_options(file_path)
    assert isinstance(movie_options.key_frames, list)

    fake_file = "Incompatible File.json"
    with open(fake_file, "w") as f:
        fake_data = {"test": "no_movie_info_here"}
        file_info = json.dumps(fake_data)
        f.write(file_info)
        f.close()

    movie_options = MovProc.load_options(fake_file)
    assert movie_options is None

    os.remove(file_path)
    os.remove(fake_file)


def test_get_resolution():
    resolution_keys = [
        "720p",
        "1080p",
        "1440p",
        "2160p",
        "720p Square",
        "1080p Square",
        "1440p Square",
        "2160p Square",
    ]

    values = [
        [1280, 720],
        [1920, 1080],
        [2560, 1440],
        [3840, 2160],
        [720, 720],
        [1080, 1080],
        [1440, 1440],
        [2160, 2160],
    ]

    for i, resolution in enumerate(resolution_keys):
        X, Y = MovProc.get_resolution(resolution, test_DPI=False)
        assert [X, Y] == values[i]
        X, Y = MovProc.get_resolution(resolution, test_DPI=False)
        assert [X, Y] == values[i]

    return


test_get_resolution()
