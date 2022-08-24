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
from skimage.io import imread


@njit(parallel=True, nogil=True, cache=True)
def segment_roi(
    labeled_volume: np.ndarray,
    minima: np.ndarray,
    maxima: np.ndarray,
    segmentation_id: int,
) -> np.ndarray:
    """Return a segmented region of interest from a labeled vasculature volume.

    Parameters
    ----------
    labeled_volume : np.ndarray
        The labeled vasculature volume.
    minima : np.ndarray
        The minima of the ROI in [z, y, x] format.
    maxima : np.ndarray
        The maxima of the ROI in [z, y, x] format.
    segmentation_id : int
        The integer-based ID of the ROI that will be segmented from the labeled volume.

    Returns
    -------
    volume : np.ndarray
        The segmented ROI from the input volume.
    """
    # Isolate the segmented region from the main volume
    volume = labeled_volume[
        minima[0] : maxima[0] + 1, minima[1] : maxima[1] + 1, minima[2] : maxima[2] + 1
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


def roi_segmentation_input(
    minima: np.ndarray,
    maxima: np.ndarray,
    segmentation_id: int,
    labeled_volume_fname: str = None,
    verbose: bool = False,
) -> np.ndarray:
    """Input function used to segment an ROI from a cached labeled volume.

    Parameters
    ----------
    minima : np.ndarray
        The minima of the ROI to be segmented in [z, y, x] format.
    maxima : np.ndarray
        The maxima of the ROI to be segmented in [z, y, x] format.
    segmentation_id : int
        The integer-based ID of the ROI that will be segmented from the labeled volume.
    labeled_volume_fname : str, optional
        The filepath to the cached labeled volume, by default None
    verbose : bool, optional
        Print the status of the ROI segmentation, by default False

    Returns
    -------
    volume : np.ndarray
        The segmented region of interest.

    """
    if verbose:
        t = pf()
        print("Segmenting ROI from volume...", end="\r")

    if not labeled_volume_fname:
        labeled_volume = ImProc.load_labeled_volume_cache()
    else:
        labeled_volume = imread(labeled_volume_fname)

    volume = segment_roi(labeled_volume, minima, maxima, segmentation_id)
    del labeled_volume

    if verbose:
        print(f"ROI segmented in {pf() - t:0.2f} seconds.")

    return volume
