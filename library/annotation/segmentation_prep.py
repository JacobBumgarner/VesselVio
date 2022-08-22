"""ROI processing functions for ID and RGB region segmentations."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import typing

import numpy as np
from numba import njit


def build_roi_array(roi_dict: dict, annotation_type: str = "ID") -> np.ndarray:
    """Convert a list of parent and child annotations into into an roi_array.

    Given an roi_dict (Annotation Processing export), this function converts the
    parent structure list into

    Parameters:
    roi_dict : dict
        An roi_dict created from the Annotation Processing page. Must be pre-
        loaded using the `load_annotation_file` function.

    annotation_type : str, optional
        The type of annotation. Options [`"ID"`, `"RGB"`]. Default `"ID"`.

    Returns:
    np.array : roi_array
        An array of (n,m) shape, where n is the number of ROIs, and m is
        the largest number of children that an individual ROI has. Each row of the array
        contains the IDs of the children in the array. If the row has fewer children
        than the length of the array, the rest of the elements after the final child are
        filled with zeros. This array is necessary for Numba processing.
    """
    # isolate the ROIs
    if not isinstance(annotation_type, str):
        raise TypeError("annotation_type must be a string.")
    if not annotation_type.lower() in {"id", "rgb"}:
        raise ValueError("annotation_type must be one of the follow: 'ID', 'RGB'.")

    dict_key = "ids" if annotation_type.lower() == "id" else "colors"
    ROIs = [roi_dict[key][dict_key] for key in roi_dict.keys()]

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
    roi_array = np.zeros(
        (len(ROIs), max_len + 1), dtype=np.uint32
    )  # Make sure a zero is in every set ---
    for i, ROI in enumerate(ROIs):
        roi_array[i, : len(ROI)] = ROI
    return roi_array


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
def construct_id_dict(roi_array: np.ndarray) -> typing.Tuple[dict, set]:
    """Use the roi_array to prepare the objects for a segmentation.

    Parameters:
    roi_array : np.ndarray
        The roi_array created with the ``build_roi_array` function. Stores the
        ids associated with each parent region.

    Returns:
    id_dict : dict
        A dict where each key points to the row number of the parent structure
        that it is related to.

    id_dict_keyset : set
        The unique set of ids.
    """
    id_dict = dict()
    for n in range(roi_array.shape[0]):
        for roi_id in range(roi_array.shape[1]):
            if not roi_array[n, roi_id]:
                break  # Break if we're at the end of the ids
            id_dict[roi_array[n, roi_id]] = n

    id_dict_keyset = set(roi_array.flatten())
    id_dict_keyset.remove(0)
    return id_dict, id_dict_keyset


@njit(cache=True)
def prep_volume_arrays(roi_array) -> typing.Tuple[np.ndarray, np.ndarray]:
    """Prepare the arrays used to record ROI volumes.

    Parameters:
    roi_array : np.ndarray
        The ROI array created with the ``build_roi_array`` function.

    Returns:
    np.ndarray : roi_volumes
        An empty np.zeros() array used to add the ROI volume to.

    np.ndarray : volume_updates
        This is a complicated one... Hold on. Numba does not keep track of
        updates to individual numpy array elements in parallel processing.
        However, numba does keep track of whole-array updates during parallel
        processing. As such, volume_updates is an ``np.identity`` array used
        to update the element of interest during ``slice_labeling``.
    """
    roi_volumes = np.zeros(roi_array.shape[0])
    volume_updates = np.identity(roi_array.shape[0])
    return roi_volumes, volume_updates


@njit(cache=True)
def build_minima_maxima_arrays(
    volume: np.ndarray, roi_array: np.ndarray
) -> typing.Tuple[np.ndarray, np.ndarray]:
    """Return minima and maxima arrays for segmentation bounding.

    The maxima array starts with 0 values, and the minima array starts with the


    Parameters:
    volume : np.ndarray

    roi_array : np.ndarray

    Returns:
    np.ndarray : minima

    np.ndarray : maxima
    """
    minima = np.ones((roi_array.shape[0], 3), dtype=np.int_) * np.array(volume.shape)
    maxima = np.zeros((roi_array.shape[0], 3), dtype=np.int_)
    return minima, maxima
