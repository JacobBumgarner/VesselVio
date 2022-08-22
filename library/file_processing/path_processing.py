"""Functions used to standardize and manage file paths."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import glob
import json
import os
import sys

from library import os_checks
from natsort import natsorted
from PyQt5.QtWidgets import QFileDialog


# General path processinv
def get_cwd() -> str:
    """Return the current working directory.

    Returns:
    str
    """
    try:
        wd = sys._MEIPASS
    except AttributeError:
        wd = os.getcwd()
    return std_path(wd)


def std_path(path) -> str:
    """Standardize path strings for cross-platform compatibility.

    Parameters:
    path : str, list, optional

    Returns:
    str, list

    """
    if isinstance(path, str):
        path = os.path.normpath(path)
    elif isinstance(path, (list, str)):
        path = [os.path.normpath(p) for p in path]
    else:
        raise TypeError(
            "path must be a single str filepath or a list of str filepaths."
        )

    return path


def get_desktop_path() -> str:
    """Return the filepath to the user's desktop.

    Returns:
    str

    """
    sys_os = os_checks.get_OS()
    if sys_os == "Darwin":
        load_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    elif sys_os == "Windows":
        load_dir = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
    load_dir = std_path(load_dir)
    return load_dir


def get_basename(filepath: str) -> str:
    """Return the basename of the filepath.

    Returns:
    str : basename
    """
    basename = os.path.basename(filepath)
    return basename


# Preferencdes cache loading and processing
def get_preferences_path() -> str:
    """Return the path to the preferences file.

    Returns:
    str : preferences_path
    """
    wd = get_cwd()
    preferences_path = os.path.join(wd, "library", "cache", "preferences.json")
    return preferences_path


def load_preferences() -> dict:
    """Open and return the preferences cache.

    Returns:
    dict : preferences
    """
    preferences_path = get_preferences_path()
    with open(preferences_path, "r") as f:
        preferences = json.load(f)

    return preferences


def update_preferences(preferences: dict) -> None:
    """Update the preferences file.

    Parameterse:
    preferences : dict
        The updated preferenes dict that will overwrite the current preferences.
    """
    preferences_path = get_preferences_path()
    with open(preferences_path, "w") as f:
        json.dump(preferences, f)


def load_results_dir() -> str:
    """Query the preferences.json to return a results folder.

    If a results folder has not been selected or if the previously selected
    folder no longer exists, return a False bool.

    Returns:
    str, None
        Return the results path as a string if it exists, otherwise None.

    """
    preferences = load_preferences()
    results_dir = preferences["results_dir"]

    if not os.path.exists(results_dir):
        results_dir = None
        preferences = load_preferences()
        preferences["results_dir"] = ""
        update_preferences(preferences)

    return results_dir


def set_results_dir(return_path: bool = False) -> str:
    """Open a file dialog to retrieve a results export path.

    If a folder is selected, the path is stored in the preferences for future
    exports.

    Parameters:
    return_path : bool
        Return the path of the results directory, if one was selected.
        Default ``False``.

    Returns:
    str, None
    """
    results_dir = QFileDialog.getExistingDirectory(
        QFileDialog(), "Select Results Folder", get_desktop_path()
    )
    if results_dir:
        results_dir = std_path(results_dir)
        preferences = load_preferences()
        preferences["results_dir"] = results_dir
        update_preferences(preferences)
    if not results_dir or not return_path:
        results_dir = None
    return results_dir


def get_directory_image_files(filepath: str, ext: str = ".png") -> list:
    """Return a list of the image files in the directory.

    Parameters
    ----------
    filepath : str
        The path of the folder to examine.
    ext : str, optional
        The extension of the image files to load, by default ".png"

    Returns
    -------
    list
        A sorted list of the input image files.
    """
    files = glob.glob(os.path.join(filepath, "*" + ext))
    files = natsorted(files)
    return files
