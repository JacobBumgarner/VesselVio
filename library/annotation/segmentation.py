"""ROI segmentation functions."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from time import perf_counter as pf

import numpy as np

from library import image_processing as ImProc
from numba import njit, prange


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
