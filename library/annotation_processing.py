"""
Annotation volume processing backend. Used for ID (int or float) or RGB based annotations.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os
from time import perf_counter as pf

import cv2
import numpy as np

from library import helpers

from numba import njit, prange


#######################
### Tree Processing ###
#######################
class JSON_Options:
    def __init__(
        self, name="name", children="children", color="color_hex_triplet", id="id"
    ):
        self.name = name
        self.children = children
        self.id = id
        self.color = color


# Convert lists of hexes to list of RGB values for annotation visualization
def hex_to_rgb(hexes):
    rgb = []
    for hex in hexes:
        rgb.append(
            list(int(hex[i : i + 2], 16) for i in (0, 2, 4))
        )  # Convert hex to RGB 255
    return rgb


# Find Colors and IDs of children structures
def find_children(tree, colors, ids, tree_info):
    for child in tree:
        ids.append(child[tree_info.id])
        colors.append(child[tree_info.color])
        if child[tree_info.children]:
            find_children(child[tree_info.children], colors, ids, tree_info)
    return


# Identify the parent structure and return its family.
def find_family(tree, name, tree_info):
    for child in tree:
        if child[tree_info.name] == name:
            # Grab the id and colors of the parent
            colors = [child[tree_info.color]]
            ids = [child[tree_info.id]]
            find_children(child[tree_info.children], colors, ids, tree_info)
            colors = list(set(colors))  # Get set of unique colors
            return {"colors": colors, "ids": ids}
        elif child[tree_info.children]:
            family = find_family(child[tree_info.children], name, tree_info)
            if family:
                return family
    return None


# Tree ids is a list of string names for each region
def tree_processing(file=None, names=None, tree_info=None):
    # Load the default file if there isn't one
    if not file:
        wd = get_cwd()
        file = helpers.std_path(
            os.path.join(wd, "library", "annotation_trees", "p56 Mouse Brain.json")
        )

    # Set up the JSON_Options object to know how to read the JSON file
    if not tree_info:
        tree_info = JSON_Options()

    # Load the annotation tree
    with open(file) as f:
        file = json.load(f)
        tree = file[tree_info.children]  # Load all children of the root

    # Populate the annotation_info dict with the id/color information for each child
    # Assumes that tree has
    annotation_info = {}
    if names:
        for name in names:
            annotation_info[name] = find_family(tree, name, tree_info)
    else:
        annotation_info[None] = None

    return annotation_info


# Load a VesselVio annotation JSON file
def load_annotation_file(file):
    with open(file) as f:
        annotation_data = json.load(f)["VesselVio Annotations"]
    return annotation_data


########################
### ROI Segmentation ###
########################
@njit(parallel=True, nogil=True, cache=True)
def segment_volume(labeled_volume, mins, maxes, segmentation_id):
    """Given a labeled volume and ROI bounds, segment the loaded id.
    labeled_volume: np.uint8 volume containing labeled regions
    mins: 3 element array containing ZYX bound minima
    maxes: 3 element array containing ZYX bound maxima
    segmentation_id: integer-id of the volume to segment

    returns: bounded and segmented volume
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


#####################
### ID Processing ###
#####################
# Convert the Annotation Processing JSON ids into an array of ids
# This is mainly because numba can't take lists or sets as input variables,
# and sending in tuples was throwing too many errors during set creation.
def prep_id_array(ROI_dict):
    """Given an ROI_dict (Annotation Processing export) containing ROI information,
    export an array containing the id information for each region in the order of appearance.
    The array contains zeros, but these will be removed during set creation.
    """
    ROIs = [ROI_dict[key]["ids"] for key in ROI_dict.keys()]

    ### REMOVE BEFORE FLIGHT ###
    ### REMOVE BEFORE FLIGHT ###
    # for ROI in ROIs:
    #     ROI += [r * -1 for r in ROI]
    ### REMOVE BEFORE FLIGHT ###
    ### REMOVE BEFORE FLIGHT ###

    max_len = 0
    for ROI in ROIs:  # Find maximum length of ROI ids
        max_len = len(ROI) if len(ROI) > max_len else max_len

    # Convert into array, fill with ROI ids, leaving 0's behind rest
    id_array = np.zeros([len(ROIs), max_len + 1])  # Make sure a zero is in every set
    for i, ROI in enumerate(ROIs):
        id_array[i, : len(ROI)] = ROI
    return id_array


@njit(cache=True)
def prep_id_annotation(id_array):
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


######################
### RGB Processing ###
######################
def RGB_check(annotation_data):
    """Given an annotation_data dict (Annotation Processing export),
    check to see whether there are duplicate colors among the regions.
    """
    hexes = [annotation_data[key]["colors"] for key in annotation_data.keys()]
    hex_set = []
    duplicates = False
    for ROI_hexes in hexes:
        for ROI_hex in ROI_hexes:
            if ROI_hex not in hex_set:
                hex_set.extend(ROI_hex)
            else:
                duplicates = True
        if duplicates:
            break
    return duplicates


@njit(fastmath=True, cache=True)
def hash_RGB_array(RGB, image=True):
    """Hash an (3, n, n) dimensional RGB np.array"""
    RGB = RGB.astype(np.float64)
    hash_1 = np.array((321.2, 143.4, 245.4))
    hash_2 = np.array((56.3, 33.2, 91.9))

    if not image:
        hash_1 = np.flip(hash_1)  # cv2.imread loads GRB
        hash_2 = np.flip(hash_2)
        RGB *= 255
    else:
        RGB = RGB  # cv2.imread loads as 255 RGB

    RGB = RGB * hash_1
    RGB = RGB / hash_2
    hashed = np.sum(RGB, axis=-1)
    return hashed


def prep_RGB_array(ROI_dict):
    """Given an ROI_dict (Annotation Processing export),
    hash the RGB values to create an array that contains the hashed_RGB labels for each region.
    The array contains zeros, but these will be removed during set creation.
    """
    hexes = [ROI_dict[key]["colors"] for key in ROI_dict.keys()]
    max_len = 0
    for hex_ids in hexes:
        max_len = len(hex_ids) if len(hex_ids) > max_len else max_len

    RGB_hashes = np.zeros([len(hexes), max_len + 1], dtype=np.float64)
    for i, hex_ids in enumerate(hexes):
        hashed_RGBs = np.zeros(max_len + 1)
        for j, hex_id in enumerate(hex_ids):
            RGB = np.asarray(helpers.hex_to_rgb(hex_id))
            hashed_RGBs[j] = hash_RGB_array(RGB, image=False)
        RGB_hashes[i] = hashed_RGBs
    return RGB_hashes


@njit(cache=True)
def prep_RGB_annotation(RGB_hashes):
    """Given an RGB_hash array, create a key set,
    dict with hash keys that point to items that contain corresponding index,
    and ROI_volume/volume update arrays"""
    RGB_dict = dict()
    for n in range(RGB_hashes.shape[0]):
        for RGB_id in range(RGB_hashes.shape[1]):
            if not RGB_hashes[n, RGB_id]:
                break  # End of the hashes
            RGB_dict[RGB_hashes[n, RGB_id]] = n

    RGB_keys = set(RGB_hashes.flatten())
    RGB_keys.remove(0)

    ROI_volumes = np.zeros(RGB_hashes.shape[0])
    volume_updates = np.identity(RGB_hashes.shape[0])

    return RGB_dict, RGB_keys, ROI_volumes, volume_updates


######################
### Slice Labeling ###
######################
@njit(cache=True)
def update_bounds(mins, maxes, z, y, x, indx):
    if z < mins[indx, 0]:
        mins[indx, 0] = z
    elif z > maxes[indx, 0]:
        maxes[indx, 0] = z
    if y < mins[indx, 1]:
        mins[indx, 1] = y
    elif y > maxes[indx, 1]:
        maxes[indx, 1] = y
    if x < mins[indx, 2]:
        mins[indx, 2] = x
    elif x > maxes[indx, 2]:
        maxes[indx, 2] = x
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
def RGB_labeling_input(volume, annotation_folder, RGB_array, verbose=False):
    # Load the images from the RGB annotation folder
    annotation_images = ImProc.dir_files(annotation_folder)

    if not ImProc.RGB_dim_check(annotation_images, volume.shape, verbose=verbose):
        return None, None, None, None

    # Prepare all of the necessary items
    RGB_dict, RGB_keys, ROI_volumes, volume_updates = prep_RGB_annotation(RGB_array)
    slice_volumes = ROI_volumes.copy()

    # Convert RGB_keys back into np.array
    RGB_keys = np.asarray(list(RGB_keys))

    mins = np.ones((RGB_array.shape[0], 3), dtype=np.int_) * np.array(volume.shape)
    maxes = np.zeros((RGB_array.shape[0], 3), dtype=np.int_)

    for i, file in enumerate(annotation_images):
        t = pf()
        image = cv2.imread(file)
        RGB_hash = hash_RGB_array(image)
        slice_labeling(
            volume,
            RGB_hash,
            slice_volumes,
            volume_updates,
            RGB_dict,
            RGB_keys,
            mins,
            maxes,
            i,
        )
        ROI_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
                flush=True,
            )

    return volume, ROI_volumes, mins, maxes


###########################
### ID Volume Labeling ####
###########################
# For images that have dtype incompatible with numba
def nn_id_labeling(volume, a_memmap, id_array, verbose=False):
    # Prepare all of the necessary items
    id_dict, id_keys, ROI_volumes, volume_updates = prep_id_annotation(id_array)
    slice_volumes = ROI_volumes.copy()

    # Convert id_keys back into np.array
    id_keys = np.asarray(list(id_keys))

    mins = np.ones((id_array.shape[0], 3), dtype=np.int_) * np.array(volume.shape)
    maxes = np.zeros((id_array.shape[0], 3), dtype=np.int_)

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
            mins,
            maxes,
            i,
        )
        ROI_volumes += slice_volumes
        slice_volumes *= 0

        if verbose:
            print(
                f"Slice {i+1}/{volume.shape[0]} segmented in {pf() - t:0.2f} seconds.",
                end="\r",
            )

    return volume, ROI_volumes, mins, maxes


### Numba dtype compatible segmentation
@njit(parallel=True, nogil=True, cache=True)
def numba_id_labeling(vprox, a_volume, id_array):
    id_dict, id_keys, ROI_volumes, volume_updates = prep_id_annotation(id_array)

    mins = np.ones((id_array.shape[0], 3), dtype=np.int_) * np.array(vprox.shape)
    maxes = np.zeros((id_array.shape[0], 3), dtype=np.int_)

    for z in prange(a_volume.shape[0]):
        for y in range(a_volume.shape[1]):
            for x in range(a_volume.shape[2]):
                p = a_volume[z, y, x]
                if p and p in id_keys:
                    ROI_id = id_dict[p]
                    ROI_volumes += volume_updates[ROI_id]
                    if vprox[z, y, x]:
                        vprox[z, y, x] = ROI_id + 1
                        update_bounds(mins, maxes, z, y, x, id_dict[p])
                elif vprox[z, y, x]:
                    vprox[z, y, x] = 0
    maxes = maxes + 1
    return vprox, ROI_volumes, mins, maxes


# Label the volume with id-based annotations
def id_labeling_input(volume, annotation_file, id_array, verbose=False):
    # Load a memmap of the annotation file
    annotation_memmap = ImProc.load_nii_volume(annotation_file)

    # # Make sure volume and annotation are of same shape.
    if not ImProc.id_dim_check(annotation_memmap, volume.shape, verbose=verbose):
        return None, None, None, None

    # Check to see that the dtype is appropriate for numba
    numba_seg = ImProc.dtype_check(annotation_memmap)

    if numba_seg:
        labeled_volume, ROI_volumes, mins, maxes = numba_id_labeling(
            volume, annotation_memmap, id_array
        )
    else:
        labeled_volume, ROI_volumes, mins, maxes = nn_id_labeling(
            volume, annotation_memmap, id_array, verbose=verbose
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


###############
### Testing ###
###############
if __name__ == "__main__":
    # !!! #
    # If labeling from __main__, this file needs to be copied to
    # Parent dir of /Library folder, i.e., with the VesselVio.py file.
    from os import getcwd as get_cwd

    from library import image_processing as ImProc

    annotation_data = load_annotation_file("")
    print("Regions:", len(annotation_data.keys()))

    ### NII Testing
    # volume = ImProc.load_nii_volume('')
    # annotation = ""
    # id_array = prep_id_array(annotation_data)
    # volume, ROI_volumes, mins, maxes = id_segmentation_input(volume, annotation, id_array, verbose=True)

    ### RGB Testing
    volume = ImProc.load_nii_volume("")
    annotation_folder = ""
    RGB_array = prep_RGB_array(annotation_data)
    volume, ROI_volumes, mins, maxes = RGB_labeling_input(
        volume, annotation_folder, RGB_array, verbose=True
    )

else:
    from library import image_processing as ImProc
    from library.helpers import get_cwd
