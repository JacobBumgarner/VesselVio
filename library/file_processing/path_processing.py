"""
Functions used to standardize and manage file paths.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os

from library import os_checks


def std_path(path):
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


def get_desktop_path():
    """Return the filepath to the user's desktop

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
