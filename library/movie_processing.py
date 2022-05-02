"""VesselVio movie generation functions."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"

import numpy as np
import pyvista as pv

from library import helpers, input_classes as IC


# Final path processing to update selected frames
def update_orbit_frames(path, frames):

    camera_path = path[:, 0]
    focal_path = path[:, 1]
    viewup = path[:, 2]
    camera = [camera_path[0], focal_path[0], viewup[0]]
    return construct_orbital_path(camera, frames, update=True)


def update_flythrough_frames(path, frames):
    c_path = path[:, 0]
    f_path = path[:, 1]
    viewup = path[:, 2]

    camera_path = np.linspace(c_path[0], c_path[-1], frames, endpoint=True)
    focal_path = np.linspace(f_path[0], f_path[-1], frames, endpoint=True)
    viewup = np.repeat([viewup[0]], frames, axis=0)

    return np.stack([camera_path, focal_path, viewup], axis=1)


# Path construction for visualiation
def construct_orbital_path(plotter, points, update=False):
    if not update:
        camera = np.array([position for position in plotter.camera_position])
    else:
        camera = [plotter[0], plotter[1], plotter[2]]

    radius = np.linalg.norm(camera[0] - camera[1])
    path = pv.Polygon(center=camera[1], radius=radius, normal=camera[2], n_sides=points)

    focal = np.repeat([camera[1]], points, axis=0)
    viewup = np.repeat([camera[2]], points, axis=0)
    return np.stack([path.points, focal, viewup], axis=1)


def construct_flythrough_path(plotter, points, update=False):
    if not update:
        camera = np.array([position for position in plotter.camera_position])
    else:
        camera = [plotter[0], plotter[1], plotter[2]]

    # starting with a -> b,  a + (a - b) will get us the path b -> a -> c
    A = camera[1]
    B = camera[0]
    v1 = A - B
    C = A + v1

    # focal path of a -> c -> d
    D = C + v1

    camera_path = np.linspace(B, C, points, endpoint=True)
    focal_path = np.linspace(A, D, points, endpoint=True)
    viewup = np.repeat([camera[2]], points, axis=0)
    return np.stack([camera_path, focal_path, viewup], axis=1)


def update_flythrough_orientation(plotter, path, points):
    # Get the orientation of the camera and build the updated basis
    camera = np.array([position for position in plotter.camera_position])
    camera_path = path[:, 0]
    path_length = np.linalg.norm(camera_path[-1] - camera_path[0])

    v1 = camera[1] - camera[0]
    focus_vector = v1 / np.linalg.norm(v1) * path_length / 2

    focus_start = camera_path[0] + focus_vector
    focus_end = camera_path[-1] + focus_vector

    viewup = np.repeat([camera[2]], points, axis=0)
    focus_path = np.linspace(focus_start, focus_end, points)
    return np.stack([camera_path, focus_path, viewup], axis=1)


# Taken directly from https://docs.pyvista.org/examples/00-load/create-spline.html
def polyline_from_points(points):
    poly = pv.PolyData()
    poly.points = points
    the_cell = np.arange(0, len(points), dtype=np.int_)
    the_cell = np.insert(the_cell, 0, len(points))
    poly.lines = the_cell
    return poly


def create_path_actors(p, path):
    camera_path = path[:, 0]
    focal_path = path[:, 1]
    viewup_path = path[:, 2]

    # Get local basis vectors from initial path position
    A = focal_path[0]
    B = camera_path[0]
    C = viewup_path[0]
    v1 = A - B
    # v2 = B + C

    b1 = v1 / np.linalg.norm(v1)
    b2 = C
    v3 = np.cross(b1, b2)
    b3 = v3 / np.linalg.norm(v3)

    # Bounds resizing factor
    radius = np.linalg.norm(B - A)
    bfactor = max(1, radius / 100)

    # Add the camera actors
    actors = IC.CameraActors()
    camera = pv.Line(B - b1 * 2 * bfactor, B + b1 * 2 * bfactor)
    camera = camera.tube(radius=2 * bfactor, n_sides=4)

    actors.camera = p.add_mesh(camera, color="f2f2f2", reset_camera=False)

    lens = pv.Line(B, B + b1 * 2 * bfactor + b1 * bfactor)
    lens["size"] = [0.2 * bfactor, 1.3 * bfactor]
    factor = max(lens["size"]) / min(lens["size"])
    lens = lens.tube(radius=min(lens["size"]), scalars="size", radius_factor=factor)
    actors.lens = p.add_mesh(
        lens, color="9fd6fc", smooth_shading=True, reset_camera=False
    )

    leg0 = pv.Line(B, B - b2 * 4 * bfactor + b1 * 2 * bfactor).tube(radius=bfactor / 2)
    leg1 = pv.Line(B, B - b2 * 4 * bfactor - b1 * 2 * bfactor + b3 * 2 * bfactor).tube(
        radius=bfactor / 2
    )
    leg2 = pv.Line(B, B - b2 * 4 * bfactor - b1 * 2 * bfactor - b3 * 2 * bfactor).tube(
        radius=bfactor / 2
    )
    legs = leg0 + leg1 + leg2

    actors.camera_legs = p.add_mesh(
        legs, color="383838", smooth_shading=True, reset_camera=False
    )

    # Create the line
    line_path = polyline_from_points(camera_path[1:-1]).tube(
        radius=0.5 * bfactor, capping=True
    )
    actors.path = p.add_mesh(
        line_path, color="ff0000", smooth_shading=True, reset_camera=False
    )

    path_direction = pv.Line(camera_path[-2], camera_path[-1])
    path_direction["size"] = [bfactor * 2, 0.1]
    path_direction = path_direction.tube(
        radius=0.1, scalars="size", radius_factor=bfactor * 2 / 0.1
    )
    actors.path_direction = p.add_mesh(
        path_direction, color="ff0000", smooth_shading=True, reset_camera=False
    )

    p.camera_position = [B + b2 * bfactor * 20 - b1 * bfactor * 100, A, C]

    return actors


# Gram-Schmidt basis processing
def gsBasis(A):
    B = np.array(
        A, dtype=np.float_
    )  # Make B a copy of A, since we're going to alter it's values.
    # Loop over all vectors, starting with zero, label them with i
    for i in range(B.shape[1]):
        # Loop over all previous vectors, j, to subtract.
        for j in range(i):
            B[:, i] = B[:, i] - B[:, i] @ B[:, j] * B[:, j]
        # Normalization test for B[:, i]
        if np.linalg.norm(B[:, i]) > 0.00000001:
            B[:, i] = B[:, i] / np.linalg.norm(B[:, i])
        else:
            B[:, i] = np.zeros_like(B[:, i])

    # Finally, return the result:
    return B


# Pyvista movie resolution processing
def get_resolution(resolution):
    if resolution == "720p":
        X, Y = 1280, 720
    elif resolution == "1080p":
        X, Y = 1920, 1080
    elif resolution == "1440p":
        X, Y = 2560, 1440
    elif resolution == "2160p":
        X, Y = 3840, 2160

    # Widget resizing behaves differently on windows than it does on MacOS for some reason.
    # Halve the frame size on MacOS, not windows.
    if helpers.unix_check():
        X /= 2
        Y /= 2
    return X, Y
