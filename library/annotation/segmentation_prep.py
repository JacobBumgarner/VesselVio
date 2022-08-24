"""ROI processing functions for ID and RGB region segmentations."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from typing import Tuple, Union

import numpy as np
from numba import njit


def construct_roi_array(
    annotation_dict: dict, annotation_type: str = "ID"
) -> np.ndarray:
    """Construct an ROI array where each row contains the children IDs of each ROI.

    Parameters
    ----------
    annotation_dict : dict
        A VesselVio annotation dictionary created with the
        ``tree_processing.convert_annotation_data`` function or loaded with the
        ``tree_processing.load_vesselvio_annotation_file`` function.
        An example annotation_dict might look like this:
        {"Eye": {"colors": ["#190000"], "ids": [1]}}
    annotation_type : str, optional
        The type of annotation data to be pulled from the annotation_dict. Must be either
        "ID" or "RGB", by default "ID"

    Returns
    -------
    roi_array : np.ndarray
        An array of (n,m) shape, where n is the number of ROIs, and m is
        the largest number of children that an individual ROI has. Each row of the array
        contains the IDs of the children in the array. If the row has fewer children
        than the length of the array, the rest of the elements after the final child are
        filled with zeros. This array is necessary for Numba processing.

    Raises
    ------
    TypeError
        Raised error if the ``annotation_type`` is not a string.
    ValueError
        Raised error if the ``annotation_type`` is not either "ID" or "RGB".
    """
    # isolate the ROIs
    if not isinstance(annotation_type, str):
        raise TypeError("annotation_type must be a string.")
    if not annotation_type.lower() in {"id", "rgb"}:
        raise ValueError("annotation_type must be one of the follow: 'ID', 'RGB'.")

    dict_key = "ids" if annotation_type.lower() == "id" else "colors"
    ROIs = [annotation_dict[key][dict_key] for key in annotation_dict.keys()]

    if annotation_type == "RGB":
        ROIs = convert_hex_list_to_int_list(ROIs)

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


def convert_hex_list_to_int_list(hex_family_tree: list) -> list:
    """Convert a list of hex colors into a list of int values.

    Parameters
    ----------
    hex_family_tree : list
        An (m, n) shaped list, where each m index is an individual ROI, and each n
        element is the hex color associated with the ROI child.

    Returns
    -------
    list
        An (m, n) shaped list where the child hex colors have been converted to their
        corresponding unique integer value. These int_lists are used to identify the
        children in the int-converted RGB values in the ``labeling.convert_bgr_to_int``
        function.
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


"""Use the roi_array to prepare the objects for a segmentation.

Parameters:
roi_array : np.ndarray
    The roi_array created with the ``construct_roi_array` function. Stores the
    ids associated with each parent region.

Returns:
id_dict : dict
    A dict where each key points to the row number of the parent structure
    that it is related to.

id_dict_keyset : set
    The unique set of ids.
"""


@njit(cache=True)
def construct_id_dict(roi_array: np.ndarray) -> Tuple[dict, set]:
    """Construct an ID dictionary from an input roi_array.

    Each key in this dictionary represents the ID of the selected ROI, and each key
    points to the row that the ROI is located in the roi_array.

    For example, the "Eye" region ID might have children IDs `1` and `2`, and it may
    represent the third ROI selected for the analysis. The entries for the "Eye" ROI
    in this ID dictionary would be: ``1:2`` and ``2:2``. If either of ID values are
    identified in an analysis, the corresponding vasculature will be labeled with ``3``
    and the third row of the ROI volumes array will be updated appropriately.

    Parameters
    ----------
    roi_array : np.ndarray
        The ROI array constructed with a VesselVio annotation dict file sent to
        ``construct_roi_array``.

    Returns
    -------
    id_dict : dict
        The ID dictionary.
    id_dict_keyset : set
        A set of the keys in the dictionary. This object is returned in order to ensure
        that any 0s from the ROI array are removed from the dict keys.

    Tuple[dict, set]
        _description_
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
def construct_roi_volume_arrays(
    roi_array: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return an empty array used to record volume values and an identity array.

    These arrays are used to record the volumes of ROIs in the labeled volume. Because
    Numba can only keep track of array slice updates in parallel and not individual
    element updates, the ROI volumes array is updated with a slice of an identity
    matrix, where the slice is determined by the index of the ROI.

    Parameters
    ----------
    roi_array : np.ndarray
        The ROI array created with the ``construct_roi_array`` function. Used to inform
        the shape of the ROI volume and identity arrays.

    Returns
    -------
    roi_volume : np.ndarray
        An empty np.zeros() array used to add the ROI volume to.

    volume_update_array : np.ndarray
        An ``np.identity`` array used to update the element of interest during
        ``labeling.volume_slice_labeling``.
    """
    roi_volumes = np.zeros(roi_array.shape[0])
    volume_update_array = np.identity(roi_array.shape[0])
    return roi_volumes, volume_update_array


@njit(cache=True)
def construct_minima_maxima_arrays(
    volume_shape: Union[np.ndarray, list], n_rois: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Return arrays used to record the minima and maxima of each ROI.

    The arrays are returned by default with inverted values. I.e., the maxima array is
    filled with zeros, and the minima array is filled with the maximum index of the
    volume. During volume labeling, the location of each ROI voxel is compared to these
    arrays, and the arrays are updated as necessary.

    Parameters
    ----------
    volume : np.ndarray
        The shape of the volume that is going to be labeled.
    n_rois : int
        The number of ROIs to record minima and maxima for.

    Returns
    -------
    minima : np.ndarray
        An (m, 3) array used to record the [z, y, x] minima of each ROI, where each
        value is by default the largest index of each array.
    maxima : np.ndarray
        An (m, 3) array used to record the [z, y, x] maxima of each ROI, where each
        value is by default zero.
    """
    minima = np.ones((n_rois, 3), dtype=np.int_) * np.array(volume_shape)
    maxima = np.zeros((n_rois, 3), dtype=np.int_)
    return minima, maxima
