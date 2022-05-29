"""
A catchall helpers page with small functions that are used throughout the program.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import concurrent.futures as cf
import json
import os
import platform
import sys
import typing
from itertools import chain
from math import floor
from multiprocessing import cpu_count, get_context
from time import perf_counter as pf

import numpy as np
import pyvista as pv

from matplotlib.cm import get_cmap
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QFileDialog


##########################
### File Path Handling ###
##########################
# Standardize the path for the OS
def std_path(path):
    path = os.path.normpath(path)
    return path


# Find out whether the program is running from the app or terminal
def get_cwd():
    try:
        wd = sys._MEIPASS
    except AttributeError:
        wd = os.getcwd()
    return wd


def get_dir(location):
    sys_os = get_OS()
    if sys_os == "Darwin":
        load_dir = os.path.join(os.path.expanduser("~"), location)
    elif sys_os == "Windows":
        load_dir = os.path.join(os.path.join(os.environ["USERPROFILE"]), location)
    load_dir = std_path(load_dir)
    return load_dir


def get_OS():
    sys_os = platform.system()
    return sys_os


def unix_check():
    sys_os = get_OS()
    return sys_os != "Windows"


def get_ext(file):
    ext = os.path.splitext(file)[-1]
    return ext


def load_screenshot_dir():
    results_dir = load_results_dir()
    screenshot_dir = os.path.join(results_dir, "Screenshots")
    screenshot_dir = std_path(screenshot_dir)
    return screenshot_dir


def load_movie_dir():
    results_dir = load_results_dir()
    if os.path.exists(results_dir):
        movie_dir = os.path.join(results_dir, "Movies")
        movie_dir = std_path(movie_dir)
        if not os.path.exists(movie_dir):
            os.mkdir(movie_dir)
        return movie_dir
    else:
        return get_dir("Desktop")


def prep_media_path(directory, name):
    raw_name = os.path.join(directory, name)
    filename = std_path(raw_name)
    return filename


def prep_media_dir(filename):
    media_dir = os.path.dirname(filename)
    if not os.path.exists(media_dir):
        parent_dir = os.path.dirname(media_dir)
        if not os.path.exists(parent_dir):
            os.mkdir(parent_dir)  # Make sure the parent folder exists
        os.mkdir(media_dir)  # Make sure the screenshots folder exists
    return


def load_results_dir():
    results_dir = get_results_cache()

    # Checks to see if our results pathway is present or if our results cache is empty.
    if not os.path.exists(results_dir):
        # If its empty, create a default folder.
        # It will be created later on during results export if it doesn't exist.
        desktop = get_dir("Desktop")
        results_dir = os.path.join(desktop, "VesselVio")
        results_dir = std_path(results_dir)
        update_results_cache(results_dir)

    return results_dir


def set_results_dir():
    # Get selected results directory
    results_dir = QFileDialog.getExistingDirectory(
        QFileDialog(), "Select Results Folder", get_dir("Desktop")
    )
    results_dir = std_path(results_dir)
    # Update our stored results folder location.
    if results_dir:
        update_results_cache(results_dir)
    return results_dir


def load_volumes():
    message = "Load volume files"
    file_filter = "Images (*.nii *.png *.bmp *.tif *.tiff *.jpg *.jpeg)"
    files = QFileDialog.getOpenFileNames(
        QFileDialog(), message, get_dir("Desktop"), file_filter
    )[0]
    if files:
        files = [std_path(file) for file in files]
    return files


def load_graphs(graph_format):
    message = f"Load {graph_format} files"
    file_filter = f"{graph_format} (*.{graph_format})"
    files = QFileDialog.getOpenFileNames(
        QFileDialog(), message, get_dir("Desktop"), file_filter
    )[0]
    if files:
        files = [std_path(file) for file in files]
    return files


def load_volume():
    message = "Load volume file"
    file_filter = "Images (*.nii *.png *.bmp *.tif *.tiff *.jpg *.jpeg)"
    file = QFileDialog.getOpenFileName(
        QFileDialog(), message, get_dir("Desktop"), file_filter
    )[0]
    if file:
        file = std_path(file)
    return file


def load_graph(graph_format):
    message = f"Load {graph_format} file"
    file_filter = f"{graph_format} (*.{graph_format})"
    files = QFileDialog.getOpenFileName(
        QFileDialog(), message, get_dir("Desktop"), file_filter
    )
    return files[0]


def load_nii_annotation():
    message = "Load '.nii' file"
    file_filter = "nii (*.nii)"
    file = QFileDialog.getOpenFileName(
        QFileDialog(), message, get_dir("Desktop"), file_filter
    )[0]
    if file:
        file = std_path(file)
    return file


def load_RGB_folder():
    message = "Select RGB annotation folder"
    folder = QFileDialog.getExistingDirectory(
        QFileDialog(), message, get_dir("Desktop")
    )
    if folder:
        folder = std_path(folder)
    return folder


def get_save_file(message, directory, format):
    file_filter = f"{format} (*.{format})"
    file_name = QFileDialog.getSaveFileName(
        QFileDialog(), message, directory, file_filter
    )[0]
    if file_name:
        file_name = std_path(file_name)
    return file_name


def load_JSON(directory):
    message = "Select JSON Tree File"
    file_filter = "json (*.json)"
    loaded_file = QFileDialog.getOpenFileName(
        QFileDialog(), message, directory, file_filter
    )[0]
    if loaded_file:
        loaded_file = std_path(loaded_file)
    return loaded_file


## cache path loading
def load_prefs():
    wd = get_cwd()
    pref_cache = os.path.join(wd, "library", "cache", "preferences.json")
    with open(pref_cache) as p:
        prefs = json.load(p)
    return prefs


def save_prefs(prefs):
    wd = get_cwd()
    pref_cache = os.path.join(wd, "library", "cache", "preferences.json")
    with open(pref_cache, "w") as p:
        json.dump(prefs, p)
    return


def update_results_cache(results_dir):
    prefs = load_prefs()
    prefs["results_dir"] = results_dir
    save_prefs(prefs)
    return


def get_results_cache():
    prefs = load_prefs()
    results_cache = prefs["results_dir"]
    return results_cache


def get_graph_cache():
    wd = get_cwd()
    graph_cache = os.path.join(wd, "library", "cache", "cached_graph.graphml")
    graph_cache = std_path(graph_cache)
    return graph_cache


def get_volume_cache_path(directory: str = None) -> str:
    """Return the filepath where the labeled_volume is/will be cached.

    Parameters:
    directory : str, optional
        The cache directory. Default ``None``, which leads to a save in the
        ``"library/cache/"`` folder.

    Returns:
    str : cache_directory
    """
    if not directory:
        directory = os.path.join(get_cwd(), "library", "cache")

    cache_directory = os.path.join(directory, "labeled_volume.npy")

    cache_directory = std_path(cache_directory)

    return cache_directory


def silence_update_alerts():
    prefs = load_prefs()
    prefs["update_check"] = False
    save_prefs(prefs)
    return


#####################
### Icon Handling ###
#####################
def load_icon():
    """Locates the path to the application icon based on the current OS

    returns icon_path"""
    wd = get_cwd()

    # Load the correct icon file, dependent on OS.
    # Assumes we're only running this on Windows or Mac...
    if get_OS() == "Windows":
        icon_path = std_path(os.path.join(wd, "library", "icons", "icon.ico"))
    else:
        icon_path = std_path(os.path.join(wd, "library", "icons", "icon.icns"))

    return icon_path


########################
### Disk Space Check ###
#########################
def check_storage(volume_file):
    """Given a volume, compares the volume size to the default disk size.
    volume_file: file path to the loaded volume
    returns False if the volume is larger than the available disk space.
    """
    desktop = get_dir("desktop")
    disk_info = os.statvfs(desktop)
    free_space = disk_info.f_frsize * disk_info.f_bavail
    volume_size = get_file_size(volume_file)
    return volume_size < free_space


def get_file_size(volume_file, GB=False):
    """Returns the filesize of a file either in bytes or GB
    volume_file: file path to the loaded volume
    """
    file_size = os.path.getsize(volume_file)
    if GB:
        file_size *= 10**-9
    return file_size


#######################
### Multiprocessing ###
#######################
# The variables used in the called function need to be global
def multiprocessing_input(function, list_size, workers: int = None, sublist=False):
    """
    The variables used in the called function need to be global.

    function: The function to be used for multiprocessing

    list_size: The size of the list that is to be processed.
        This list will be processed in steps based on worker count.

    workers: The amount of CPUs to be called on. Defaults to maximum available based on mp.cpu_count()
    """
    if not workers:
        workers = cpu_count()

    futures = []
    steps = floor(list_size / workers)

    with cf.ProcessPoolExecutor(
        max_workers=workers, mp_context=get_context("fork")
    ) as executor:
        for i in range(workers):
            bottom = i * steps
            top = bottom + steps if i != workers - 1 else list_size
            futures.append(executor.submit(function, bottom, top))

    if sublist:
        results = chain.from_iterable([f.result()] for f in cf.as_completed(futures))
    else:
        results = chain.from_iterable(f.result() for f in cf.as_completed(futures))

    return list(results)


########################
### Color Processing ###
########################
def get_widget_rgb(widget):
    color = widget.palette().color(QPalette.Background)
    hex_value = color.name()
    rgb = hex_to_rgb(hex_value)
    return rgb


# Colorizing, color in RGB format
def update_widget_color(widget, color):
    widget.setStyleSheet(
        f"border: 1px solid gray; background: rgb({color[0]}, {color[1]}, {color[2]});"
    )
    return


def rgb_to_hex(rgb: typing.Union[list, tuple]) -> str:
    """Convert an RGB iterable into a hex color.

    Parameters:
    rgb : list, tuple
        A (3,) iterable of RGB values.

    Returns:
    str : A str representation of the RGB in hex format.
    """
    if not isinstance(rgb, (list, tuple)):
        raise TypeError("rgb must be passed as a list or tuple")
    if not len(rgb) == 3:
        raise TypeError("rgb must have exactly three values")

    hex_color = f"{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return hex_color


def hex_to_rgb(hex_value: str, normalize=True) -> tuple:
    """Convert a hex string into a tuple of three values.

    The returned values can either be uint8 or 0-1 floats.

    Parameters:
    hex : str

    normalized : bool
        Determines whether the values are returned as uint8 values or 0-1 float
        values. ``True`` return 0-1 float values, ``False`` return 0-255 values.
        Default ``True``.

    Returns:
    list : A tuple containing three uint8 values
    """
    if not isinstance(hex_value, str):
        raise TypeError("hex_value must be passed as a string")
    hex_value = hex_value.strip("#")

    rgb = tuple(int(hex_value[i : i + 2], base=16) for i in (0, 2, 4))

    if normalize:
        rgb = tuple(value / 255 for value in rgb)

    return rgb


def prep_opacity_update(p2):
    ids = [None] * 4
    return ids


def get_colortable(colormap):
    cmap = get_cmap(colormap)
    ctable = cmap(np.linspace(0, 1, 256)) * 255
    ctable = ctable.astype(np.uint8)
    return ctable


def get_clim(mesh, scalar):
    scalars = pv.utilities.get_array(mesh, scalar)
    clim = [np.min(scalars), np.max(scalars)]
    return clim


def load_cmaps():
    cmaps = ["Viridis", "Jet", "Turbo", "Plasma", "Hot", "HSV", "Rainbow"]

    return cmaps


#############################
### Edge hex colorization ###
#############################
def annotation_colorization_input(graph, meshes):
    # First get all of the colors from the graph
    hexes = graph.es["hex"]
    # then find the unique values
    unique_hexes = get_unique_hexes(hexes)

    # Add ROI
    if "roi_ID" in graph.es.attributes():
        ids = graph.es["roi_ID"]
    else:
        ids = match_hex_ids(hexes, unique_hexes)
        graph.es["roi_ID"] = ids

    # Zip the two together
    id_hex_dict = generate_id_hex_dict(ids, hexes)

    # First create a key that contains shifted colors from the original color
    shifted_dict = {
        roi_ID: generate_shifted_rgb(hex_to_rgb(id_hex_dict[roi_ID])) for roi_ID in ids
    }

    # Then create a key that links all ids to a random rainbow color
    colortable = get_colortable("gist_rainbow")[:, :3]
    rainbow_dict = {roi_ID: generate_rainbow_rgb(colortable) for roi_ID in ids}

    # Then iterate through each ID and add the original, shifted, or rainbow hexes to new arrays
    original_rgb = [
        hex_to_rgb(roi_hex) for roi_hex in hexes
    ]  # Just convert hexes to RGB
    shifted_rgb = [shifted_dict[roi_ID] for roi_ID in ids]
    rainbow_rgb = [rainbow_dict[roi_ID] for roi_ID in ids]

    del graph.es["hex"]
    # Add the color arrays to the graph
    graph.es["original_rgb"] = original_rgb
    graph.es["shifted_rgb"] = shifted_rgb
    graph.es["rainbow_rgb"] = rainbow_rgb

    # To re-randomize shifted colors, keep track of the ID and the original color that it pointed it
    meshes.id_hex_dict = id_hex_dict

    return graph


def get_unique_hexes(hexes):
    unique = []
    for hex_val in hexes:
        if hex_val not in unique:
            unique.append(hex_val)
    return unique


# Build an id array that matches to the corresponding
# unique hex values in the original array
def match_hex_ids(hexes, unique_hexes):
    hex_array = np.array(hexes)
    id_array = np.zeros(hex_array.shape[0])
    for i, unique_hex in unique_hexes:
        indices = np.where(hex_array == unique_hex)
        id_array[indices] = i
    return id_array


def generate_id_hex_dict(ids, hexes):
    id_to_hex = {roi_ID: hexes[i] for i, roi_ID in enumerate(ids)}
    return id_to_hex


# This function is set up to generate a random rgb rainbow color from a rainbow input
def generate_shifted_rgb(rgb):
    shift = np.random.uniform(-0.25, 0.25, 3)
    rgb = np.abs(np.array(rgb) - shift)
    rgb[rgb > 1] = 1
    rgb = rgb.tolist()
    return rgb


def generate_rainbow_rgb(colortable):
    rgb = colortable[np.random.randint(0, 256)]
    # h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
    # rgb = [i for i in colorsys.hls_to_rgb(h,l,s)]
    return rgb


def randomize_mesh_colors(meshes, rainbow=False, shifted=False):
    id_hex_dict = meshes.id_hex_dict

    # Randomize rainbow colors.
    if rainbow:
        # Generate a new rainbow color for each unique color
        colortable = get_colortable("gist_rainbow")[:, :3]  # sent back as RGBA
        id_rainbow_dict = {
            roi_ID: generate_rainbow_rgb(colortable) for roi_ID in id_hex_dict.keys()
        }

        for mesh in meshes.iter_vessel_meshes():
            if not mesh:
                continue
            # Get the rainbow and id arrays
            rainbow_array = mesh["Rainbow_RGB"]
            ids = mesh["ids"]
            for key in id_rainbow_dict.keys():
                indices = np.where(ids == key)
                # Convert the old rainbow colors into the new ones
                rainbow_array[indices] = id_rainbow_dict[key]
            mesh["Rainbow_RGB"] = rainbow_array  # Update the mesh

    # Reshift the original RGB values
    if shifted:
        # Create a new dict that matches ids to shifted RGBs based on their original color
        id_shifted_dict = {
            roi_ID: generate_shifted_rgb(hex_to_rgb(id_hex_dict[roi_ID]))
            for roi_ID in id_hex_dict.keys()
        }

        for mesh in meshes.iter_vessel_meshes():
            if not mesh:
                continue
            # Get the shifted color and id arrays
            shifted_array = mesh["Shifted_RGB"]
            ids = mesh["ids"]
            for key in id_shifted_dict.keys():
                indices = np.where(ids == key)
                # Convert the old shifted to the new shifted
                shifted_array[indices] = id_shifted_dict[key]
            mesh["Shifted_RGB"] = shifted_array  # Update the mesh

    return


#######################
### Analysis Speeds ###
#######################
def get_time(tic_time):
    time = pf() - tic_time
    if time > 3600:
        time /= 3600
        speed = f"{time:.1f} hours"
    if time > 60:
        time /= 60
        speed = f"{time:.1f} minutes"
    else:
        speed = f"{time:.1f} seconds"
    return speed


##########################
### Pyvista Processing ###
##########################
# Stripped from pyvista==0.29.1. Was removed in the higher version for some reason
def remove_legend(plotter, actor, reset_camera=False, render=False):
    """Remove this actor's mapper from the given plotter's _scalar_bar_mappers."""
    try:
        mapper = actor.GetMapper()
    except AttributeError:
        return
    for name in list(plotter.scalar_bars._scalar_bar_mappers.keys()):
        try:
            plotter.scalar_bars._scalar_bar_mappers[name].remove(mapper)

        except ValueError:
            pass

        if len(plotter.scalar_bars._scalar_bar_mappers[name]) < 1:
            slot = plotter._scalar_bar_slot_lookup.pop(name, None)
            if slot is not None:
                # plotter.scalar_bars._scalar_bar_widgets.pop(name) # For interactive widgets
                plotter.scalar_bars._scalar_bar_mappers.pop(name)
                plotter.scalar_bars._scalar_bar_ranges.pop(name)
                plotter.remove_actor(
                    plotter.scalar_bars._scalar_bar_actors.pop(name),
                    reset_camera=reset_camera,
                    render=True,
                )
                plotter._scalar_bar_slots.add(slot)
    return


def get_scalar(comboBox):
    scalar = comboBox.currentText()
    if scalar == "PAF %":
        scalar = "Volume"
    return scalar
