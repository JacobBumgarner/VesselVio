"""
Annotation volume processing backend.

Used for ID (int or float) or RGB based annotations.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from time import perf_counter as pf
from typing import Tuple, Union

import cv2
import numba
import numpy as np
from library import image_processing as ImProc
from library.annotation import segmentation_prep

from library.file_processing.path_processing import get_directory_image_files
from numba import njit, prange


########################
### General Labeling ###
########################
@njit(cache=False)
def update_ROI_bounds(
    minima: np.ndarray, maxima: np.ndarray, z: int, y: int, x: int, index: int
) -> None:
    """Update the current ROI bounds array based on input point coordinates.

    Parameters
    ----------
    minima : np.ndarray
        The array containing the ROI minima.
    maxima : np.ndarray
        The array containing the ROI maxima.
    z : int
        The z position of the point.
    y : int
        The y position of the point.
    x : int
        The x position of the point.
    index : int
        The index of the current ROI. Used to update the minima and maxima arrays.
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
    id_dict: numba.typed.typeddict.Dict,
    id_dict_keyset: np.ndarray,
    minima: np.ndarray,
    maxima: np.ndarray,
    z: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a slice of vasculature with a corresponding annotation volume slice.

    Parameters
    ----------
    volume : np.ndarray
        The 3D input volume to annotate.
    annotation_slice : np.ndarray
        The slice of annotation volume used to label a slice of the input volume.
    slice_volumes : np.ndarray
        An empty array used to store the volumes of the individual ROIs in annotation slice.
    volume_updates : np.ndarray
        An identity matrix used to update the slice volumes. This matrix is needed
        because Numba can only keep track of array slice updates in parallel.
    id_dict : numba.typed.typeddict.Dict
        The dictionary where each item is the index of the ROIs in the `slice_volumes`,
        `minima`, and `maxima` arrays. The keys for these items are the annotation ROI
        IDs.
    id_dict_keyset : np.ndarray
        The set of the ID keys used in the id_dict. Must be passed as a np.ndarray and
        then converted to set for this function.
    minima : np.ndarray
        The array containing the bounds minima for the regions.
    maxima : np.ndarray
        The array containing the bounds minima for the regions.
    z : int
        The z index of the input volume.

    Returns
    -------
    volume : np.ndarray
        The input volume with the newly labeled slice.
    slice_volumes : np.ndarray
        The filled array indicating the voxel volumes of the individual ROIs in the
        annotated slice.
    minima : np.ndarray
        The updated array containing the ROI minima.
    maxima : np.ndarray
        The updated array containing the ROI maxima.
    """
    id_dict_keyset = set(id_dict_keyset)  # convert from list to set
    for y in prange(volume.shape[1]):
        for x in range(volume.shape[2]):
            # get the value of the element
            point_value = annotation_slice[y, x]
            if point_value and point_value in id_dict_keyset:  # check if its valid
                roi_id = id_dict[point_value]
                slice_volumes += volume_updates[roi_id]
                if volume[z, y, x]:
                    volume[z, y, x] = roi_id + 1  # roi_ids start at 0
                    update_ROI_bounds(minima, maxima, z, y, x, roi_id)
            elif volume[z, y, x]:  # if the point is non-zero, set it to 0
                volume[z, y, x] = 0

    return volume, slice_volumes, minima, maxima


####################
### RGB-Specific ###
####################
@njit(cache=False)
def convert_bgr_to_int(bgr_array: np.ndarray) -> np.ndarray:
    """Collapse an BGR array into a single value along the last dimension.

    This function conducts bitwise shifts of the RGB values to identify the
    unique integer value associated with each color. This serves to consolidate
    the RGB and ID-based annotation analysis pipelines.

    Parameters
    ----------
    bgr_array : np.ndarray
        A BGR input array loaded with cv2.imread(). This array contains the colorized
        annotations for the input volumes. Should be of dimensions (m, n, 3)

    Returns
    -------
    np.ndarray
        An (m, n) dimensional array, where the final dimension of the input BGR image
        has been converted to the unique bitshifted integer associated with the RGB
        values.
    """
    # We want to actually do this as RGB, so swap 0,1,2
    int_array = (bgr_array[..., 2] << 16) | (bgr_array[..., 1] << 8) | bgr_array[..., 0]
    return int_array.astype(np.uint32)


def volume_sliced_labeling(
    volume: np.ndarray,
    annotation: Union[np.memmap, str],
    roi_array: np.ndarray,
    id_labeling: bool = False,
    verbose: bool = False,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a vasculature volume slice-by-slice with an input annotation dataset.

    This function handles annotation labeling or both RGB-based annotation volumes and
    annotation volumes with dtypes that are not compatible with Numba.

    RGB annotations can be constructed manually or can be created using programs
    like QuickNII or VisuAlign.

    ID-based annotations often come from annotation atlases such as the
    "p56 Adult Mouse Brain" atlas from the Allen Institute, or from manual
    segmentations made in programs like 3DSlicer or ITK-Snap.

    Parameters
    ----------
    volume : np.ndarray
        The input vasculature volume that will be labeled for subsequent ROI
        segmentations and analyses.
    annotation : Union[np.memmap, str]
        Depending on the type of annotation volume, this argument should either be
        a np.memmap if the volume has int-based annotations, or a str of the annotation
        image file directory if the volume has RGB-based annotations.
        The filepath to the folder that contains the RGB images with the labeled
        regions of interest.
    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.
    id_labeling : bool, optional
        Whether the annotation volume is ID-based. If False, converts to an RGB-based
        labeling. Defaults to False.
    verbose : bool, optional
        Defaults to False.

    Returns
    -------
    volume : np.ndarray
        The labeled volume.
    roi_volumes : np.ndarray
        The an (n,) dimensional array where each element represents the number of voxels
        present in each ROI. The index of these elements corresponds with the index of
        the ROIs from the input roi_array.
    minima : np.ndarray
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.
    maxima : np.ndarray
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    # If we're using an RGB volume, first load the RGB folder images
    if not id_labeling:
        annotation_images = get_directory_image_files(annotation)

        # Check dimensions. This was already done for the ID volume.
        if not ImProc.RGB_dim_check(annotation_images, volume.shape, verbose=verbose):
            return None, None, None, None

    # Prepare all of the necessary objects
    id_dict, id_dict_keyset = segmentation_prep.construct_id_dict(roi_array)

    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)
    slice_volumes = roi_volumes.copy()

    id_dict_keyset = np.asarray(list(id_dict_keyset))  # Numba needs this as an array

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(volume, roi_array)

    # Label each slice of the vasculature volume slice-by-slice
    slices = volume.shape[0] if id_labeling else len(annotation_images)
    for i in range(slices):
        t = pf()

        # First prep the input slice
        if id_labeling:
            annotation_slice = ImProc.get_annotation_slice(annotation, i)
        else:

            image = cv2.imread(annotation_images[i])
            annotation_slice = convert_bgr_to_int(image)  # convert the RGB

        # Label the corresponding slice of vasculature
        volume, slice_volumes, minima, maxima = label_slice(
            volume,
            annotation_slice,
            slice_volumes,
            volume_updates,
            id_dict,
            id_dict_keyset,
            minima,
            maxima,
            i,
        )

        # Update the ROI volumes
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
### Numba dtype compatible segmentation
@njit(parallel=True, nogil=True, cache=False)
def volume_labeling(
    volume: np.ndarray, annotation_memmap: np.memmap, roi_array: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label a vasculature volume from a Numba compatible ID annotation volume.

    This function is built specifically for annotation volumes that have dtypes
    that are compatible with Numba.

    ID-based annotations often come from annotation atlases such as the
    "p56 Adult Mouse Brain" atlas from the Allen Institute, or from manual
    segmentations made in programs like 3DSlicer or ITK-Snap.

    Parameters
    ----------
    volume : np.ndarray
        The input volume to be labeled.
    annotation_memmap : np.memmap
        The memory-mapped annotatino volume.
    roi_array : np.ndarray
        The ROI_array built with the ``segmentation_prep.build_roi_array``
        function. Contains the family of int-based RGB values that represent
        each of the ROIs.

    Returns
    -------
    volume : np.ndarray
        The labeled volume.
    roi_volumes : np.ndarray
        The an (n,) dimensional array where each element represents the number of voxels
        present in each ROI. The index of these elements corresponds with the index of
        the ROIs from the input roi_array.
    minima : np.ndarray
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.
    maxima : np.ndarray
        An (n,3) shaped array containing the maxima for each ROI. Used for
        segmentation bounding.
    """
    id_dict, id_dict_keyset = segmentation_prep.construct_id_dict(roi_array)
    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(volume, roi_array)

    for z in prange(annotation_memmap.shape[0]):
        for y in range(annotation_memmap.shape[1]):
            for x in range(annotation_memmap.shape[2]):
                point_value = annotation_memmap[z, y, x]
                if point_value and point_value in id_dict_keyset:
                    roi_id = id_dict[point_value]
                    roi_volumes += volume_updates[roi_id]
                    if volume[z, y, x]:
                        volume[z, y, x] = roi_id + 1
                        update_ROI_bounds(minima, maxima, z, y, x, id_dict[point_value])
                elif volume[z, y, x]:
                    volume[z, y, x] = 0

    return volume, roi_volumes, minima, maxima


# Label the volume with id-based annotations
def id_labeling_input(
    volume: np.ndarray,
    annotation_file: str,
    roi_array: np.ndarray,
    verbose: bool = False,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Label an input volume with a corresponding ID-based .nii annotation volume.

    Parameters
    ----------
    volume : np.ndarray
        The input volume that will be labeled.
    annotation_file : str
        The filepath to the NIfTI annotation volume.
    roi_array : np.ndarray
        The ROI array constructed with the ``segmentation_prep.buile_roi_array``
        function. Contains the family of int values that represent each structure in the
        ROIs.
    verbose : bool, optional
        Print the status of the analysis, by default False

    Returns
    -------
    volume : np.ndarray
        The labeled volume.
    roi_volumes : np.ndarray
        The an (n,) dimensional array where each element represents the number of voxels
        present in each ROI. The index of these elements corresponds with the index of
        the ROIs from the input roi_array.
    minima : np.ndarray
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.
    maxima : np.ndarray
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
        labeled_volume, roi_volumes, minima, maxima = volume_labeling(
            volume, annotation_memmap, roi_array
        )
    else:
        labeled_volume, roi_volumes, minima, maxima = volume_sliced_labeling(
            volume, annotation_memmap, roi_array, id_labeling=True, verbose=verbose
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
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Label an input volume with a corresponding annotation volume.

    This is the input function used to label vasculature volumes with annotations. The
    function dispatches the input arguments to the appropriate argument, which depends
    on whether the annotation volumes are ID or RGB based and whether they have Numba
    compatible dtypes.

    After the volume has been labeled, an .npy copy of the labeled volume will be
    cached onto the disk. Disk space availability should be pre-checked before this
    function is called, as this is not a forward-facing function.

    Parameters
    ----------
    volume : np.ndarray
        The input volume to be labeled. This volume will be cached as a .npy file after
        it has been labeled.
    annotation_file : str
        The filepath to the input annotation volume. This path should point to either
        a NIfTI file or a directory of RGB images.
    roi_array : np.ndarray
        _description_
    annotation_type : str
        The ROI array constructed with the ``segmentation_prep.buile_roi_array``
        function. Contains the family of int values that represent each structure in the
        ROIs.
    cache_directory : str, optional
        The directory where the labeled volume should be cached, by default None
    verbose : bool, optional
        Print the status of the labeling, by default False

    Returns
    -------
    roi_volumes : np.ndarray
        The an (n,) dimensional array where each element represents the number of voxels
        present in each ROI. The index of these elements corresponds with the index of
        the ROIs from the input roi_array.
    minima : np.ndarray
        An (n,3) shaped array containing the minima for each ROI. Used for
        segmentation bounding.
    maxima : np.ndarray
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
        labeled_volume, roi_volumes, minima, maxima = volume_sliced_labeling(
            volume, annotation_file, roi_array, verbose=verbose
        )

    # Cache the labeled volume
    if labeled_volume is not None:
        if verbose:
            print(f"Volume labeling completed in {pf() - t:0.2f} seconds.")
        ImProc.cache_labeled_volume(labeled_volume, cache_directory, verbose=verbose)

    return roi_volumes, minima, maxima
