"""ROI processing functions for ID and RGB region segmentations."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import typing

import numpy as np
from numba import njit


def build_ROI_array(ROI_dict, annotation_type: str = "ID") -> np.ndarray:
    """Convert a list of parent and child annotations into into an ROI_array.

    Given an ROI_dict (Annotation Processing export), this function converts the
    parent structure list into

    Parameters:
    ROI_dict : dict
        An ROI_dict created from the Annotation Processing page. Must be pre-
        loaded using the `load_annotation_file` function.

    annotation_type : str
        The type of annotation. Options [`"ID"`, `"RGB"`]. Default `"ID"`.

    Returns:
    np.array : An ROI_Array
        An array of (n,m) shape, where `n` is the number of parents, and `m` is
        the largest number of children that an individual parent has.
    """
    # isolate the ROIs
    if not isinstance(annotation_type, str):
        raise TypeError("annotation_type must be a string.")
    if not annotation_type.lower() in {"id", "rgb"}:
        raise ValueError("annotation_type must be one of the follow: 'ID', 'RGB'.")

    dict_key = "ids" if annotation_type.lower() == "id" else "colors"
    ROIs = [ROI_dict[key][dict_key] for key in ROI_dict.keys()]

    if annotation_type == "RGB":
        ROIs = convert_hex_list_to_int(ROIs)

    ### REMOVE BEFORE FLIGHT ###
    ### REMOVE BEFORE FLIGHT ###
    # for ROI in ROIs:
    #     ROI += [r * -1 for r in ROI]
    ### REMOVE BEFORE FLIGHT ###
    ### REMOVE BEFORE FLIGHT ###

    max_len = find_max_children_count(ROIs)  # find depth of upcoming array

    # Convert into array, fill with ROI ids, leaving 0's behind rest
    ROI_array = np.zeros(
        (len(ROIs), max_len + 1), dtype=np.uint32
    )  # Make sure a zero is in every set ---
    for i, ROI in enumerate(ROIs):
        ROI_array[i, : len(ROI)] = ROI
    return ROI_array


def convert_hex_list_to_int(hex_family_tree: list) -> list:
    """Convert a list of hex colors into a list of int values.

    Given an (n,m) list of hex-based annotation representations, return an
    (n,m) shaped list of integer-RGB representations.

    Parameters:
    hex_list : list

    Returns:
    list
    """
    int_family_tree = [
        [int(hex_child, base=16) for hex_child in parent_tree]
        for parent_tree in hex_family_tree
    ]
    return int_family_tree


def find_max_children_count(parent_tree: list) -> int:
    """Return the size of the largest annotation family.

    Parameters:
    parent_tree : list
        An (n,m) list, where `n` represents the parents, and `m` represents
        their children.

    Returns:
    int
        Returns the largest identified `m` in the parent_tree.
    """
    max_children = 0
    for children in parent_tree:  # Find maximum length of ROI ids
        if len(children) > max_children:
            max_children = len(children)
    return max_children


@njit(cache=True)
def prep_ROI_array(id_array):
    """Given an id_array, create a key set,
    dict with hash keys that point to items that contain corresponding index,
    and ROI_volume/volume_update arrays"""
    id_dict = dict()
    for n in range(id_array.shape[0]):
        for ROI_id in range(id_array.shape[1]):
            if not id_array[n, ROI_id]:
                break  # Break if we're at the end of the ids
            id_dict[id_array[n, ROI_id]] = n

    id_keys = set(id_array.flatten())
    id_keys.remove(0)

    ROI_volumes = np.zeros(id_array.shape[0])
    volume_updates = np.identity(id_array.shape[0])

    return id_dict, id_keys, ROI_volumes, volume_updates


@njit()
def build_minima_maxima_arrays(
    volume: np.ndarray, ROI_array: np.ndarray
) -> typing.Tuple[np.ndarray, np.ndarray]:
    """Return minima and maxima arrays for segmentation bounding.

    The maxima array starts with 0 values, and the minima array starts with the


    Parameters:
    volume : np.ndarray

    ROI_array : np.ndarray

    Returns:
    np.ndarray : minima

    np.ndarray : maxima
    """
    minima = np.ones((ROI_array.shape[0], 3), dtype=np.int_) * np.array(volume.shape)
    maxima = np.zeros((ROI_array.shape[0], 3), dtype=np.int_)
    return minima, maxima


def RGB_duplicates_check(annotation_data) -> bool:
    """Determine whether duplicate colors exist among annotation regions.

    For RGB processing, it is important to determine whether individual regions
    share the same color coded values. For example, in the hippocampal formation
    of mice, the Allen Brain Atlas color coding scheme uses both ``"7ED04B"``
    and ``"66A83D"`` for the Ammon's Horn and Dentate Gyrus regions. If both
    regions were selected for separate analyses, the results would include
    vessels from both regions.

    Parameters:
    annotation_data : dict
        A dict output of the `Annotation Processing` export that has been pre-
        processed using `prep_RGB_annotation`.

    Returns:
    bool : True if duplicates present, False otherwise
    """
    nested_hexes = [annotation_data[key]["colors"] for key in annotation_data.keys()]
    hexes = [color for nested_colors in nested_hexes for color in nested_colors]

    duplicates = len(hexes) != len(set(hexes))
    return duplicates
