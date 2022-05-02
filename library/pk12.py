"""
A numba-based implementation of the Palagyi and Kuba 1999 12-subiteration thinning algorithm.
https://www.sciencedirect.com/science/article/pii/S1077316999904987
This code was HEAVILY inspired and sourced from Christoph Kirst's TubeMap skeletonization code:
https://github.com/ChristophKirst/ClearMap2
Ultimately, VesselVio does not implement the PK12 algorithm.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os
import sys
from time import perf_counter as pf

import numpy as np
from numba import njit, prange

####################
### Neighborhood ###
####################
n6 = np.array(
    [
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
    ],
    dtype=bool,
)
"""6-Neighborhood excluding center"""


######################
### LUT Generation ###
######################

# Palagyi matching templaes
def match(cube):
    # T1
    T1 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and (
            cube[0, 0, 0]
            or cube[1, 0, 0]
            or cube[2, 0, 0]
            or cube[0, 1, 0]
            or cube[2, 1, 0]
            or cube[0, 2, 0]
            or cube[1, 2, 0]
            or cube[2, 2, 0]
            or cube[0, 0, 1]
            or cube[1, 0, 1]
            or cube[2, 0, 1]
            or cube[0, 1, 1]
            or cube[2, 1, 1]
            or cube[0, 2, 1]
            or cube[1, 2, 1]
            or cube[2, 2, 1]
        )
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[0, 1, 2])
        and (not cube[1, 1, 2])
        and (not cube[2, 1, 2])
        and (not cube[0, 2, 2])
        and (not cube[1, 2, 2])
        and (not cube[2, 2, 2])
    )
    if T1:
        return True

    # T2
    T2 = (
        cube[1, 1, 1]
        and cube[1, 2, 1]
        and (
            cube[0, 1, 0]
            or cube[1, 1, 0]
            or cube[2, 1, 0]
            or cube[0, 2, 0]
            or cube[1, 2, 0]
            or cube[2, 2, 0]
            or cube[0, 1, 1]
            or cube[2, 1, 1]
            or cube[0, 2, 1]
            or cube[2, 2, 1]
            or cube[0, 1, 2]
            or cube[1, 1, 2]
            or cube[2, 1, 2]
            or cube[0, 2, 2]
            or cube[1, 2, 2]
            or cube[2, 2, 2]
        )
        and (not cube[0, 0, 0])
        and (not cube[1, 0, 0])
        and (not cube[2, 0, 0])
        and (not cube[0, 0, 1])
        and (not cube[1, 0, 1])
        and (not cube[2, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
    )
    if T2:
        return True

    # T3
    T3 = (
        cube[1, 1, 1]
        and cube[1, 2, 0]
        and (
            cube[0, 1, 0]
            or cube[2, 1, 0]
            or cube[0, 2, 0]
            or cube[2, 2, 0]
            or cube[0, 1, 1]
            or cube[2, 1, 1]
            or cube[0, 2, 1]
            or cube[2, 2, 1]
        )
        and (not cube[0, 0, 0])
        and (not cube[1, 0, 0])
        and (not cube[2, 0, 0])
        and (not cube[0, 0, 1])
        and (not cube[1, 0, 1])
        and (not cube[2, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[0, 1, 2])
        and (not cube[1, 1, 2])
        and (not cube[2, 1, 2])
        and (not cube[0, 2, 2])
        and (not cube[1, 2, 2])
        and (not cube[2, 2, 2])
    )
    if T3:
        return True

    # T4
    T4 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and cube[1, 2, 1]
        and ((not cube[0, 0, 1]) or (not cube[0, 1, 2]))
        and ((not cube[2, 0, 1]) or (not cube[2, 1, 2]))
        and (not cube[1, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T4:
        return True

    # T5
    T5 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and cube[1, 2, 1]
        and cube[2, 0, 2]
        and ((not cube[0, 0, 1]) or (not cube[0, 1, 2]))
        and (
            ((not cube[2, 0, 1]) and cube[2, 1, 2])
            or (cube[2, 0, 1] and (not cube[2, 1, 2]))
        )
        and (not cube[1, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T5:
        return True

    # T6
    T6 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and cube[1, 2, 1]
        and cube[0, 0, 2]
        and ((not cube[2, 0, 1]) or (not cube[2, 1, 2]))
        and (
            ((not cube[0, 0, 1]) and cube[0, 1, 2])
            or (cube[0, 0, 1] and (not cube[0, 1, 2]))
        )
        and (not cube[1, 0, 1])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T6:
        return True

    # T7
    T7 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and cube[2, 1, 1]
        and cube[1, 2, 1]
        and ((not cube[0, 0, 1]) or (not cube[0, 1, 2]))
        and (not cube[1, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T7:
        return True

    # T8
    T8 = (
        cube[1, 1, 0]
        and cube[0, 1, 1]
        and cube[1, 1, 1]
        and cube[1, 2, 1]
        and ((not cube[2, 0, 1]) or (not cube[2, 1, 2]))
        and (not cube[1, 0, 1])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T8:
        return True

    # T9
    T9 = (
        cube[1, 1, 0]
        and cube[1, 1, 1]
        and cube[2, 1, 1]
        and cube[0, 0, 2]
        and cube[1, 2, 1]
        and (
            ((not cube[0, 0, 1]) and cube[0, 1, 2])
            or (cube[0, 0, 1] and (not cube[0, 1, 2]))
        )
        and (not cube[1, 0, 1])
        and (not cube[1, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T9:
        return True

    # T10
    T10 = (
        cube[1, 1, 0]
        and cube[0, 1, 1]
        and cube[1, 1, 1]
        and cube[2, 0, 2]
        and cube[1, 2, 1]
        and (
            ((not cube[2, 0, 1]) and cube[2, 1, 2])
            or (cube[2, 0, 1] and (not cube[2, 1, 2]))
        )
        and (not cube[1, 0, 1])
        and (not cube[1, 0, 2])
        and (not cube[1, 1, 2])
    )
    if T10:
        return True

    # T11
    T11 = (
        cube[2, 1, 0]
        and cube[1, 1, 1]
        and cube[1, 2, 0]
        and (not cube[0, 0, 0])
        and (not cube[1, 0, 0])
        and (not cube[0, 0, 1])
        and (not cube[1, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[0, 1, 2])
        and (not cube[1, 1, 2])
        and (not cube[2, 1, 2])
        and (not cube[0, 2, 2])
        and (not cube[1, 2, 2])
        and (not cube[2, 2, 2])
    )
    if T11:
        return True

    # T12
    T12 = (
        cube[0, 1, 0]
        and cube[1, 2, 0]
        and cube[1, 1, 1]
        and (not cube[1, 0, 0])
        and (not cube[2, 0, 0])
        and (not cube[1, 0, 1])
        and (not cube[2, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[0, 1, 2])
        and (not cube[1, 1, 2])
        and (not cube[2, 1, 2])
        and (not cube[0, 2, 2])
        and (not cube[1, 2, 2])
        and (not cube[2, 2, 2])
    )
    if T12:
        return True

    # T13
    T13 = (
        cube[1, 2, 0]
        and cube[1, 1, 1]
        and cube[2, 2, 1]
        and (not cube[0, 0, 0])
        and (not cube[1, 0, 0])
        and (not cube[2, 0, 0])
        and (not cube[0, 0, 1])
        and (not cube[1, 0, 1])
        and (not cube[2, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[0, 1, 2])
        and (not cube[1, 1, 2])
        and (not cube[0, 2, 2])
        and (not cube[1, 2, 2])
    )
    if T13:
        return True

    # T14
    T14 = (
        cube[1, 2, 0]
        and cube[1, 1, 1]
        and cube[0, 2, 1]
        and (not cube[0, 0, 0])
        and (not cube[1, 0, 0])
        and (not cube[2, 0, 0])
        and (not cube[0, 0, 1])
        and (not cube[1, 0, 1])
        and (not cube[2, 0, 1])
        and (not cube[0, 0, 2])
        and (not cube[1, 0, 2])
        and (not cube[2, 0, 2])
        and (not cube[1, 1, 2])
        and (not cube[2, 1, 2])
        and (not cube[1, 2, 2])
        and (not cube[2, 2, 2])
    )
    if T14:
        return True

    return False


def build_index_cube(indx):
    cube = np.zeros([3, 3, 3], dtype=bool)
    e = 0
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if [x, y, z] == [1, 1, 1]:
                    cube[x, y, z] = True
                else:
                    cube[x, y, z] = (indx >> e) & 0x01
                    e += 1
    return match(cube)


def build_LUT():
    LUT = np.zeros(2**10, dtype=bool)
    for index in range(2**10):
        LUT[index] = build_index_cube(index)
    return LUT


def load_LUT():
    try:
        # Determines if we're opening the file from a pyinstaller exec.
        wd = sys._MEIPASS
    except AttributeError:
        wd = os.getcwd()
    file = os.path.join(wd, "library/volumes/PK12.npy")
    if not os.path.exists(file):
        LUT = build_LUT()
        np.save(file, LUT)
    else:
        LUT = np.load(file)
    return LUT


##################
### Base2 Cube ###
##################
def rotate(cube, axis=2, steps=0):
    cube = cube.copy()

    if axis == 0:
        if steps == 1:
            return cube[:, ::-1, :].swapaxes(1, 2)
        elif steps == 2:  # rotate 180 degrees around x
            return cube[:, ::-1, ::-1]
        elif steps == 3:  # rotate 270 degrees around x
            return cube.swapaxes(1, 2)[:, ::-1, :]

    elif axis == 1:
        if steps == 1:
            return cube[:, :, ::-1].swapaxes(2, 0)
        elif steps == 2:  # rotate 180 degrees around x
            return cube[::-1, :, ::-1]
        elif steps == 3:  # rotate 270 degrees around x
            return cube.swapaxes(2, 0)[:, :, ::-1]

    if axis == 2:  # z axis rotation
        if steps == 1:
            return cube[::-1, :, :].swapaxes(0, 1)
        elif steps == 2:  # rotate 180 degrees around z
            return cube[::-1, ::-1, :]
        elif steps == 3:  # rotate 270 degrees around z
            return cube.swapaxes(0, 1)[::-1, :, :]


# Cube rotations for the border point assessment
# Rotations are defined in Palagyi 1999
def generate_templates(cube):
    rotUS = cube.copy()
    rotUW = rotate(cube, axis=2, steps=1)
    rotUN = rotate(cube, axis=2, steps=2)
    rotUE = rotate(cube, axis=2, steps=3)

    rotDS = rotate(cube, axis=1, steps=2)
    rotDW = rotate(rotDS, axis=2, steps=1)
    rotDN = rotate(rotDS, axis=2, steps=2)
    rotDE = rotate(rotDS, axis=2, steps=3)

    rotSW = rotate(cube, axis=1, steps=1)
    rotSE = rotate(cube, axis=1, steps=3)

    rotNW = rotate(rotUN, axis=1, steps=1)
    rotNE = rotate(rotUN, axis=1, steps=3)

    return [
        rotUS,
        rotNE,
        rotDW,
        rotSE,
        rotUW,
        rotDN,
        rotSW,
        rotUN,
        rotDE,
        rotNW,
        rotUE,
        rotDS,
    ]


# Construct a base2 cube to serve as a binary product for our LUT
def build_base2_cube():
    cube = np.zeros([3, 3, 3])
    e = 0
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if [x, y, z] == [1, 1, 1]:
                    cube[x, y, z] = False
                else:
                    cube[x, y, z] = 2**e
                    e += 1
    return cube


def load_templates():
    cube = build_base2_cube()
    rotations = generate_templates(cube)
    return rotations


"""
The following skeletonization algorithm implementation would not have been possible without code from Christoph Kirst/TubeMap 2.0.

Kirst's implementation of the Palagyi 1999 skeletonization algorithm uses an ingenenious technique to examine local volume point topology. In essence, a LUT table of the 2**26 possible 3x3x3 cubes is created, matched with the Palagyi templates, and used as a reference to determine the removal status of border points.

Kirst creates the tables using right-shifted ints & 0x01 in range(2**26) to create the candidate cubes, and then uses a rotated base cube summed with local 3x3x3 topology to determine whether the point should be removed. Awesome programming.

Unfortunately, this algorithm produces skeletons that are not as well-structured as the Lee '94 algorithm, so it wasn't used for the program. However, it has been left for potential future implementations.
"""


###########
### JIT ###
###########
@njit()
def nonzero_JIT(volume):
    return np.nonzero(volume)


def identify_nonzero(volume):
    return np.asarray(nonzero_JIT(volume)).T


###########################
### Skeleton processing ###
###########################
@njit(parallel=True)
def convolve_3d_points(volume, kernel, points, filter):
    """Convolves binary data with a specified kernel at specific points only."""

    ki, kj, kk = kernel.shape
    npoints = points.shape[0]
    for n in prange(npoints):
        x, y, z = points[n]
        filter[n] += np.sum(
            volume[x - 1 : x + 2, y - 1 : y + 2, z - 1 : z + 2] * kernel
        )
    return filter


def convolve_input(volume, kernel, points):
    npts = points.shape[0]
    filter = np.zeros(npts, np.int_)
    filter = convolve_3d_points(volume, kernel, points, filter)
    return filter


def PK12_skeletonize(volume, verbose=False):
    volume = volume.copy()
    templates = load_templates()
    PK12_LUT = load_LUT()
    points = identify_nonzero(volume)

    while True:
        t = pf()
        border = convolve_input(volume, n6, points) < 6
        border_points = points[border]
        border_ids = np.nonzero(border)[0]
        keep = np.ones(border.shape[0], bool)

        removal_count = 0
        # examine = np.ones(border_points.shape[0], bool)
        for i in range(12):
            point_fate = PK12_LUT[convolve_input(volume, templates[i], border_points)]
            removals = border_points[point_fate]
            volume[removals[:, 0], removals[:, 1], removals[:, 2]] = 0

            keep[border_ids[point_fate]] = False
            removal_count += removals.shape[0]

        points = points[keep]

        if verbose:
            print(
                f"Removed {removal_count} points in {pf() - t:.2f} seconds.             ",
                end="\r",
            )
        if not removal_count:
            break
    if verbose:
        print("                              ", end="\r")
    return volume


###############
### Testing ###
###############
if __name__ == "__main__":
    volume = np.pad(np.ones([3, 3, 3]))
    skeleton = PK12_skeletonize(volume)
