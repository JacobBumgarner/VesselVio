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
from library.annotation import roi_processing

from numba import njit, prange


########################
### ROI Segmentation ###
########################
@njit(parallel=True, nogil=True, cache=True)
def segment_volume(labeled_volume, mins, maxes, segmentation_id):
    """Given a labeled volume and ROI bounds, segment the loaded id.

    Parameters:
    labeled_volume : np.ndarray
        An ndim=3 array containing labeled regions

    mins : np.ndarray
        An (3,) array containing the lower bounds of the ROI.

    mins : np.ndarray
        An (3,) array containing the upper bounds of the ROI.

    segmentation_id: int
        An int id of the volume to segment

    Returns:
    np.ndarray : An ndim=3 array where the region of interest is segmented.
    """
    # Isolate the segmented region from the main volume
    volume = labeled_volume[
        mins[0] : maxes[0], mins[1] : maxes[1], mins[2] : maxes[2]
    ].copy()
    volume = np.asarray(volume, dtype=np.uint8)

    # Iterate through the volume to segmented the id
    for z in prange(volume.shape[0]):
        for y in range(volume.shape[1]):
            for x in range(volume.shape[2]):
                p = volume[z, y, x]
                if p and p != segmentation_id:
                    volume[z, y, x] = 0
                elif p:
                    volume[z, y, x] = 1
    return volume


def segmentation_input(mins, maxes, segmentation_id, verbose=False):
    if verbose:
        t = pf()
        print("Segmenting ROI from volume...", end="\r")

    labeled_volume = ImProc.load_labeled_volume_cache()
    volume = segment_volume(labeled_volume, mins, maxes, segmentation_id)
    del labeled_volume

    if verbose:
        print(f"ROI segmented in {pf() - t:0.2f} seconds.")
    return volume


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
    volume, a_slice, slice_volumes, volume_updates, ROI_dict, ROI_keys, mins, maxes, z
):
    ROI_keys = set(ROI_keys)
    for y in prange(volume.shape[1]):
        for x in prange(volume.shape[2]):
            p = a_slice[y, x]
            if p and p in ROI_keys:
                ROI_id = ROI_dict[p]
                slice_volumes += volume_updates[ROI_id]
                if volume[z, y, x]:
                    volume[z, y, x] = ROI_id + 1
                    update_bounds(mins, maxes, z, y, x, ROI_id)
            else:
                volume[z, y, x] = 0
    return


#######################
### Volume Labeling ###
#######################
## RGB Atlas processing (Mostly likely from QuickNII or VisuAlign)
def RGB_labeling_input(volume, annotation_folder, ROI_array, verbose=False):
    # Load the images from the RGB annotation folder
    annotation_images = ImProc.dir_files(annotation_folder)

    if not ImProc.RGB_dim_check(annotation_images, volume.shape, verbose=verbose):
        return None, None, None, None

    # Prepare all of the necessary items
    id_dict, id_keys, ROI_volumes, volume_updates = roi_processing.prep_ROI_array(
        ROI_array
    )
    slice_volumes = ROI_volumes.copy()

    # Convert RGB_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    minima, maxima = roi_processing.build_minima_maxima_arrays(volume, ROI_array)

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
        ROI_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print("\r", end="")  # clear previous output
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
            )

    return volume, ROI_volumes, minima, maxima


###########################
### ID Volume Labeling ####
###########################
# For images that have dtype incompatible with numba
def nn_id_labeling(volume, a_memmap, ROI_array, verbose=False):
    # Prepare all of the necessary items
    id_dict, id_keys, ROI_volumes, volume_updates = roi_processing.prep_ROI_array(
        ROI_array
    )
    slice_volumes = ROI_volumes.copy()

    # Convert id_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    minima, maxima = roi_processing.build_minima_maxima_arrays(ROI_array, volume)

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
        ROI_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
            )

    return volume, ROI_volumes, minima, maxima


### Numba dtype compatible segmentation
@njit(parallel=True, nogil=True, cache=True)
def numba_id_labeling(vprox, a_volume, ROI_array):
    id_dict, id_keys, ROI_volumes, volume_updates = roi_processing.prep_ROI_array(
        ROI_array
    )

    minima, maxima = roi_processing.build_minima_maxima_arrays(ROI_array, vprox)

    for z in prange(a_volume.shape[0]):
        for y in range(a_volume.shape[1]):
            for x in range(a_volume.shape[2]):
                p = a_volume[z, y, x]
                if p and p in id_keys:
                    ROI_id = id_dict[p]
                    ROI_volumes += volume_updates[ROI_id]
                    if vprox[z, y, x]:
                        vprox[z, y, x] = ROI_id + 1
                        update_bounds(minima, maxima, z, y, x, id_dict[p])
                elif vprox[z, y, x]:
                    vprox[z, y, x] = 0
    maxima = maxima + 1
    return vprox, ROI_volumes, minima, maxima


# Label the volume with id-based annotations
def id_labeling_input(volume, annotation_file, ROI_array, verbose=False):
    # Load a memmap of the annotation file
    annotation_memmap = ImProc.load_nii_volume(annotation_file)

    # # Make sure volume and annotation are of same shape.
    if not ImProc.id_dim_check(annotation_memmap, volume.shape, verbose=verbose):
        return None, None, None, None

    # Check to see that the dtype is appropriate for numba
    numba_seg = ImProc.dtype_check(annotation_memmap)

    if numba_seg:
        labeled_volume, ROI_volumes, mins, maxes = numba_id_labeling(
            volume, annotation_memmap, ROI_array
        )
    else:
        labeled_volume, ROI_volumes, mins, maxes = nn_id_labeling(
            volume, annotation_memmap, ROI_array, verbose=verbose
        )

    return labeled_volume, ROI_volumes, mins, maxes


# Given an annotation file and region, segment the region from the volume
def volume_labeling_input(
    volume, annotation_file, ROI_array, annotation_type, verbose=False
):

    if verbose:
        t = pf()
        print("Labeling volume...", end="\r")

    # Label our volume
    if annotation_type == "ID":
        labeled_volume, ROI_volumes, mins, maxes = id_labeling_input(
            volume, annotation_file, ROI_array, verbose=verbose
        )
    elif annotation_type == "RGB":
        labeled_volume, ROI_volumes, mins, maxes = RGB_labeling_input(
            volume, annotation_file, ROI_array, verbose=verbose
        )

    # Cache the labeled volume
    if labeled_volume is not None:
        if verbose:
            print(f"Volume labeling completed in {pf() - t:0.2f} seconds")
        ImProc.cache_labeled_volume(labeled_volume, verbose=verbose)

    return ROI_volumes, mins, maxes
