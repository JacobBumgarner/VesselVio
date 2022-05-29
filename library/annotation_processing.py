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

import cv2
import numpy as np
from library import image_processing as ImProc
from library.annotation import segmentation_prep

from numba import njit, prange


######################
### RGB Processing ###
######################
@njit(cache=True)
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


######################
### Slice Labeling ###
######################
@njit(cache=True)
def update_bounds(minima, maxima, z, y, x, index):
    """Given XYZ coordinates, update the bounds for the current region.

    Parameters:
    minima : np.ndarray

    maxima : np.ndarray

    z : int

    y : int

    x : int

    index : int
        The index of the minima/maxima array to update.
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
def slice_labeling(
    volume, a_slice, slice_volumes, volume_updates, roi_dict, roi_keys, mins, maxes, z
):
    roi_keys = set(roi_keys)
    for y in prange(volume.shape[1]):
        for x in prange(volume.shape[2]):
            p = a_slice[y, x]
            if p and p in roi_keys:
                roi_id = roi_dict[p]
                slice_volumes += volume_updates[roi_id]
                if volume[z, y, x]:
                    volume[z, y, x] = roi_id + 1
                    update_bounds(mins, maxes, z, y, x, roi_id)
            else:
                volume[z, y, x] = 0
    return


#######################
### Volume Labeling ###
#######################
## RGB Atlas processing (Mostly likely from QuickNII or VisuAlign)
def RGB_labeling_input(volume, annotation_folder, roi_array, verbose=False):
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
        slice_labeling(
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
# For images that have dtype incompatible with numba
def nn_id_labeling(volume, a_memmap, roi_array, verbose=False):
    # Prepare all of the necessary objects
    id_dict, id_keys = segmentation_prep.prep_roi_array(roi_array)

    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)
    slice_volumes = roi_volumes.copy()

    # Convert id_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(roi_array, volume)

    # Process slice by slice
    for i in range(volume.shape[0]):
        t = pf()
        a_slice = ImProc.get_annotation_slice(a_memmap, i)
        slice_labeling(
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
@njit(parallel=True, nogil=True, cache=True)
def numba_id_labeling(vprox, a_volume, roi_array):
    id_dict, id_keys = segmentation_prep.prep_roi_array(roi_array)
    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(roi_array, vprox)

    for z in prange(a_volume.shape[0]):
        for y in range(a_volume.shape[1]):
            for x in range(a_volume.shape[2]):
                p = a_volume[z, y, x]
                if p and p in id_keys:
                    roi_id = id_dict[p]
                    roi_volumes += volume_updates[roi_id]
                    if vprox[z, y, x]:
                        vprox[z, y, x] = roi_id + 1
                        update_bounds(minima, maxima, z, y, x, id_dict[p])
                elif vprox[z, y, x]:
                    vprox[z, y, x] = 0

    return vprox, roi_volumes, minima, maxima


# Label the volume with id-based annotations
def id_labeling_input(volume, annotation_file, roi_array, verbose=False):
    # Load a memmap of the annotation file
    annotation_memmap = ImProc.load_nii_volume(annotation_file)

    # # Make sure volume and annotation are of same shape.
    if not ImProc.id_dim_check(annotation_memmap, volume.shape, verbose=verbose):
        return None, None, None, None

    # Check to see that the dtype is appropriate for numba
    numba_seg = ImProc.dtype_check(annotation_memmap)

    if numba_seg:
        labeled_volume, roi_volumes, mins, maxes = numba_id_labeling(
            volume, annotation_memmap, roi_array
        )
    else:
        labeled_volume, roi_volumes, mins, maxes = nn_id_labeling(
            volume, annotation_memmap, roi_array, verbose=verbose
        )

    return labeled_volume, roi_volumes, mins, maxes


# Given an annotation file and region, segment the region from the volume
def volume_labeling_input(
    volume, annotation_file, roi_array, annotation_type, verbose=False
):

    if verbose:
        t = pf()
        print("Labeling volume...", end="\r")

    # Label our volume
    if annotation_type == "ID":
        labeled_volume, roi_volumes, mins, maxes = id_labeling_input(
            volume, annotation_file, roi_array, verbose=verbose
        )
    elif annotation_type == "RGB":
        labeled_volume, roi_volumes, mins, maxes = RGB_labeling_input(
            volume, annotation_file, roi_array, verbose=verbose
        )

    # Cache the labeled volume
    if labeled_volume is not None:
        if verbose:
            print(f"Volume labeling completed in {pf() - t:0.2f} seconds")
        ImProc.cache_labeled_volume(labeled_volume, verbose=verbose)

    return roi_volumes, mins, maxes
