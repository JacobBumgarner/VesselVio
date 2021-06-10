#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 15:37:05 2021

The Euclidian Distance Transformation algorithm equation calculates point distance.
Because of this, the radius of a vessel segment is overestimated, as the true 'edge'
     of the vessel exists at the border of the nearest black voxel, not the center. 

This short program calculates the EDT to the edge of face-connected voxels rather than their centers. Corner edts are calculated normally.

The program then generates an array of a predetermined size that can be accessed to provide rapidly provide corrected distances for our centerlines.

Author - Jacob R. Bumgarner
"""

import numpy as np
from math import asin, cos, sqrt
from numba import njit, prange
import time
import sys, os

@njit(parallel=True, fastmath=True)
def table_generation(resolution, max_radius, save=True):
    size = int(max_radius / resolution)
    LUT = np.zeros((size, size, size), dtype=np.float32)
    
    for z in prange(size):
        for y in range(size):
            for x in range(size):
                coords = [z,y,x]
                coords.sort()
                zeros = coords.count(0)
                
                # Corrections for lines along 1D planes are easy - remove half a voxel.
                if zeros == 2:
                    corrected = coords[2] - 0.5
                    corrected = sqrt(z**2 + y**2 + x**2)
                    LUT[z, y, x] = corrected
                    
                else:
                    # a = np.linalg.norm(coords)
                    a = sqrt(z**2 + y**2 + x**2)
                    LUT[z, y, x] = a
                    
                # Calculations to the edge of nearest voxel. this resulted in vessels being too small.
                # Corrections along 2D/3D planes are made by finding the angles of our EDT line. 
                # if zeros == 1:
                #     a = np.linalg.norm(coords)
                #     m = asin(coords[1] / a)
                #     correction = 0.5 / cos(m)
                #     corrected = a - correction
                #     LUT[z][y][x] = a
                    
                # if zeros == 0:
                #     lower_hy = [0, coords[0], coords[1]]
                #     a = np.linalg.norm(coords)
                #     b = np.linalg.norm(lower_hy)
                #     m = asin(b / a)
                #     correction = 0.5 / cos(m)
                #     corrected = a - correction
                #     LUT[z][y][x] = a
    
    return LUT
    
# Load the corrections table.    
def load_corrections(resolution = 1, max_radius = 150, verbose=False, new_build=False):
    try:
        wd = sys._MEIPASS # Determines whether we're opening the file from a pyinstaller exec.
    except AttributeError:
        wd = os.getcwd()
    rc_path = os.path.join(wd, 'Library/Radii_Corrections.npy')
    
    
    if new_build:
        LUT = table_generation(1, 150)
        np.save(rc_path, LUT)

    else:
        try:
            # Load the file.
            radii_corrections = np.load(rc_path)
            
            # Make the sure the file is big enough for our purposes.
            loaded_ratio = (max_radius/resolution)
            decimal = loaded_ratio % 1
            if decimal > 0:
                loaded_ratio -= (decimal + 1)
            if radii_corrections.shape[0] < loaded_ratio:
                # if verbose:
                print ("Generating new correction table.")
                table_generation(5,5, False)
                LUT = table_generation(resolution, max_radius)
                np.save(rc_path, LUT)
                
            if verbose:
                print ("Radii correction table successfully loaded.")
        
        except:
            if verbose:
                print ("Radii correction table not found. Generating now...")
            LUT = table_generation(resolution, max_radius)
            np.save(rc_path, LUT)
            radii_corrections = LUT
                        
        return radii_corrections


# IDE Build.
if __name__ == "__main__":
    resolution = 1
    max_radius = 150
    load_corrections(resolution, max_radius, new_build=True, verbose=True)
