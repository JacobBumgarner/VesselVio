"""VesselVio movie generation functions."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json

from math import ceil
from typing import Sequence, Tuple, Union

import numpy as np
import pyvista as pv

from library import helpers, input_classes as IC

from scipy import interpolate


################################
### Generate Path Processing ###
################################
def path_actor_scaling(seed_point: Union[pv.CameraPosition, np.ndarray, list]) -> float:
    """Generate a scaling factor for the plotter path actors.

    Subtracts the focal point from the camera position and then generates a scaling
    factor based on the emperically determined equation `max(1, distance/100)`.

    Parameters
    ----------
    seed_point : Union[pv.CameraPosition, np.ndarray, list]
        A (3,3) shaped iterable containing a PyVista camera position.

    Returns
    -------
    float
        The resizing factor.
    """
    radius = np.linalg.norm(seed_point[1] - seed_point[0])  # focal_pos - camera_pos
    resize_factor = max(1, radius / 100)  # emperically determined scaling
    return float(resize_factor)


def load_path_basis(
    seed_point: Union[np.ndarray, pv.CameraPosition, list, tuple]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a new basis vector based on an input camera position.

    Parameters
    ----------
    seed_point : Union[np.ndarray, pv.CameraPosition, list, tuple]
        A (3,3) shaped iterable containing the camera position, focal point, and viewup
        vectors.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        Three (3,) shaped arrays representing the new basis vectors of the camera.
    """
    if isinstance(seed_point, (pv.CameraPosition, tuple, list)):
        seed_point = np.array([pos for pos in seed_point])
    camera_pos = seed_point[0]
    focal_pos = seed_point[1]
    viewup = seed_point[2]
    v1 = focal_pos - camera_pos
    # v2 = B + C

    b1 = v1 / np.linalg.norm(v1)
    b2 = viewup
    v3 = np.cross(b1, b2)
    b3 = v3 / np.linalg.norm(v3)
    return b1, b2, b3


# Taken directly from https://docs.pyvista.org/examples/00-load/create-spline.html
def polyline_from_points(points: np.ndarray) -> pv.PolyData:
    """Generate a polyline from input points.

    Parameters
    ----------
    points : np.ndarray
        The point array to convert to a polyline.

    Returns
    -------
    pv.PolyData
    """
    poly = pv.PolyData()
    poly.points = points
    the_cell = np.arange(0, len(points), dtype=np.int_)
    the_cell = np.insert(the_cell, 0, len(points))
    poly.lines = the_cell
    return poly


def post_path_plotter_update(
    plotter: pv.Plotter, seed_position: pv.CameraPosition, orbit: bool = True
) -> None:
    """Move the plotter camera position slightly behind the seed position.

    This function is serves to prevent placing the plotter inside the path actors during
    movie path creation.

    Parameters
    ----------
    plotter : pv.Plotter
        _description_
    seed_position : pv.CameraPosition
        _description_
    orbit : bool, optional
        _description_, by default True
    """
    seed_position = np.array([pos for pos in seed_position])

    b1, b2, b3 = load_path_basis(seed_position)
    if orbit:
        resize_factor = path_actor_scaling(seed_position)
    else:
        resize_factor = 1

    plotter.camera_position = [
        seed_position[0] + b2 * resize_factor * 20 - b1 * resize_factor * 100,
        seed_position[1],
        seed_position[2],
    ]

    return


def load_movie_options(filepath: str) -> IC.MovieExportOptions:
    """Load a movie options file.

    Parameters
    ----------
    filepath : str


    Returns
    -------
    IC.MovieExportOptions
    """
    with open(filepath) as f:
        data = json.load(f)
        if len(data) != 1 or "VesselVio Movie Options" not in data.keys():
            return None
        data = data["VesselVio Movie Options"]

    movie_type = data["movie_type"]
    key_frames = data["key_frames"]
    movie_options = IC.MovieExportOptions(movie_type, key_frames)

    return movie_options


def export_options(filepath, movie_options: IC.MovieExportOptions):
    """Given a save path and a set of keyframes, save the movie options.

    Parameters
    ----------
    filepath : str

    movie_options : MovieOptions
        A MovieOptions object
    """
    # parse the options into a json format
    options = {}
    options["movie_type"] = movie_options.movie_type
    key_frames = prep_keyframes(movie_options.key_frames)
    options["key_frames"] = key_frames.tolist()

    if filepath:
        with open(filepath, "w") as f:
            annotation_data = {"VesselVio Movie Options": options}
            file_info = json.dumps(annotation_data)
            f.write(file_info)
            f.close()
    return


###############################
### Orbital Path Processing ###
###############################
def time_to_frames(framerate: float, movie_duration: float) -> int:
    """Convert a movie duration in time and a framerate to a frame count.

    Parameters
    ----------
    framerate : float

    movie_duration : float

    Returns
    -------
    int
        The number of frames in the movie.
    """
    frames = ceil(framerate * movie_duration)
    return int(frames)


def generate_orbital_path(
    camera_position: Union[pv.CameraPosition, np.ndarray, list],
    n_path_points: int = 100,
) -> np.ndarray:
    """Generate an orbital path from a seed camera position.

    Parameters
    ----------
    camera_position : Union[pv.CameraPosition, np.ndarray, list]

    n_path_points : int, optional
        The number of points in the resulting path, by default 100.

    Returns
    -------
    np.ndarray
        The (n,3,3) orbital path.

    Raises
    ------
    ValueError
        Raises an error if the input camera position isn't of (3,3) shape.
    """
    if not isinstance(camera_position, np.ndarray):
        camera_position = np.asarray([p for p in camera_position])

    if camera_position.shape != (3, 3):
        raise ValueError(
            "A (3,3) array containing the camera position, focal point, "
            "and viewup should be passed."
        )

    radius = np.linalg.norm(camera_position[0] - camera_position[1])
    path = pv.Polygon(
        center=camera_position[1],
        radius=radius,
        normal=camera_position[2],
        n_sides=n_path_points,
    )

    focal = np.repeat([camera_position[1]], n_path_points, axis=0)
    viewup = np.repeat([camera_position[2]], n_path_points, axis=0)
    return np.stack([path.points, focal, viewup], axis=1)


def generate_orbit_path_actors(
    plotter: pv.Plotter, path: Sequence[pv.CameraPosition]
) -> IC.OrbitActors:
    """Generate path actors to visualize the orbital camera path.

    Parameters
    ----------
    plotter : pv.Plotter

    path : Sequence[pv.CameraPosition]
        An iterable of pv.CameraPosition objects.

    Returns
    -------
    IC.OrbitActors
    """
    seed_point = path[0]
    camera_pos = seed_point[0]

    # Get local basis vectors from initial path position
    b1, b2, b3 = load_path_basis(seed_point)

    # Bounds resizing factor
    resize_factor = path_actor_scaling(seed_point)

    # Add the camera actors
    actors = IC.OrbitActors()

    # Create the camera
    camera = pv.Line(
        camera_pos - b1 * 2 * resize_factor, camera_pos + b1 * 2 * resize_factor
    )
    camera = camera.tube(radius=2 * resize_factor, n_sides=4)

    actors.camera = plotter.add_mesh(camera, color="f2f2f2", reset_camera=False)

    lens = pv.Line(camera_pos, camera_pos + b1 * 2 * resize_factor + b1 * resize_factor)
    lens["size"] = [0.2 * resize_factor, 1.3 * resize_factor]
    factor = max(lens["size"]) / min(lens["size"])
    lens = lens.tube(radius=min(lens["size"]), scalars="size", radius_factor=factor)
    actors.lens = plotter.add_mesh(
        lens, color="9fd6fc", smooth_shading=True, reset_camera=False
    )

    leg0 = pv.Line(
        camera_pos, camera_pos - b2 * 4 * resize_factor + b1 * 2 * resize_factor
    )
    leg0 = leg0.tube(radius=resize_factor / 2)
    leg1 = pv.Line(
        camera_pos,
        camera_pos
        - b2 * 4 * resize_factor
        - b1 * 2 * resize_factor
        + b3 * 2 * resize_factor,
    )
    leg1 = leg1.tube(radius=resize_factor / 2)
    leg2 = pv.Line(
        camera_pos,
        camera_pos
        - b2 * 4 * resize_factor
        - b1 * 2 * resize_factor
        - b3 * 2 * resize_factor,
    )
    leg2 = leg2.tube(radius=resize_factor / 2)
    legs = leg0 + leg1 + leg2

    actors.camera_legs = plotter.add_mesh(
        legs, color="383838", smooth_shading=True, reset_camera=False
    )

    # Create the orbit path
    line_path = polyline_from_points(path[1:-1, 0])
    line_path = line_path.tube(radius=0.5 * resize_factor, capping=True)
    actors.path = plotter.add_mesh(
        line_path, color="ff0000", smooth_shading=True, reset_camera=False
    )

    path_direction = pv.Line(path[-2, 0], path[-1, 0])
    path_direction["size"] = [resize_factor * 2, 0.1]
    path_direction = path_direction.tube(
        radius=0.1, scalars="size", radius_factor=resize_factor * 2 / 0.1
    )
    actors.path_direction = plotter.add_mesh(
        path_direction, color="ff0000", smooth_shading=True, reset_camera=False
    )

    # update the plotter position
    post_path_plotter_update(plotter, seed_point)

    return actors


##############################
### Fly Through Processing ###
##############################
def prep_keyframes(key_frames: Sequence[pv.CameraPosition]) -> np.ndarray:
    """Prepare a set of keyframes for a flythrough movie.

    Ensures that no two sequential camera positions are identical. Adds a minuscule
    value to the second camera position if the previous position is found to be
    identical.

    Parameters
    ----------
    key_frames : Sequence[pv.CameraPosition]
        An iterable of pv.CameraPosition objects.

    Returns
    -------
    np.ndarray
    """
    # The keyframes will come as a list of CameraPositions
    # Convert them to an array
    key_frames = [[list(pos) for pos in frame] for frame in key_frames]

    key_frames = np.asarray(key_frames)

    for i in range(1, len(key_frames)):  # dumb to iterate, i know
        for j in range(3):
            pos0 = key_frames[i - 1, j]
            pos1 = key_frames[i, j]
            if np.all(pos0 == pos1):
                key_frames[i, j] += 0.000001

    return key_frames


def generate_3D_spline_path(
    input_path: Union[np.ndarray, list, tuple], path_points: int = 40
) -> np.ndarray:
    """Generate an interpolate spline path a for an input iterable of keyframes.

    The path is a cubic b-spline that passes through all of the input keyframes.

    Parameters
    ----------
    input_path : Union[np.ndarray, list, tuple]

    path_points : int, optional
        The number of points to evaluate along the path, by default 40.

    Returns
    -------
    np.ndarray
        The interpolated path.

    Raises
    ------
    TypeError
        Raises an error if the input path isn't one of the correct types.
    """
    if not isinstance(input_path, [np.ndarray, list, tuple]):
        raise TypeError(
            "The input_path must be an iterable of keyframes.\n"
            "Pass the path as an np.ndarray, a list, or a tuple of shape (n,3,3)."
        )

    if not isinstance(input_path, np.ndarray):
        input_path = np.asarray(input_path)
    tck, u = interpolate.splprep(
        [input_path[:, 0], input_path[:, 1], input_path[:, 2]],
        k=int(min(2, input_path.shape[0] - 1)),
        s=0,
    )
    u = np.linspace(0, 1, num=path_points, endpoint=True)
    out = interpolate.splev(u, tck)
    path = np.asarray(out).T
    return path


def interpolate_linear_path(
    position_a: Union[pv.CameraPosition, np.ndarray, list],
    position_b: Union[pv.CameraPosition, np.ndarray, list],
    n_points: int,
    endpoint: bool = False,
):
    """Return linearly interpolated path between two input camera positions.

    Parameters
    ----------
    position_a : Union[pv.CameraPosition, np.ndarray, list]
        _description_
    position_b : Union[pv.CameraPosition, np.ndarray, list]
        (3,3) shaped iteratable containing the camera's position, focal point, and
        viewup.
    n_points : int
        The number of points to be interpolated between the two positions
    endpoint : bool, optional
        Add the position_b to the end of the interpolation, by default False

    Returns
    -------
    _type_
        (n,3,3) Shaped array of the interpolated path, where each `n` index
        stores a PyVista.CameraPosition array.

    Raises
    ------
    TypeError
        If `n_points` is not passed as an integer.
    """
    position_a = np.array([list(pos) for pos in position_a])
    position_b = np.array([list(pos) for pos in position_b])

    if not isinstance(n_points, int):
        raise TypeError(
            "n_points must be passed as an integer value for point interpolation"
        )

    # linearly interpolate the camera, focal, and viewup at once
    path = np.linspace(position_a, position_b, num=n_points, endpoint=endpoint)
    return path


def generate_flythrough_path(
    key_frames, movie_duration=10, framerate=30, path_type="linear"
):
    """Generates a linear flythrough path with specified frame durations

    Parameters
    ----------
    key_frames : list
        A list of PyVista.CameraPositions

    keyframe_durations : float, optional
        The duration of the movie in seconds

    framerate : int, optional
        The framerate used to convert the frame_durations into frames

    path_type : str
        Options: "linear", "smoothed"

    Returns
    -------
    path : np.array
        A (n,3,3) shaped array that represents a time-series of
        PyVista.CameraPositions. The amount of frames (n) will be determined
        by the input frame_durations and the input frame_rate
        path_points = [pos[0] for pos in key_frames]
    """
    # convert the key_frames into a numpy array
    key_frames = prep_keyframes(key_frames)

    # indicate how long each movie step should be
    approx_frames = time_to_frames(framerate, movie_duration)
    step_frames = int(approx_frames / (key_frames.shape[0] - 1))
    total_frames = step_frames * (key_frames.shape[0] - 1)

    if not isinstance(path_type, str):
        raise TypeError(
            "path_type must be a string and one of the two options",
            "'linear', 'smoothed'",
        )

    if path_type.lower() == "linear":
        # first path frame acts as seed for appends
        path = np.zeros((1, 3, 3), dtype=float)
        for i in range(len(key_frames) - 1):  # don't iterate the last frame
            pos_a = key_frames[i]
            pos_b = key_frames[i + 1]
            frame_path = interpolate_linear_path(
                pos_a, pos_b, step_frames, endpoint=i == len(key_frames) - 2
            )
            path = np.append(path, frame_path, axis=0)
        path = path[1:]  # strip the seeded zeros

    elif path_type.lower() == "smoothed":
        camera_path = generate_3D_spline_path(key_frames[:, 0], total_frames)
        focal_path = generate_3D_spline_path(key_frames[:, 1], total_frames)
        viewup_path = generate_3D_spline_path(key_frames[:, 2], total_frames)

        path = np.stack([camera_path, focal_path, viewup_path], axis=1)

    return path


def generate_flythrough_actors(plotter, key_frames, path_type):
    """Given a series of keyframes, creates a path actor tube that helps the
    user visualize the proposed path of the movie.

    Parameters
    ----------
    plotter : PyVista.Plotter

    key_frames : list
        A list of PyVista.CameraPositions, or a (n,3,3) shaped list where each
        n index contains a camera position, focal point, and viewup vector

    path_type : str
        Options: ['linear', 'spline']

    current_index : int, optional
        An optional argument that is used to update the plotter position to
        the specified index of the key_frames

    Returns
    -------
    FlyThroughActors

    """

    actors = IC.FlyThroughActors()

    path = generate_flythrough_path(key_frames, path_type=path_type)
    path_points = path[:, 0]  # only pull the camera position
    line = pv.Spline(path_points, n_points=path_points.shape[0])

    # Create the path actor
    line_path = line.tube(radius=2, capping=True)

    actors.path = plotter.add_mesh(
        line_path, color="ff0000", smooth_shading=True, reset_camera=False
    )

    # add start/end spheres
    start_sphere = pv.Sphere(radius=3, center=path_points[0])
    actors.start_sphere = plotter.add_mesh(
        start_sphere, color="green", smooth_shading=True, reset_camera=False
    )

    end_sphere = pv.Sphere(radius=3, center=path_points[-1])
    actors.end_sphere = plotter.add_mesh(
        end_sphere, color="orange", smooth_shading=True, reset_camera=False
    )

    return actors


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
    if resolution == "720p Square":
        X, Y = 720, 720
    elif resolution == "1080p Square":
        X, Y = 1080, 1080
    elif resolution == "1440p Square":
        X, Y = 1440, 1440
    elif resolution == "2160p Square":
        X, Y = 2160, 2160

    # TODO - low priority
    # Resizing of the PyVista plotter behaves different between normal and
    # high DPI screens. I haven't been able to figure out a good way to identify
    # high DPI screens yet. There is a potential solution by calling the widget,
    # getting the window.QScreen and getting the pixels per inch, but I'm not
    # sure if there is a universal 'high' vs. 'low' DPI.
    if helpers.unix_check():
        X /= 2
        Y /= 2
    return X, Y
