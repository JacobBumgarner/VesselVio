# -*- coding: utf-8 -*-

import numpy as np
from numba import njit, prange

from skimage.morphology import skeletonize_3d # ,binary_dilation, ball
import time
from scipy.ndimage import label


# import edt

# Skeletonization.
def skeletonize(volume):
    skeleton = skeletonize_3d(volume)
    # Messing about with multiple iterations of skeletonization. No success.
    # sphere = ball(4)
    # dilated_skeleton = binary_dilation(first_pass, sphere).astype(np.uint8)
    # skeleton = skeletonize_3d(dilated_skeleton)
    
    # Keep points in numpy format for ease of array-calculations.
    # Convert points from (3, n) to (n, 3) shape.
    
    points = np.asarray(np.where(skeleton == 1))
    points = np.reshape(points, (-1), order = 'F')

    dimension = skeleton.ndim
    if dimension == 3:
        length = int(len(points) / 3)
        points = np.reshape(points, (length, 3))
    elif dimension == 2:
        length = int(len(points) / 2)
        points = np.reshape(points, (length, 2))
    
    
    return skeleton, points

#############################
######## Input Sites ########
#############################
# Loading dock for our volume radii corrections
def calculate_radii(volume, skeleton, points, LUT, resolution, max_radius):
    if skeleton.ndim == 2:
        skeleton_radii = calculate_2Dradii(volume, skeleton, points, LUT, resolution, max_radius)
        
    elif skeleton.ndim == 3:
        skeleton_radii = calculate_3Dradii(volume, skeleton, points, LUT, resolution, max_radius)   
        
    return skeleton_radii


#############################
####### 3D Processing #######
#############################
# This function calculates the corrected radii for each centerline point.
# It is functionally the same as an EDT, but it calculates the distance to the edge (rather than the center) of the nearest
# non-vessel voxel.
@njit(fastmath=True)
def calculate_3Dradii(volume, skelly, points, LUT, resolution, max_radius):
    volume = volume
    skelly = skelly
    points = points
    
    skeleton_radii = []
    
    # Find our maximum radius
    loaded_ratio = (max_radius/resolution)
    decimal = loaded_ratio % 1
    if decimal > 0:
        loaded_ratio -= (decimal + 1)
    
    for point in points:
        z,y,x = point
        point_radii = []
        i = 1
        determined = False

        while determined == False:
            zmin = z - i
            if zmin < 0:
                zmin = 0
            ymin = y - i
            if ymin < 0:
                ymin = 0
            xmin = x - i
            if xmin < 0:
                xmin = 0
            zeros = np.where(volume[zmin:z+i+1,ymin:y+i+1,xmin:x+i+1] == 0)
            
            if len(zeros[0]) > 3:
                for j in range(len(zeros[0])):
                    zero_z = zeros[0][j] + zmin
                    zero_y = zeros[1][j] + ymin
                    zero_x = zeros[2][j] + xmin
                    zero_z_rel = abs(z - zero_z)
                    zero_y_rel = abs(y - zero_y)
                    zero_x_rel = abs(x - zero_x)
                    # zero_radius = sqrt(zero_z_rel**2 +  zero_y_rel**2 + zero_x_rel**2)
                    
                    # if zero_z_rel < loaded_ratio and zero_y_rel < loaded_ratio and zero_x_rel < loaded_ratio:
                    zero_radius = LUT[zero_z_rel][zero_y_rel][zero_x_rel]
                    # else:
                    #     zero_radius = max_radius
                        
                    point_radii.append(zero_radius)
                    
                point_radii.sort()
                rad_sum = 0
                for k in range(4):
                    rad_sum += point_radii[k]
                
                radius = rad_sum / 4
                skeleton_radii.append(radius)
                determined = True
                
            if i * resolution > max_radius:
                radius = max_radius
                skeleton_radii.append(radius)
                determined = True
                
            i += 1    
            
    return skeleton_radii

# I choose to remove small clusters from my dataset analysis.
    # Make this optional in the future? TODO
def clean_volume(g, volume, filter_length=10, resolution=1, verbose=False):
    t1 = time.perf_counter()
    # Remove 0-edge vertices and small segments.
    clusters = g.clusters()        
    vertices_togo = []
    
    struct = np.ones((3,3,3), dtype=np.int)
    labels, num_features = label(volume, structure=struct)
    del(num_features)
    filter_ids = []
    id_coords = []
    
    size_filter = filter_length * resolution
        
    for cluster in clusters:
        cluster_length = len(cluster)
        if cluster_length < size_filter:
            vertices_togo.extend(cluster)
            vert = int(cluster_length / 2) # Find point in  middle of segment
            seed_coords = g.vs[cluster[vert]]['v_coords']
            z = seed_coords[0]
            y = seed_coords[1]
            x = seed_coords[2]
            
            label_id = labels[z][y][x]
            
            filter_ids.append(label_id)
            id_coords.append([z, y, x])
    
    # Remove the filtered segments from the dataset.
    filter_ids = np.array(filter_ids)
    id_coords = np.array(id_coords)
    if len(id_coords) > 0:
        volume = filter_3Dsegments(labels, volume, filter_ids, id_coords)
    
    # Delete the filtered vertices from our graph. 
    g.delete_vertices(vertices_togo)   

    if verbose:
        print (f"Filtering {time.perf_counter - t1:0.4f}")
    
    return volume

# Filters small segments from the actual image.
@njit(fastmath=True)
def filter_3Dsegments(labels, volume, filter_ids, id_coords):
    for index in range(len(filter_ids)):
        element = filter_ids[index]
        z, y, x = id_coords[index]
        i = 1
        determined = False

        while determined == False:
            zmin = z - i
            if zmin < 0:
                zmin = 0
            ymin = y - i
            if ymin < 0:
                ymin = 0
            xmin = x - i
            if xmin < 0:
                xmin = 0
            removals = np.where(labels[zmin:z+i+1,ymin:y+i+1,xmin:x+i+1] == element)
            count = len(removals[0])

            if count > 0:
                for j in range(count):
                    zmod = zmin + removals[0][j]
                    ymod = ymin + removals[1][j]
                    xmod = xmin + removals[2][j]

                    volume[zmod][ymod][xmod] = 0
                                                  
            else:
                determined = True
                
            i += 1
            if i > 25:
                determined = True

    return volume


#############################
####### 2D Processing #######
#############################
@njit(fastmath=True)
def calculate_2Dradii(volume, skelly, points, LUT, resolution, max_radius):
    volume = volume
    skelly = skelly
    points = points
    
    skeleton_radii = []
    
    for point in points:
        y,x = point
        point_radii = []
        i = 1
        determined = False

        while determined == False:
            ymin = y - i
            if ymin < 0:
                ymin = 0
            xmin = x - i
            if xmin < 0:
                xmin = 0
            zeros = np.where(volume[ymin:y+i+1,xmin:x+i+1] == 0)
            if len(zeros[0]) > 3:
                for j in range(len(zeros[0])):
                    zero_y = zeros[0][j] + ymin
                    zero_x = zeros[1][j] + xmin
                    zero_y_rel = abs(y - zero_y)
                    zero_x_rel = abs(x - zero_x)
                    zero_radius = LUT[0][zero_y_rel][zero_x_rel] # LUT is 3d but we can just use the first slice.
                    point_radii.append(zero_radius)
                    
                point_radii.sort()
                rad_sum = 0
                for k in range(4):
                    rad_sum += point_radii[k]
                
                radius = rad_sum / 4
                skeleton_radii.append(radius)
                determined = True
                
            if i * resolution > max_radius:
                radius = max_radius
                skeleton_radii.append(radius)
                determined = True
                
            i += 1    
            
    return skeleton_radii

