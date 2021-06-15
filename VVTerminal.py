# -*- coding: utf-8 -*-
"""
By executing this program in a terminal, the specified files can be analyzed or visualized.
Most commonly, I used this program for testing and movie generation.
The features for movie generation can be adjusted in the Volume_Visualization.py file. 
Adjustments will be made to allow for movie feature alterations from this file.

Created on Tue Mar  2 15:03:10 2021

@author: jacobbumgarner
"""


import sys
from os import path, getcwd
import time
import numpy as np

from Library import Image_Processing as improc
from Library import Volume_Processing as volproc
from Library import Graph_Processing as gproc
from Library import Volume_Visualization as volvis
from Library import Feature_Extraction as feats 

from Library.Radii_Corrections import load_corrections


###############################
###### Command-line code ######
###############################
def process_file(file_path, Visualize, movie, title, resolution, gen_volume, gen_tubes, save_seg_results, save_labeled, save_graph, verbose, iteration):
    if verbose:
        print ("Analyzing file:", file_path)

    tic = time.perf_counter()

    ## Image and volume processing.
    # Get our array, make sure there is actually something in our dataset
    volume = improc.getArray(file_path)
    if volume is None:
        if verbose:
            print ("Couldn't analyze file.")
        return
        
    # Skeletonize, then find radii of skeleton points
    skeleton, points = volproc.skeletonize(volume)
    LUT = load_corrections(resolution, max_radius, verbose=verbose)
    t1 = time.perf_counter()
    skeleton_radii = volproc.calculate_radii(volume, skeleton, points, LUT, resolution, max_radius)
    del(LUT) # Just for sanity
    if verbose:
        print (f"Radii identified in {time.perf_counter() - t1:0.2f} seconds.")
    
    # Once radii have been calculated for 2D volumes, we can treat them as 3D arrays for compatability with the rest of our pipeline.
    if volume.ndim == 2:
        zeros = np.zeros(volume.shape)
        volume = np.dstack([volume, zeros])
        skeleton = np.dstack([skeleton, zeros])
        skeleton = np.dstack([zeros, skeleton])
        points = np.asarray(np.where(skeleton == 1))
        points = np.reshape(points, (-1), order = 'F')
        length = int(len(points) / 3)
        points = np.reshape(points, (length, 3))
        
    ## Network creation and analysis.
    # Send information to graph network creation.
    t1 = time.perf_counter()
    graph = gproc.create_graph(skeleton, skeleton_radii, points, resolution, prune_length, verbose)
    
    # Take our extracted centerlines and remove filtered segments from our volume dataset.
    volume = volproc.clean_volume(graph, volume, resolution=resolution, filter_length=filter_size)
    if verbose:
        print (f"Graph creation completed in {time.perf_counter() - t1:0.2f} seconds.")
    
    # Finally, we can to extract relevant features from our graph.
    if not Visualize:
        if verbose:
            print ("Analyzing...")
        results = []
        seg_results = []
        analysis_folder = '/Users/jacobbumgarner/Desktop/VesselVio'
        t1 = time.perf_counter()
        
        result, seg_result = feats.features(graph, volume, resolution, file_path, save_seg_results=save_seg_results, save_labeled=save_labeled)
        results.append(result)
        seg_results.append(seg_result)
        feats.write_results(results, analysis_folder, seg_results)
        t2 = time.perf_counter()
        if verbose:
            print (f"Feature extraction in {t2 - t1:0.2f} seconds.")
        if save_graph:
            gproc.save_graph(graph, points, file_path, analysis_folder)
    
    if verbose:
        toc = time.perf_counter()
        print (f"Dataset analysis completed in a total of {toc - tic:0.2f} seconds.")
        
    # Visualize the dataset
    if Visualize:
        volvis.generate(graph, volume, gen_tubes=gen_tubes, gen_volume=gen_volume, resolution=resolution, verbose=True, movie=movie, title=title, iteration=iteration)
     
    del(graph)
    
    del(volume)


# Loading dock for testing individual files.
def loading_dock(file_path, short_name, Visualize, movie, title, resolution, gen_volume, gen_tubes, save_seg_results, save_labeled, save_graph, verbose, iteration):
    wd = getcwd()
    
    if short_name:
        file_path = path.join(wd, file_path)
        
    process_file(file_path, Visualize, movie, title, resolution, gen_volume, gen_tubes, save_seg_results, save_labeled, save_graph, verbose, iteration)
    
    return


prune_length = 0
filter_size = 10
max_radius = 150

## Testing.
if __name__ == "__main__":
    file1 = 'FILE PATH HERE'
    file2 = 'ABBREV. FILE IN WORKING DIR'
    
    title = 'FILE_NAME.nii'
    resolution = 1
    short_name = False
    Visualize = False
    movie = True
    gen_tubes = True
    gen_volume = False
    save_seg_results = True
    save_labeled = True
    save_graph = False
    verbose = True
    iteration = 0

    loading_dock(file2, short_name=short_name, Visualize=Visualize, movie=movie, title=title, resolution=resolution, gen_volume=gen_volume, gen_tubes=gen_tubes, save_seg_results=save_seg_results,save_labeled=save_labeled, save_graph=save_graph, verbose=verbose, iteration=iteration)
