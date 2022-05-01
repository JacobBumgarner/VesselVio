"""
Volume (np.ndarray) processing page: skeletonization input, radius calculations, volume bounding, etc.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from time import perf_counter as pf

import numpy as np

from library import lee94, radii_corrections as RadCor
from numba import njit, prange
from scipy.ndimage import label
from skimage.morphology import skeletonize_3d


#######################
### Volume Bounding ###
#######################
def volume_prep(volume):
    """IO for volume binarization/segmentation and volume bounding
    volume: np.ndarray or np.memmap
    """
    # Make sure that we're in c-order, was more important for flat
    # skeletonization, but it's 3D now so it's somewhat unnecessary
    volume = np.asarray(volume, dtype=np.uint8)
    if not volume.data.contiguous:
        volume = np.ascontiguousarray(volume)
    # 3D Processing
    if volume.ndim == 3:
        volume, minima = binarize_and_bound_3D(volume)

    # 2D Processing
    elif volume.ndim == 2:
        volume, minima = bound_2D(volume)

    return volume, minima


@njit(parallel=True, nogil=True, cache=True)
def binarize_and_bound_3D(volume):
    """
    A function that simultaneously serves to segment an integer
    from a volume as well as record the bounding box locations
    volume: A 3D np.array or np.memmap
    """
    mins = np.array(volume.shape, dtype=np.int_)
    maxes = np.zeros(3, dtype=np.int_)
    for z in prange(volume.shape[0]):
        for y in range(volume.shape[1]):
            for x in range(volume.shape[2]):
                p = volume[z, y, x]
                if p:
                    volume[z, y, x] = 1
                    if z < mins[0]:
                        mins[0] = z
                    elif z > maxes[0]:
                        maxes[0] = z
                    if y < mins[1]:
                        mins[1] = y
                    elif y > maxes[1]:
                        maxes[1] = y
                    if x < mins[2]:
                        mins[2] = x
                    elif x > maxes[2]:
                        maxes[2] = x

    volume = volume[
        mins[0] : maxes[0] + 1, mins[1] : maxes[1] + 1, mins[2] : maxes[2] + 1
    ]
    return volume, mins


# Bound and segment 2D volumes
def bound_2D(volume):
    """Binarize and bound 2 dimensional volumes"""
    volume = (volume > 0).astype(np.uint8)

    # To find minima and maxima, flatten the volume along 0th and 1st axes
    y = np.any(volume, axis=1)
    x = np.any(volume, axis=0)

    # Find the first/last occurnce of points along the flattened arrays
    ymin, ymax = np.argmax(y), volume.shape[0] - 1 - np.argmax(np.flip(y))
    xmin, xmax = np.argmax(x), volume.shape[1] - 1 - np.argmax(np.flip(x))

    # Bound and binarize the volume
    volume = volume[ymin : ymax + 1, xmin : xmax + 1]
    return volume, [0, ymin, xmin]


# Separate padding function for loading volumes during visualization
def pad_volume(volume):
    volume = np.pad(volume, 1)
    return volume


def absolute_points(points, minima):
    """The coordinates of the points are based on the bounded volume.
    To make sure that the coordinate points match the location of the points
    in the original volume space, we must add the bounding minima back to
    the point values. This function achieves that.

    Parameters
    ----------
    points : np.array with shape (n, 3)

    minima : np.array with shape (3,)

    Returns
    -------
    (n, 3) np.array
        Updated array that converts the bounded volume points back to
        the original image space.
    """
    abs_points = points + minima
    return abs_points.astype(np.int_)


#########################
### Segment Filtering ###
#########################
# Remove the filtered segments from the volume for visualization purposes.
def filter_volume(volume, keep_coords):
    if keep_coords.shape[0]:
        labeled = label_volume(volume)
        keep_ids = labeled[keep_coords[:, 0], keep_coords[:, 1], keep_coords[:, 2]]
        volume = filter_segments(labeled, keep_ids)

    return volume


# Label our dataset. Potentially replace with flood filling one day
def label_volume(volume):
    struct = np.ones((3, 3, 3), dtype=int)
    labeled, _ = label(volume, structure=struct)
    del volume
    return labeled


# Filters labeled volumes from the volume.
@njit(parallel=True, cache=True)
def filter_segments(labeled, keep_ids):
    """Remove specific ids from a labeled np.3darray
    labeled: a 3D np.array or np.memmap that is labeled with specific ids
    remove_ids: a 1D np.array of values that will be removed from the volume
    returns the labeled volume with all elements of the remove_ids converted
    to zero.
    """
    keep_ids = set(keep_ids)
    for z in prange(labeled.shape[0]):
        for y in range(labeled.shape[1]):
            for x in range(labeled.shape[2]):
                p = labeled[z, y, x]
                if p and p not in keep_ids:
                    labeled[z, y, x] = 0
    return labeled > 0


###########################
### Radius Calculations ###
###########################
# Loading dock for our volume radii corrections
def radii_calc_input(volume, points, resolution, gen_vis_radii=False, verbose=False):
    if verbose:
        t = pf()
        print("Calculating radii...", end="\r")

    # Calculate radii for feature analysis
    # Load the mEDT_LUT
    LUT = RadCor.load_corrections(resolution, verbose=verbose)
    skeleton_radii = radii_calc(volume, points, LUT)
    del LUT  # Just for sanity

    # If visualizing, rerun to find unit radii of dataset.
    vis_radii = None
    if gen_vis_radii:
        # Load the mEDT_LUT using basis units.
        LUT = RadCor.load_corrections(Visualize=True, verbose=verbose)
        vis_radii = radii_calc(volume, points, LUT)
        del LUT  # Just for sanity

    if verbose:
        print(f"Radii identified in {pf() - t:0.2f} seconds.")

    return skeleton_radii, vis_radii


def radii_calc(volume, points, LUT):
    if volume.ndim == 3:
        skeleton_radii = calculate_3Dradii(volume, points, LUT)

    elif volume.ndim == 2:
        skeleton_radii = calculate_2Dradii(volume, points, LUT)

    return skeleton_radii.tolist()


# This function calculates the corrected radii for each centerline point.
# It is functionally the same as an EDT, but it calculates the distance
# to the edge (rather than the center) of the nearest non-vessel voxel.
# Essentially, it searches around a point for four zero neighbors
# and runs them through the mEDT_LUT.
@njit(parallel=True, cache=True)
def calculate_3Dradii(volume, points, LUT):
    volume = volume
    points = points
    LUT = LUT

    # Have to keep this as a list for igraph
    skeleton_radii = np.zeros(points.shape[0])
    empty = np.zeros(150)

    # Iterate through each skeleton point to find
    # local zeros for radius identifications
    for p in prange(points.shape[0]):
        for i in range(empty.shape[0]):
            point = points[p]
            mins = point - i
            # mins = point * -1 ### lots of weird Numba finagling here...
            mins[mins < 0] = 0  # Find the minimum onset of the search box
            zeros = np.vstack(
                np.where(
                    volume[
                        mins[0] : point[0] + i + 1,
                        mins[1] : point[1] + i + 1,
                        mins[2] : point[2] + i + 1,
                    ]
                    == 0
                )
            ).T

            # If there's more than 4 zeros, find radii for average.
            if zeros.shape[0] > 3:
                point_radii = np.zeros(zeros.shape[0])
                zeros = np.abs((zeros + mins) - point)
                for j in range(zeros.shape[0]):
                    point_radii[j] = LUT[zeros[j, 0], zeros[j, 1], zeros[j, 2]]

                point_radii = np.sort(point_radii)
                radius = np.sum(point_radii[:4]) / 4
                skeleton_radii[p] = radius
                break

            # Arbitrary number to cutoff and prevent deadlock.
            # Hard-coding this could be problematic.
            if i == 149:
                skeleton_radii[p] = LUT[-1, -1, -1]
                break

    return skeleton_radii


# Identical copy of 3D functino, save for the z-dimension. See 3D for notes.
@njit(parallel=True, cache=True, nogil=True)
def calculate_2Dradii(volume, points, LUT):
    volume = volume
    points = points

    skeleton_radii = np.zeros(points.shape[0])
    empty = np.zeros(150)
    for p in prange(points.shape[0]):
        for i in range(empty.shape[0]):
            point = points[p]
            mins = point - i
            mins[mins < 0] = 0
            zeros = np.argwhere(
                volume[mins[0] : point[0] + i + 1, mins[1] : point[1] + i + 1] == 0
            )

            if zeros.shape[0] > 3:
                point_radii = np.zeros(zeros.shape[0])
                zeros = np.abs((zeros + mins) - point)
                for j in prange(zeros.shape[0]):
                    # LUT is 3d but we can just use the first slice.
                    point_radii[j] = LUT[0, zeros[j, 0], zeros[j, 1]]

                point_radii = np.sort(point_radii)
                radius = np.sum(point_radii[:4]) / 4
                skeleton_radii[p] = radius
                break

            # Arbitrary number to cutoff and prevent deadlock.
            # Hard-coding this could be problematic.
            if i == 149:
                skeleton_radii[p] = LUT[0, -1, -1]
                break

    return skeleton_radii


#######################
### Skeletonization ###
#######################
@njit(cache=True)
def find_centerlines(skeleton):
    points = np.vstack(np.nonzero(skeleton)).T
    return points.astype(np.int_)


def skeletonize(volume, verbose=False):
    if verbose:
        t = pf()
        print("Skeletonizing...", end="\r")

    # skeleton = skeletonize_3d(volume)
    if volume.ndim == 2:
        # Didn't configure my implementation for 2D datasets.
        skeleton = skeletonize_3d(volume)
    else:
        skeleton = np.ascontiguousarray(volume.copy())
        skeleton = lee94.skeletonize(skeleton, verbose=verbose)

    # Rearrange point array to (n,3) or (n,2).
    points = find_centerlines(skeleton)

    if verbose:
        print(f"Skeletonization completed in {pf() - t:0.2f} seconds.")

    return points
