
"""
Graph construction and processing pipelines
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import igraph as ig
import numpy as np
from time import perf_counter as pf

from numba import njit

import concurrent.futures as cf
from itertools import repeat, chain
from multiprocessing import cpu_count
from math import floor

from library import feature_extraction as FeatExt
from library import volume_processing as VolProc
from library import helpers


#######################
### Graph Reduction ###
#######################

def simplify_graph(g, reduced_edges,
                   volumes, surface_areas, lengths, tortuosities, 
                   radii_avg, radii_max, radii_min, radii_SD,
                   vis_radii, coords_lists, radii_lists):
    g.delete_edges(g.es())
    g.add_edges(reduced_edges, {'volume':volumes, 'surface_area':surface_areas,
                                'length':lengths, 'tortuosity':tortuosities,
                                'radius_avg':radii_avg, 'radius_max':radii_max,
                                'radius_min':radii_min, 'radius_SD':radii_SD,
                                'coords_list':coords_lists, 
                                'radii_list':radii_lists, 
                                'vis_radius':vis_radii})
    g.delete_vertices(g.vs.select(_degree = 0))
    return
 
######################
### Edge Detection ###
######################

## Scanning orientations for edge detection.
def orientations():
    # Prepration for edge point analysis. Directional edge detection 
    # based on C. Kirst's algorithm.
    # Matrix preparation for edge detetction
    # Point of interest rests at [1,1,1] in 3x3x3 array.
    scan = np.array([[2, 2, 0],
                     [2, 2, 1],
                     [2, 2, 2],
                     [1, 2, 0],
                     [1, 2, 1],
                     [1, 2, 2], # End of top slice
                     [2, 1, 0],
                     [2, 1, 1],
                     [2, 1, 2],
                     [1, 1, 2], # End of middle slice
                     [2, 0, 0],
                     [2, 0, 1],
                     [2, 0, 2]]) # End of bottom slice
        
    scan -= 1

    return scan

## Construct vertex index LUT
def construct_vLUT(points, shape):
    values = np.arange(0, points.shape[0]) 
    vertex_LUT = np.zeros(shape, dtype=np.int_)
    vertex_LUT[points[:,0], points[:,1], points[:, 2]] = values
    return vertex_LUT

@njit(cache=True)
def identify_edges(points, vertex_LUT, spaces):    
    points = points
    edges = []
           
    for i in range(points.shape[0]):
        local = spaces + points[i]
        
        for j in range(local.shape[0]):
            # Check if neighbor is a non-zero, then add edge if it is.
            target_index = vertex_LUT[local[j,0], local[j,1], local[j,2]]
            if target_index > 0: 
                edges.append((i, target_index))
    return edges


#########################
### Clique Processing ###
#########################
# Isoalte branch points from the graph
def g_branch_graph(g, components=False):
    # Start by getting a vertex count for our graph 
    # and assign all vertices their original ID.
    # This will prevent us from having to look up the IDs from a backlog
    g.vs['id'] = np.arange(g.vcount())    
    
    # Isolate branch point cliques from the graph.
    gbs = g.subgraph(g.vs.select(_degree_gt = 2))

    if components:
        cliques = [clique for clique in gbs.components() if len(clique) > 3]
    else:
        # Eliminate all 1-degree edges that are connected to the cliques
        # Loop through this process indefinitely until 
        # all non-clique branches are removed.
        while True:
            count = len(gbs.vs.select(_degree_lt = 2))
            if count == 0:
                break
            gbs = gbs.subgraph(gbs.vs.select(_degree_gt = 1))   
        cliques = [clique for clique in gbs.maximal_cliques() if 2 < len(clique) < 5]
    lens = [len(c) for c in cliques]
    return gbs, cliques

# Restore external neighbors to the newly added vertex
def restore_v_neighbors(g, gb_vs):
    g_vs = g.vs[gb_vs['id']]
    
    neighbors = []
    all_vs = zip(g_vs, gb_vs)
    for g_v, gb_v in all_vs:
        if g_v.degree() != gb_v.degree(): # find external neighbors
            clique_neighbors = [n['id'] for n in gb_v.neighbors()]
            neighbors += [n['id'] for n in g_v.neighbors() if n['id'] 
                          not in clique_neighbors] # add those not in clique

    return neighbors

def new_vertex(g, vs, coords=None):
    if vs[0]['vis_radius']:
        vis_radius = np.mean(vs['vis_radius'])
    else:
        vis_radius = None
        
    v_radius = np.mean(vs['v_radius'])
    
    if not coords:
        coords = np.mean(vs['v_coords'], axis=0)
    
    vertex = (v_radius, vis_radius, coords)
    neighbors = restore_v_neighbors(g, vs)
    return vertex, neighbors


## See documentation for explanation of clique filters
# Class 3 clique filter - the big cajone
def class3_filter(g, gbs, clique):
    vs = gbs.vs[clique]
    # find the coordinates of all of the clique vertices
    coords = np.insert(np.array(vs['v_coords']), 3, 
                       np.arange(len(clique)), axis=1)
    
    # Scan along the cluster in the longest axis
    distances_rough = [0,0,0]
    for i in range(3):
        coords = coords[np.argsort(coords[:,i])]
        # no sqrt here to save time, only add indices, not the id added above
        distances_rough[i] = np.abs(coords[0, :3] - coords[-1, :3]).sum() 
    axis = np.argmax(distances_rough)
    coords = coords[np.argsort(coords[:, axis])]
    
    # Slice along the clique bundle to create a new centerline
    slices = np.linspace(0, coords.shape[0], 
                         min(6, coords.shape[0]), endpoint=True)

    new_vertices = []
    for i in range(slices.shape[0] - 1):
        bottom, top = int(slices[i]), int(slices[i+1])
        ids = coords[bottom:top, 3].tolist()
        
        # Get the new vertices
        vertex, neighbors = new_vertex(g, vs[ids])
        new_vertices.append([vertex, neighbors])


    return new_vertices

# Class 2 clique filter.
def class2_filter(g, gbs, clique):
    # For these odd cliques, reduce the clique to a single branchpoint junction
    gb_vs = gbs.vs[clique]
        
    # Add new vertex and restore external projections from the cluster    
    vertex, neighbors = new_vertex(g, gb_vs)
    
    return [vertex, neighbors]

def class2and3_dispatcher(bottom, top):
    vertices_togo= []
    class_two = []
    class_three = []
    for clique in cliques[bottom:top]:
        vertices_togo += gbs.vs[clique]['id']
        if len(clique) <= 50:
            class_two.append(class2_filter(g, gbs, clique))
        else:
            class_three.append(class3_filter(g, gbs, clique))

    return [vertices_togo, class_two, class_three]

def class2and3_processing():
    new_edges = []
    vertices_togo = []
    class_two = []
    class_three = []
    
    clique_count = len(cliques)
    workers = cpu_count()
    if helpers.unix_check() and clique_count > workers:
        results = helpers.multiprocessing_input(class2and3_dispatcher, 
                                                clique_count, 
                                                workers, sublist=True)
        for result in results:
            vertices_togo.extend(result[0])
            class_two += result[1]
            class_three += result[2]
        
    else:
        vertices_togo, class_two, class_three = class2and3_dispatcher(0, 
                                                                      clique_count)
        
    # Add the results to the respective lists, see order in class2/3

    # Restore the class 2 vertices
    for cluster in class_two:
        v_info = cluster[0]
        neighbors = cluster[1]
        v = g.add_vertex(v_radius=v_info[0], vis_radius=v_info[1],
                         v_coords=v_info[2])
        new_edges.extend(sorted(tuple([v.index, n]) for n in neighbors))
        
    # Restore the class 3 vertices
    for cluster in class_three:
        cluster_line = []
        for c in cluster:
            v_info = c[0]
            neighbors = c[1]
            v = g.add_vertex(v_radius=v_info[0], vis_radius=v_info[1],
                            v_coords=v_info[2])
            new_edges.extend(sorted(tuple([v.index, n]) for n in neighbors))
        
        for i in range(len(cluster_line)-1):
            edge = sorted(tuple([cluster_line[i], cluster_line[i+1]]))
            new_edges.extend(edge)
        
    # Remove duplicate edges
    new_edges = [new_edge for new_edge in set(new_edges)]
    g.add_edges(new_edges) # Add the new edges
    g.delete_vertices(vertices_togo) # Delete the spurious points
    return len(class_two), len(class_three)

# Class 1 clique filter.
def class1_filter(bottom, top):
    edges_togo = []

    for clique in cliques[bottom:top]:   
        # Get the original vertices
        g_vs = g.vs[gbs.vs[clique]['id']]
        
        # Check to see if the cliques fit in our class
        if any(degree >= 5 for degree in g_vs.degree()):
            continue

        # Weight the vs based on radius and neighbor radius
        weights = g_vs['v_radius']
        for i, v in enumerate(g_vs):
            for n in v.neighbors():
                weights[i] += n['v_radius']
        
        # Sort the vertices based on their weights, remove edge between smallest
        sorted_ids = [id for _, id in sorted(zip(weights, g_vs))]
        edge = (sorted_ids[0]['id'], sorted_ids[1]['id'])
        edges_togo.append(edge)
        
    return edges_togo

# G, GBS, Clique are all global.
def class1_processing():
    # now we want to process these cliques
    edges_togo = []

    # Make sure there's more cliques than workers 
    workers = cpu_count()
    clique_count = len(cliques)
    if helpers.unix_check() and clique_count > workers:
        edges_togo = helpers.multiprocessing_input(class1_filter, 
                                                   clique_count, workers)
    else:
        edges_togo = class1_filter(0, clique_count)
        
    g.delete_edges(edges_togo)
    
    return len(edges_togo)


def clique_filter_input(g, verbose=False):
    if verbose:
        tic = pf()
    
    # Set up globals for multiprocessing
    global gbs, cliques

    # Isolate all cliques.
    processed = class_one = class_two = class_three = 0
    gbs, cliques = g_branch_graph(g)
    
    if verbose:
        print ("Filtering class 1 clique clusters...", end='\r')
    class_one = class1_processing()
    processed += class_one
    gbs, cliques = g_branch_graph(g, components=True)
    
    if verbose:
        print ("Filtering class 2 and 3 clique clusters...", end='\r')
    if len(cliques) > 0:
        class_two, class_three = class2and3_processing()
        processed += class_two + class_three
        
    # Cleanup
    del(g.vs['id'], gbs, cliques)
    
    if verbose:
        print (f'{processed} branch point clique clusters '
               f'corrected in {pf() - tic:0.2f} seconds.')
        # print (f"{class_one},{class_two},{class_three}")
    return
     
     
#######################
### Segment Pruning ###
#######################
# Isolate segments/endpoints from the graph
def segment_isolation(g, filter):
    # Store ids of our segment vertices
    segment_ids = g.vs.select(_degree_lt = filter) 
    gsegs = g.subgraph(segment_ids)
    segments = gsegs.clusters() # Find segments
    segments = [s for s in segments if len(s) < max(1, g_prune_len)]
    return gsegs, segments, segment_ids


# Remove short connected endpoint segments from the main graph. 
# g, resolution, prune_length, verbose=False
def segment_pruning(bottom, top):        
    # Prune only the connected endpoints here. 
    # Isolated segments are pruned later with flood filling in VolProc.
    vertices_togo = []
    pruned = 0
    for segment in segments[bottom:top]:
        num_verts = len(segment)
        if num_verts < g_prune_len:
            # Isolate endpoint segments. Should only have one vertex with degree == 1
            # Faster than calling .indices
            vertices = [segment_ids[vertex].index for vertex in segment] 
            degrees = g.degree(vertices)
            ends = degrees.count(1)

            # If endpoint segment, calculate the size. 
            if ends == 1:
                # Send off to our feature extraction to find the size
                if num_verts == 1:
                    segment_length = FeatExt.small_seg_path(g, segment, 
                                                            segment_ids, g_res, 
                                                            centerline_smoothing=g_cl_smoothing,  
                                                            pruning=True)
                
                elif num_verts > 1:
                    segment_length = FeatExt.large_seg_path(g, gsegs, segment, 
                                                            segment_ids, g_res, 
                                                            centerline_smoothing=g_cl_smoothing, 
                                                            pruning=True)
                        
                if segment_length < g_prune_len:    
                    pruned += 1
                    vertices_togo.extend(vertices)
    
    return [vertices_togo, pruned]

def v_graph_pruning_io():
    pruned = 0
    vertices_togo = []
    
    workers = cpu_count()
    seg_count = len(segments)
    if helpers.unix_check() and seg_count > workers:
        results = helpers.multiprocessing_input(segment_pruning, seg_count, 
                                                workers, sublist=True)
        for result in results:
            vertices_togo.extend(result[0])
            pruned += result[1]
    else:
        vertices_togo, pruned = segment_pruning(0, seg_count)
        
    g.delete_vertices(vertices_togo)
    return pruned


# Prune endpoints of edge-graphs
def edge_graph_prune(g, segment_ids, segments, prune_length):
    pruned = 0
    vertices_togo = []
    for segment in segments:
        if len(segment) > 1:
            continue # Just in case something goes wrong with 
        edge = g.incident(segment_ids[segment[0]].index)
        if len(edge) > 1:
            continue # Fail safe again
        
        segment_length = g.es[edge[0]]['length']
        if segment_length < prune_length:
            vertices_togo.append(segment_ids[segment[0]].index)
            pruned += 1
    
    g.delete_vertices(vertices_togo)
    return pruned


# Input function for segment pruning of volumes and vertex-graphs
def prune_input(g, prune_length, resolution, centerline_smoothing=True, 
                graph_type='Centerlines', verbose=False):    
    if verbose:
        t = pf()
        print ('Pruning end point segments...', end='\r')
    if graph_type == 'Centerlines':
        filter = 3
    else:
        filter = 2
    
    # Define global variables for multiprocessing
    global gsegs, segments, segment_ids, g_prune_len, g_res, g_cl_smoothing
    g_prune_len = prune_length
    g_res = resolution.copy()
    g_cl_smoothing = centerline_smoothing
    gsegs, segments, segment_ids = segment_isolation(g, filter)
    
    if graph_type == 'Centerlines':
        # First pass to prune desired endpoint segments
        # G will update without a return. Stored as a mutable object.
        p1 = v_graph_pruning_io() 
        
        # Second pass to prune single-vertex endpoints
        g_prune_len = 1.01
        gsegs, segments, segment_ids = segment_isolation(g, filter)
        p2 = v_graph_pruning_io()
    
    else:
        p1 = edge_graph_prune(g, segment_ids, segments, prune_length)
        # No second pass for edge graphs
        p2 = 0
    
    # Global variable cleanup
    del(gsegs, segments, segment_ids, g_prune_len, g_res)
    
    if verbose:
        print (f"Pruned {p1 + p2} segments in {pf() - t:0.2f} seconds.")
    
    return 



#########################
### Segment Filtering ###
#########################
# Filter segments based on some length
def vgraph_segment_filter(bottom, top):
    vertices_togo = []    
    filtered = 0
    
    # Iterate through clusters, identify segments, 
    # filter those short enough to be removed
    for cluster in clusters[bottom:top]:
        # Check to see that we have an isolated segment, i.e., no branch points
        degrees = g.degree(cluster)
        cluster_length = len(cluster)
        if degrees.count(1) == 2: # Only examine isolated segments
            if cluster_length < 4:
                segment_length = FeatExt.small_seg_path(g, cluster, 
                                                        resolution=g_res,
                                                        centerline_smoothing=cl_smoothing,  
                                                        pruning=True)
            else:
                segment_length = FeatExt.large_seg_filter(g, cluster, g_res,
                                                          centerline_smoothing=cl_smoothing)

            if segment_length < g_filter_len: # Remove the vertices if short enough
                vertices_togo.extend(cluster)
                filtered += 1
            
    return [vertices_togo, filtered]

def vgraph_segment_filter_io(g, filter_length, resolution, 
                             centerline_smoothing):
    # Set up globals for forked multiprocessing
    global clusters, g_filter_len, g_res, ret_coords, cl_smoothing
    g_filter_len = filter_length
    g_res = resolution.copy()
    cl_smoothing = centerline_smoothing
    
    filtered = 0
    vertices_togo = []
    
    # Label clusters in the dataset
    clusters = g.components()
    
    # If we are here, that means that the filter value is non-zero. 
    # So find all clusters that are either 2 vertices long 
    # or those that are shorter than the filter length, whichever is the largest
    clusters = [c for c in clusters if len(c) <= max(2, g_filter_len)]     

    seg_count = len(clusters)
    workers = cpu_count()
    if helpers.unix_check() and seg_count > workers:
        results = helpers.multiprocessing_input(vgraph_segment_filter,
                                                seg_count, workers, 
                                                sublist=True)
        for result in results:
            vertices_togo.extend(result[0])
            filtered += result[1]
    else:
        vertices_togo, filtered = vgraph_segment_filter(0, seg_count)
    
    g.delete_vertices(vertices_togo)   
    
    # Global variable cleanup
    del(clusters, g_filter_len, g_res, cl_smoothing)
    
    return filtered


# Filter isolated segments in edge graphs
def egraph_segment_filter(g, filter_length):
    vertices_togo = []
    filtered = 0
    
    # Isolate individual segment clusters
    clusters = g.clusters()
    for cluster in clusters:
        if len(cluster) == 2: # If segment is isoalted
            edge = g.incident(cluster[0])
            
            # Check edge length, delete if short enough
            if g.es[edge[0]]['length'] < filter_length:
                vertices_togo.extend(cluster)
                filtered += 1
            
    g.delete_vertices(vertices_togo)
    return filtered


def filter_input(g, filter_length, resolution, centerline_smoothing=True,
                 graph_type='Centerlines', verbose=False):
    if verbose:
        t = pf()
        print ('Filtering isolated segments...', end='\r')
    
    # Eliminate isolated vertices
    g.delete_vertices(g.vs.select(_degree = 0))

    # Vertex graph segment filtering
    if filter_length > 0:
        if graph_type == 'Centerlines':            
            filtered = vgraph_segment_filter_io(g, filter_length, resolution,
                                                centerline_smoothing)

        # Edge graph segment filtering
        else:
            filtered = egraph_segment_filter(g, filter_length)

    if verbose:
        if filter_length > 0:
            print (f'Filtered {filtered} isolated '
                   f'segments in {pf() - t:0.2f} seconds.')
        else:
            print ('', end='\r')
        
    return


######################
### Graph creation ###
######################
def create_graph(volume_shape, skeleton_radii, vis_radii, points, point_minima, 
                 verbose=False):
    if verbose: 
        print (f'Creating Graph...', end='\r')
        tic = pf()
        
    # Create graph, populate graph with correct number of vertices.    
    global g
    g = ig.Graph()
    g.add_vertices(len(points))
    
    # Populate vertices with cartesian coordinates and radii
    g.vs['v_coords'] = VolProc.absolute_points(points, point_minima)
    g.vs['v_radius'] = skeleton_radii
    g.vs['vis_radius'] = vis_radii
            
    # Prepare what we need for our edge identifictation
    spaces = orientations() #13-neighbor search
    vertex_LUT = construct_vLUT(points, volume_shape)
    edges = identify_edges(points, vertex_LUT, spaces)
    g.add_edges(edges)
    
    if verbose:
        print ('Filtering cliques...', end='\r')
    
    # Remove spurious branchpoints from our labeling
    clique_filter_input(g, verbose=verbose)

    if verbose:
        print (f'Graph creation completed in {pf() - tic:0.2f} seconds.')
    
    return g