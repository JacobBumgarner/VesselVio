
"""
The Euclidian Distance Transformation (EDT) algorithm equation calculates point distance between the centers of voxels/pixels.
Because of this, radius of vessel segments is overestimated, as the true 'edge' of the vessel exists at the border of the nearest black voxel, not the center. 

This program calculates the EDT to the edge of face-connected voxels rather than their centers. Edge and corner voxel EDTS are computed normally.

The program then generates an array of a predetermined size that can be accessed to rapidly provide corrected distances for our centerlines.

Copyright © 2021, Jacob Bumgarner
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright © 2021 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import os

import numpy as np
from math import sqrt
from numba import njit, prange

######################
### LUT Generation ###
######################
@njit(parallel=True, cache=True)
def table_generation(resolution=np.array([1,1,1]), size=150):
    # size = min(500, ceil(max_radius / np.min(resolution))) # Hard code size limit at 500 mb
    LUT = np.zeros((size, size, size))
    
    correction = resolution / 2

    for z in prange(size):
        for y in range(size):
            for x in range(size):
                coords = np.array([z,y,x])
                coords = coords * resolution
                non_zeros = np.count_nonzero(coords)
                
                # To correct for radii lines along 1D planes, remove half of resolution length.
                if non_zeros == 1:
                    # Two of the values will be 0 and therefore negative after correction.
                    corrected = coords - correction
                    # Remove to isolate true correction.
                    corrected = corrected[corrected > 0][0]
                    LUT[z, y, x] = corrected
                    
                else:
                    a = np.sum(coords**2)
                    LUT[z, y, x] = sqrt(a)
    return LUT

###################
### LUT Loading ###
###################
# Load the corrections table.    
def load_corrections(resolution=np.array([1,1,1]),
                     new_build=False, Visualize=False, size=150, verbose=False):

    # Load the correct LUT: resolution(analysis) or basis(visualization) units.
    wd = get_cwd() # Find wd
    if not Visualize:
        rc_path = os.path.join(wd, 'Library/Volumes/Radii_Corrections.npy')
    else:
        rc_path = os.path.join(wd, 'Library/Volumes/Vis_Radii_Corrections.npy')
    
    # Build function
    def build(resolution):
        if verbose:
            print ("Generating new correction table.")
        _ = table_generation(size=3) # Make sure the fxn is compiled
        LUT = table_generation(resolution, size)
        np.save(rc_path, LUT) 
        
        if verbose:
            print ("Table generation complete.")
        return LUT
    
    if new_build or not os.path.exists(rc_path):
        if verbose:
            print ("New build initiated.")
        LUT = build(resolution)

    else:
        try:
            # Try loading the file.
            LUT = np.load(rc_path)
            rebuild = False
            
            # Make sure dimensions are also correct.
            if (resolution[0]/2 != LUT[1,0,0] or
                    resolution[1]/2 != LUT[0,1,0] or
                    resolution[2]/2 != LUT[0,0,1]): 
                rebuild = True
            if rebuild:
                LUT = build(resolution)
                        
        except:
            LUT = build(resolution)  
                                  
    return LUT


######################
### Terminal Build ###
######################
if __name__ == "__main__":
    from os import getcwd as get_cwd # Can't load helpers from Library level
    resolution = 1.0 # Either a float or an array.
    load_corrections(resolution, new_build=True, verbose=True, Visualize=False)
    load_corrections(resolution, new_build=True, verbose=True, Visualize=True)
else:
    from Library.helpers import get_cwd
