"""
Annotation volume processing backend.

Used for ID (int or float) or RGB based annotations.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import typing
from time import perf_counter as pf

import cv2
import numba
import numpy as np

from library import image_processing as ImProc
from library.annotation import segmentation_prep
from numba import njit, prange


########################
### General Labeling ###
########################
@njit(cache=False)
def update_bounds(
    minima: np.ndarray, maxima: np.ndarray, z: int, y: int, x: int, index: int
) -> typing.Tuple[np.ndarray, np.ndarray]:
    """Given XYZ coordinates, update the bounds for the current region.

    Parameters:
    minima : np.ndarray

    maxima : np.ndarray

    z : int

    y : int

    x : int

    index : int
        The index of the minima/maxima array to update.

    Returns:
    np.ndarray : minima

    np.ndarray : maxima
    """
    if z < minima[index, 0]:
        minima[index, 0] = z
    elif z > maxima[index, 0]:
        maxima[index, 0] = z

    if y < minima[index, 1]:
        minima[index, 1] = y
    elif y > maxima[index, 1]:
        maxima[index, 1] = y

    if x < minima[index, 2]:
        minima[index, 2] = x
    elif x > maxima[index, 2]:
        maxima[index, 2] = x

    return


# Label a slice of a volume with a corresponding annotation slice
# Used for id-based and hashed-RGB annotations
@njit(parallel=True, nogil=True)
def label_slice(
    volume: np.ndarray,
    annotation_slice: np.ndarray,
    slice_volumes: np.ndarray,
    volume_updates: np.ndarray,
    roi_dict: numba.typed.typeddict.Dict,
    roi_keys: np.ndarray,
    minima: np.ndarray,
    maxima: np.ndarray,
    z: int,
):
    """Label a single slice of a volume with an annotation volume.

    Iterates through the annotation array while searching for annotation_ids
    that match the ids input by the user. If an id is found, the non-zero
    corresponding volume voxels are labeled with keyed id.

    Parameters:
    volume : np.ndarray

    annotation : np.ndarray

    slice_volumes : np.ndarray

    volume_updates : np.ndarray

    roi_dict : numba.typed.typeddict.Dict

    roi_keys : np.ndarray

    minima: np.ndarray

    maxima: np.ndarray

    z: int
        Used to access the slice of the input volume and to update the
        ``minima`` and ``maxima`` bounding arrays.
    """
    roi_keys = set(roi_keys)
    for y in prange(volume.shape[1]):
        for x in range(volume.shape[2]):
            # get the value of the element
            point_value = annotation_slice[y, x]
            if point_value and point_value in roi_keys:  # check if its valid
                roi_id = roi_dict[point_value]
                slice_volumes += volume_updates[roi_id]
                if volume[z, y, x]:
                    volume[z, y, x] = roi_id + 1  # roi_ids start at 0
                    update_bounds(minima, maxima, z, y, x, roi_id)
            elif volume[z, y, x]:  # if the point is non-zero, set it to 0
                volume[z, y, x] = 0

    return volume, slice_volumes, minima, maxima


####################
### RGB-Specific ###
####################
@njit(cache=False)
def convert_bgr_to_int(rgb_array) -> np.ndarray:
    """Collapse an RGB array into a single value along the RGB dimension.

    This function conducts bitwise shifts of the RGB values to identify the
    unique integer value associated with each color. This serves to consolidate
    the RGB and ID-based annotation analysis pipelines.

    Parameters:
    rgb_array : np.ndarray
        An n-dimensional array containing RGB values along the last axis.

    Returns:
    np.ndarray
        An n-1 dimensional array, where the RGB values have been collapsed into
        a single integer value.
    """
    # We want to actually do this as RGB, so swap 0,1,2
    int_array = (rgb_array[..., 2] << 16) | (rgb_array[..., 1] << 8) | rgb_array[..., 0]
    return int_array.astype(np.uint32)


def RGB_labeling_input(
    volume: np.ndarray,
    annotation_folder: str,
    roi_array: np.ndarray,
    verbose: bool = False,
) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a vasculature volume from a folder of RGB annotation images.

    RGB annotations can be constructed manually or can be created using programs
    like QuickNII or VisuAlign.

    Parameters:
    volume : np.ndarray

    annotation_folder : str
        The filepath to the folder that contains the RGB images with the labeled
        regions of interest.

    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    verbose : bool, optional
        Default ``False``.

    Returns:
    np.ndarray : volume
        The labeled volume.

    np.ndarray : roi_volumes
        The number of voxels present in each ROI.

    np.ndarray : minima
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.

    np.ndarray : maxima
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    # Load the images from the RGB annotation folder
    annotation_images = ImProc.dir_files(annotation_folder)

    if not ImProc.RGB_dim_check(annotation_images, volume.shape, verbose=verbose):
        return None, None, None, None

    # Prepare all of the necessary objects
    id_dict, id_keys = segmentation_prep.prep_roi_array(roi_array)

    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)
    slice_volumes = roi_volumes.copy()

    # Convert RGB_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(volume, roi_array)

    for i, file in enumerate(annotation_images):
        t = pf()
        image = cv2.imread(file)
        RGB_hash = convert_bgr_to_int(image)  # convert the RGB
        volume, slice_volumes, minima, maxima = label_slice(
            volume,
            RGB_hash,
            slice_volumes,
            volume_updates,
            id_dict,
            id_keys,
            minima,
            maxima,
            i,
        )
        roi_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print("\r", end="")  # clear previous output
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
            )

    return volume, roi_volumes, minima, maxima


###########################
### ID Volume Labeling ####
###########################
def nn_id_labeling(
    volume: np.ndarray,
    annotation_memmap: np.memmap,
    roi_array: np.ndarray,
    verbose: bool = False,
) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a vasculature volume from a numba incompatible ID annotation.

    This function is built specifically for annotation volumes that have dtypes
    that are incompatible with Numba.

    ID-based annotations often come from annotation atlases such as the
    "p56 Adult Mouse Brain" atlas from the Allen Institute, or from manual
    segmentations made in programs like 3DSlicer or ITK-Snap.

    Parameters:
    volume : np.ndarray

    annotation_memmap : np.memmap
        The annoa.

    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    verbose : bool, optional
        Default ``False``.

    Returns:
    np.ndarray : volume
        The labeled volume.

    np.ndarray : roi_volumes
        The number of voxels present in each ROI.

    np.ndarray : minima
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.

    np.ndarray : maxima
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    # Prepare all of the necessary objects
    id_dict, id_keys = segmentation_prep.prep_roi_array(roi_array)

    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)
    slice_volumes = roi_volumes.copy()

    # Convert id_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(volume, roi_array)

    # Process slice by slice
    for i in range(volume.shape[0]):
        t = pf()
        a_slice = ImProc.get_annotation_slice(annotation_memmap, i)
        volume, slice_volumes, minima, maxima = label_slice(
            volume,
            a_slice,
            slice_volumes,
            volume_updates,
            id_dict,
            id_keys,
            minima,
            maxima,
            i,
        )
        roi_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
            )

    return volume, roi_volumes, minima, maxima


### Numba dtype compatible segmentation
@njit(parallel=True, nogil=True, cache=False)
def numba_id_labeling(
    volume: np.ndarray, annotation_memmap: np.memmap, roi_array: np.ndarray
) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a vasculature volume from a numba compatible ID annotation volume.

    This function is built specifically for annotation volumes that have dtypes
    that are compatible with Numba.

    ID-based annotations often come from annotation atlases such as the
    "p56 Adult Mouse Brain" atlas from the Allen Institute, or from manual
    segmentations made in programs like 3DSlicer or ITK-Snap.

    Parameters:
    volume : np.ndarray

    annotation_memmap : np.memmap

    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    Returns:
    np.ndarray : volume
        The labeled volume.

    np.ndarray : roi_volumes
        The number of voxels present in each ROI.

    np.ndarray : minima
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.

    np.ndarray : maxima
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    id_dict, id_keys = segmentation_prep.prep_roi_array(roi_array)
    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(volume, roi_array)

    for z in prange(annotation_memmap.shape[0]):
        for y in range(annotation_memmap.shape[1]):
            for x in range(annotation_memmap.shape[2]):
                point_value = annotation_memmap[z, y, x]
                if point_value and point_value in id_keys:
                    roi_id = id_dict[point_value]
                    roi_volumes += volume_updates[roi_id]
                    if volume[z, y, x]:
                        volume[z, y, x] = roi_id + 1
                        update_bounds(minima, maxima, z, y, x, id_dict[point_value])
                elif volume[z, y, x]:
                    volume[z, y, x] = 0

    return volume, roi_volumes, minima, maxima


# Label the volume with id-based annotations
def id_labeling_input(
    volume: np.ndarray,
    annotation_file: str,
    roi_array: np.ndarray,
    verbose: bool = False,
) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label an input volume with a corresponding ID .nii annotation volume.

    Returns a list of None is the annotation file is incompatible. Doesn't raise
    and error as to not crash the application.

    Parameters:
    volume : np.ndarray

    annotation_file : str
        The filepath to the ".nii" type annotation.

    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    verbose : bool, optional
        Default ``False``.

    Returns:
    np.ndarray : volume
        The labeled volume.

    np.ndarray : roi_volumes
        The number of voxels present in each ROI.

    np.ndarray : minima
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.

    np.ndarray : maxima
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    # Load a memmap of the annotation file
    annotation_memmap = ImProc.load_nii_volume(annotation_file)

    # Make sure volume and annotation are of same shape.
    if not ImProc.id_dim_check(annotation_memmap, volume.shape, verbose=verbose):
        return None, None, None, None

    # Check to see that the dtype is appropriate for numba
    numba_seg = ImProc.dtype_check(annotation_memmap)

    if numba_seg:
        labeled_volume, roi_volumes, minima, maxima = numba_id_labeling(
            volume, annotation_memmap, roi_array
        )
    else:
        labeled_volume, roi_volumes, minima, maxima = nn_id_labeling(
            volume, annotation_memmap, roi_array, verbose=verbose
        )

    return labeled_volume, roi_volumes, minima, maxima


#####################
### General Input ###
#####################
# Given an annotation file and region, segment the region from the volume
def volume_labeling_input(
    volume: np.ndarray,
    annotation_file: str,
    roi_array: np.ndarray,
    annotation_type: str,
    cache_directory: str = None,
    verbose: bool = False,
):
    """Label an input volume with a corresponding annotation volume.

    The input function used to label vasculature volumes. Dispatches the
    labeling to the appropriate function based on whether the annotation
    is based on IDs or RGB values. After the volume has been labeled, an
    ``.npy`` copy of the labeled volume will be saved.

    Parameters:
    volume : np.ndarray

    annotation_file : str
        The filepath to the ".nii" type annotation.

    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    annotation_type : str
        The type of annotation. Options are ``["ID", "RGB"]``.

    cache_dir : str, optional
        The directory where an .npy copy of the labeled_volume will be cached.
        Default ``None``, which leads to a save in the ``library/cache/``
        folder.

    verbose : bool, optional
        Default ``False``.

    Returns:
    np.ndarray : volume
        The labeled volume.

    np.ndarray : roi_volumes
        The number of voxels present in each ROI.

    np.ndarray : minima
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.

    np.ndarray : maxima
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    if verbose:
        t = pf()
        print("Labeling volume...", end="\r")

    # Label our volume
    if annotation_type == "ID":
        labeled_volume, roi_volumes, minima, maxima = id_labeling_input(
            volume, annotation_file, roi_array, verbose=verbose
        )
    elif annotation_type == "RGB":
        labeled_volume, roi_volumes, minima, maxima = RGB_labeling_input(
            volume, annotation_file, roi_array, verbose=verbose
        )

    # Cache the labeled volume
    if labeled_volume is not None:
        if verbose:
            print(f"Volume labeling completed in {pf() - t:0.2f} seconds.")
        ImProc.cache_labeled_volume(labeled_volume, cache_directory, verbose=verbose)

    return roi_volumes, minima, maxima
