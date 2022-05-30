"""
Image loading and processing.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os
from pathlib import Path
from time import perf_counter as pf

import cv2
import nibabel
import numpy as np

from library import helpers
from skimage.io import imread

## Global min_resolution variable
min_resolution = 1


########################
#### Volume Loading ####
########################
## Returns a true binary (0,1) array from an image file when given the file name and directory.
def load_volume(file, verbose=False):
    t1 = pf()

    # Only use .nii files for annotations, this is mainly due to loading speeds
    if helpers.get_ext(file) == ".nii":
        try:
            volume = load_nii_volume(file)
        except Exception as error:
            print(f"Could not load .nii file using nibabel: {error}")
            volume = skimage_load(file)
    else:
        volume = skimage_load(file)

    if volume is None or volume.ndim not in (2, 3):
        return None

    if verbose:
        print(f"Volume loaded in {pf() - t1:.2f} s.")

    return volume, volume.shape


# Load nifti files
def load_nii_volume(file):
    proxy = nibabel.load(file)
    data = proxy.dataobj.get_unscaled().transpose()
    if data.ndim == 4:
        data = data[0]
    return data


# Load an image volume using SITK, return None upon read failure
def skimage_load(file):
    try:
        volume = imread(file).astype(np.uint8)
    except Exception as error:
        print(f"Unable to read image file using skimage.io.imread: {error}")
        volume = None
    return volume


# Reshape 2D array to make it compatible with analysis pipeline
def reshape_2D(points, volume, verbose=False):
    if verbose:
        print("Re-constructing arrays...", end="\r")
    points = np.pad(points, ((0, 0), (1, 0)))
    zeros = np.zeros(volume.shape)  # Pad zeros onto back of array
    volume = np.stack([volume, zeros])
    image_shape = volume.shape
    return points, volume, image_shape


# Confirm that the volume was either loaded or segmented properly
def binary_check(volume: np.ndarray) -> bool:
    """Return a bool indicating if the loaded volume is binary or not.

    Takes a slice from the volume and checks to confirm that only two unique
    values are present.

    Parameters:
    volume : np.ndarray

    Returns:
    bool
        True if the spot check of the volume only return two unique values,
        False if more than two unique values were identified.
    """
    middle = int(volume.shape[0] / 2)
    unique = np.unique(volume[middle])

    return unique.shape[0] < 3


def segmentation_check(volume: np.ndarray) -> bool:
    """Return a bool indicating if volume has vessels after the segmentation.

    Some regions of interest may be present in the annotation, but there may
    be no corresponding vasculature in the datasets. This function checks to see
    if vessels are present.

    Parameters:
    volume : np.ndarray

    Returns:
    bool
        True if vessels are present, False if not.
    """
    if volume is None:
        return False
    elif not np.any(volume):
        return False
    return True


# Returns file size in bytes
def check_file_size(file):
    size = os.path.getsize(file)
    return size


# Check to see if the dtype of a loaded proxy image is compatible with Numba.
def dtype_check(volume_prox):
    numba_compatible = True
    # this is seems specific to ImageJ NIfTI export.
    if volume_prox.dtype == np.dtype(">f") or volume_prox.dtype == np.dtype(">i"):
        numba_compatible = False
    elif not (
        np.issubdtype(volume_prox.dtype, np.floating)
        or np.issubdtype(volume_prox.dtype, np.integer)
    ):
        numba_compatible = False
    return numba_compatible


def prep_numba_compatability(volume):
    if not dtype_check(volume):
        volume = np.asarray(volume, dtype=np.uint8)
    return volume


####################################
### Annotation Volume Processing ###
####################################
# Get the annotation slice. Some 3D nifti files are saved in 4D rather than 3D (e.g., FIJI output)
def get_annotation_slice(a_prox, i):
    a_slice = a_prox[i].astype(np.int_)
    return a_slice


# Dimension check for ID annotated volumes, returns False if dimensions don't match.
def id_dim_check(proxy_an, vshape, verbose=False):
    ashape = proxy_an.shape
    if ashape != vshape:
        if verbose:
            print("Annotation volume dimensions don't match dataset dimensions.")
        return False
    else:
        return True


# Dimension check for RGB annotated volumes, returns True if dimensions don't match.
def RGB_dim_check(files, vshape, verbose=False):
    ex_im = cv2.imread(files[0])
    ex_shape = ex_im[..., 0].shape
    if len(files) != vshape[0] or ex_shape[0] != vshape[1] or ex_shape[1] != vshape[2]:
        if verbose:
            print("Annotation volume dimensions don't match dataset dimensions.")
        return False
    else:
        return True


def cache_labeled_volume(
    labeled_volume: np.ndarray, cache_directory: str = None, verbose: bool = False
) -> None:
    """Save a copy of the labeled volume as an .npy file.

    Parameters:
    labeled_volume : np.ndarray

    cache_directory : str, optional
        The filepath to save the labeled volume. Default ``None``.

    verbose : bool, optional
        Default ``False``.
    """
    if verbose:
        t = pf()
        print("Saving cache of labeled volume...", end="\r")

    cache_path = helpers.get_volume_cache_path(cache_directory)
    np.save(cache_path, np.asarray(labeled_volume, dtype=np.uint8))

    if verbose:
        print(f"Labeled volume caching complete in {pf() - t:0.2f} seconds.")
    return


def load_labeled_volume_cache():
    labeled_cache = helpers.get_volume_cache_path()
    if os.path.exists(labeled_cache):
        labeled_volume = np.lib.format.open_memmap(labeled_cache, mode="r")
    else:
        labeled_volume = None
    return labeled_volume


def clear_labeled_cache():
    labeled_cache = helpers.get_volume_cache_path()
    if os.path.exists(labeled_cache):
        os.remove(labeled_cache)
    return


##########################
#### Image Processing ####
##########################
def prep_resolution(resolution):
    if not isinstance(resolution, list):
        resolution = np.repeat(resolution, 3)
    else:
        # Flip the resolution, as numpy first index will represent image depth
        resolution = np.flip(np.array(resolution))
    min_resolution = np.min(resolution)
    return resolution


# Get image files from a directory
# finds the first extension of the file in that dir
def dir_files(directory):
    extension = os.path.splitext(os.listdir(directory)[0])[1]
    files = sorted([str(file) for file in Path(directory).glob("*" + extension)])
    return files


def image_resizing(directory, output_size, ext):
    files = dir_files(directory, ext)

    for file in files:
        image = cv2.imread(file)
        image = cv2.resize(image, output_size, interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(file, image)
    return


# Get file name
def get_filename(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return filename
