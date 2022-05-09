"""VesselVio movie generation functions."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json

from math import ceil

import numpy as np
import pyvista as pv

from library import helpers, input_classes as IC

from scipy import interpolate


################################
### Generate Path Processing ###
################################
def path_actor_scaling(seed_point):
    """Given a camera position seed point and the current position of the
    plotter relative to the focal point, generate a scaling factor for the
    path actors.

    Parameters
    ----------
    seed_point: PyVista.CameraPosition, list, tuple, np.array
        An (n,3,3) shaped iterable containing:
            - The plotter camera position
            - The plotter focal poin
            - The plotter view 'up' vector

    Returns
    -------
    resize_factor : float
    """
    # focal_pos - camera_pos
    radius = np.linalg.norm(seed_point[1] - seed_point[0])
    resize_factor = max(1, radius / 100)  # emperically determined scaling
    return float(resize_factor)


def load_path_basis(seed_point):
    """Returns new basis vectors based on an input
    PyVista.Plotter.camera_position

    Parameters
    ----------
    seed_point: PyVista.CameraPosition, list, tuple, np.array
        An (n,3,3) shaped iterable containing:
            - The plotter camera position
            - The plotter focal poin
            - The plotter view 'up' vector

    Returns
    -------
    b1 : list

    b2 : list

    b3 : list

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
def polyline_from_points(points):
    poly = pv.PolyData()
    poly.points = points
    the_cell = np.arange(0, len(points), dtype=np.int_)
    the_cell = np.insert(the_cell, 0, len(points))
    poly.lines = the_cell
    return poly


def post_path_plotter_update(plotter, seed_position, orbit=True):
    """Given the plotter and a seed point, update the plotter's view to be
    shifted slightly up and back from that view. This function is useful to
    avoid placing the plotter at the exact seed_position, which might place
    it inside of path camera actors during movie creation.

    Parameters
    ----------
    plotter : PyVista.Plotter

    seed_position : PyVista.Plotter.camera_position

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


def load_options(filepath):
    """Given a save path, load a movie options file.

    Parameters
    ----------
    filepath : str


    Returns
    -------
    movie_options : MovieOptions
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
def time_to_frames(framerate, movie_time):
    """Given a framerate and a frame count, return the number
    of frames for the orbit

    Parameters
    ----------
    framerate: int

    movie_time: float

    Returns
    -------
    frames : int

    """
    frames = ceil(framerate * movie_time)
    return int(frames)


def generate_orbital_path(camera_position, n_points=100):
    """Given a seed PyVista plotter camera position, creates an orbital path

    Parameters
    ----------
    camera_position: PyVista.CameraPosition or tuple
        (3,3) tuple containing the plotter camera: position, focal point, and
        viewup. Should be passed directly from PyVista.camera_position

    n_points: int
        The number of points that the orbit will contain

    Returns
    -------
    orbital_path : np.array
        An (n,3,3) array containing a time-series of camera_positions
    """

    if not isinstance(camera_position, (pv.CameraPosition)):
        raise TypeError("A PyVista.Plotter.camera_position should be passed into the ")
    camera_position = np.asarray([p for p in camera_position])
    if camera_position.shape != (3, 3):
        raise ValueError(
            "A (3,3) array containing the camera position, focal point, and viewup should be passed."
        )

    radius = np.linalg.norm(camera_position[0] - camera_position[1])
    path = pv.Polygon(
        center=camera_position[1],
        radius=radius,
        normal=camera_position[2],
        n_sides=n_points,
    )

    focal = np.repeat([camera_position[1]], n_points, axis=0)
    viewup = np.repeat([camera_position[2]], n_points, axis=0)
    return np.stack([path.points, focal, viewup], axis=1)


def generate_orbit_path_actors(plotter, path):
    """Generate actors that help the user visualize the orbital movie path

    Parameters
    ----------
    plotter : PyVista.Plotter

    path : list
        An (n,3,3) list where each n index represents a
        pyvista.plotter.camera_position

    Returns
    -------
    OrbitPathActors

    """
    seed_point = path[0]
    camera_pos = seed_point[0]

    # Get local basis vectors from initial path position
    b1, b2, b3 = load_path_basis(seed_point)

    # Bounds resizing factor
    resize_factor = path_actor_scaling(seed_point)

    # Add the camera actors
    actors = IC.OrbitActors()
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

    # Create the line
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
def prep_keyframes(key_frames):
    """Given a list of keyframes for a flythrough movie, this function iterates
    through and makes sure that no pair of keyframes share the same plotter
    position. If two adjacent frames share identical positions, the position
    is altered by a minute amount.

    Parameters
    ----------
    key_frames : list
        (n,3,3) list where each n index contains a
        PyVista.Plotter.camera_position

    Returns
    -------
    key_frames : np.array
        An (n,3,3) shaped array with updated keyframes without any sequentially
        duplicated frames
    """
    # The keyframes will come as a list of CameraPositions
    # Convert them to an array
    key_frames = [[list(pos) for pos in frame] for frame in key_frames]

    key_frames = np.asarray(key_frames)

    for i in range(1, len(key_frames)):  # dumb to iterate, i know
        pos0 = key_frames[i - 1, 0]
        pos1 = key_frames[i, 0]
        if np.all(pos0 == pos1):
            key_frames[i, 0] += 0.000001

    return key_frames


def generate_3D_spline_path(input_path, path_points=40):
    """Given a series of keyframes, generate a quadratic b-spline curve that
    passes through all of the original input points.

    Parameters
    ----------
    input_path : list, tuple, np.array
        (n,3) Shaped array

    Returns
    -------
    path : np.array
        (n,3) shaped array containing the
    """
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


def interpolate_linear_path(position_a, position_b, n_points, endpoint=False):
    """Given two points, create a linearly interpolated path between them.

    Parameters
    ----------
    position_a : PyVista.CameraPosition, np.array, list
        (n,3,3) shape

    position_b : PyVista.CameraPosition, np.array, list
        (n,3,3) shape

    n_points : int
        The number of points to be interpolated between the two positions

    endpoint : bool
        Add the position_b to the end of the interpolation

    Returns
    -------
    path : np.array
        (n_points,3,3) Shaped array of the interpolated path, where each
        n_point index represents a PyVista.CameraPosition

    """
    position_a = np.array([list(pos) for pos in position_a])
    position_b = np.array([list(pos) for pos in position_b])

    if not isinstance(n_points, int):
        raise TypeError(
            "n_points must be passed as an integer value for point interpolation"
        )

    # god numpy is amazing
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

    # first path frame acts as seed for appends
    path = np.zeros((1, 3, 3), dtype=float)

    # indicate how long each movie step should be
    approx_frames = time_to_frames(framerate, movie_duration)
    step_frames = int(approx_frames / (key_frames.shape[0] - 1))
    total_frames = step_frames * (key_frames.shape[0] - 1)

    for i in range(len(key_frames) - 1):  # don't iterate the last frame
        pos_a = key_frames[i]
        pos_b = key_frames[i + 1]
        frame_path = interpolate_linear_path(
            pos_a, pos_b, step_frames, endpoint=i == len(key_frames) - 2
        )
        path = np.append(path, frame_path, axis=0)

    path = path[1:]  # strip the seeded zeros

    if not isinstance(path_type, str):
        raise TypeError(
            "path_type must be a string and one of the two options",
            "'linear', 'smoothed'",
        )

    if path_type.lower() == "smoothed":
        camera_path = generate_3D_spline_path(key_frames[:, 0], total_frames)
        path[:, 0] = camera_path
    return path


def generate_flythrough_actors(plotter, key_frames, path_type, current_index=0):
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
    line = pv.Spline(path_points)

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
