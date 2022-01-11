
"""
The final feature extraction pipeline, doesn't include radius analysis, as those are conducted on the volume.
Copyright © 2021, Jacob Bumgarner
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright © 2021 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


from time import perf_counter as pf
from collections import namedtuple

import numpy as np
from scipy import interpolate
from geomdl import knotvector
from math import log, ceil
from numba import njit

from multiprocessing import cpu_count

from Library import Graph_Processing as GProc
from Library import Image_Processing as ImProc
from Library import helpers


#############################
### Segment Interpolation ###
#############################
def seg_interpolate(point_coords, vis_radius):
    # Find basis-spline (BSpline) of points to smooth jaggedness of skeleton.
    # The resources I used to learn about BSplines can be examined below:
        # https://web.mit.edu/hyperbook/Patrikalakis-Maekawa-Cho/node17.html
        # http://learnwebgl.brown37.net/07_cameras/points_along_a_path.html
        # http://www.independent-software.com/determining-coordinates-on-a-html-canvas-bezier-curve.html
        
    # Set appropriate degree of our BSpline
    num_verts = point_coords.shape[0]
    if num_verts > 4:
        spline_degree = 3
    else:
        spline_degree = max(1, num_verts - 1)
              
    # The optimal number of interpolated segment points for visualization was determined emperically as a trade-off value between ground-truth length and computational costs.
    delta = delta_calc(num_verts, vis_radius)    
    
    # Find the segment length based on our cubic BSpline.
    # https://github.com/kawache/Python-B-spline-examples
    u = np.linspace(0, 1, delta, endpoint=True) # U
    
    # Scipy knot vector format
    knots = knotvector.generate(spline_degree, num_verts) # Knotvector
    tck = [knots, [point_coords[:, 0], point_coords[:, 1], point_coords[:, 2]], spline_degree] 
    
    coords_list = np.array(interpolate.splev(u, tck)).T
    return coords_list

# Build interpolation delta
def delta_calc(num_verts, vis_radius):
    # base = 3 if num_verts > 50 else 2
    delta = max(3, ceil(num_verts / log(num_verts, 2)))
    if num_verts > 100 or (vis_radius > 3 and num_verts > 20):
        delta = int(delta / 2)
    return delta

##########################
### Feature Extraction ###
##########################
FeatureSet = namedtuple("FeatureSet", """volume_or_PAF, surface_area, length, tortuosity,
                        radius_avg, radius_max, radius_min, radius_SD,
                        radii_list, coords_list, vis_radius""")
# Unified function to extract features from a segment
def feature_extraction(g, point_list, resolution, image_dim=None, image_shape=None,
                       centerline_smoothing=True, pruning=False, visualize=False):
    
    vs = g.vs[point_list]
    ### Radius ###
    radii_list = vs['v_radius']
    r_avg, r_max, r_min, r_SD = radii_calc(radii_list)
    
    if visualize:
        vis_radius = np.mean(vs['vis_radius'])
        vis_radii = vs['vis_radius']
    else:
        vis_radius = None 
        vis_radii = None

    ### Length ###
    coords_list = vs["v_coords"]
    coords = np.array(coords_list)
    
    # Interpolate points for a smoothed centerline.
    if centerline_smoothing:
        # See global def of min_resolution in ImProc
        coords = seg_interpolate(coords, r_avg / ImProc.min_resolution)
        segment_length = length_calc(coords, resolution)
    
    if pruning: # Return segment length if finding size for pruning/filtering
        return segment_length
            
    ### Tortuosity ###
    delta = np.array([coords[0], coords[-1]])
    cord_length = length_calc(delta, resolution)
    
    # See gobal variable min_res in feature_input.
    # Had some issues with loop start/ends being altered by minute fractions, causing issues.
    if cord_length >= ImProc.min_resolution:
        tortuosity = segment_length / cord_length
    else: # Loop tortuosity operationally defined as 0
        tortuosity = 0
                            
    ### Surface Area ###
    # Only lateral surface area, not of caps
    if image_dim == 3:
        surface_area = 2 * np.pi * r_avg * segment_length
    elif image_dim == 2:
        surface_area = 2 * r_avg * segment_length
    
    ### Volume ###    
    if image_dim == 3:
        volume_or_PAF = np.pi * r_avg**2 * segment_length
    elif image_dim == 2:
        volume_or_PAF = surface_area / np.prod(image_shape) * 100 if image_shape else 0
                  
    if not visualize:
        coords = None # No need to hang on to these if not visualizing or exporting the graph
        
    features = FeatureSet(volume_or_PAF, surface_area, segment_length, tortuosity,
                          r_avg, r_max, r_min, r_SD,
                          vis_radii, coords, vis_radius)
    return features

## General Features
# EDT Calculations for segment splines
@njit(fastmath=True)
def length_calc(coords, resolution):    
    # Calculate square roots
    deltas = coords[0:-1] - coords[1:]
    squares = (deltas * resolution)**2
    results = np.sqrt(np.sum(squares, axis=1))
    return np.sum(results)

# Radius features
def radii_calc(radii_list):
    r_avg = np.mean(radii_list)
    r_max = np.max(radii_list)
    r_min = np.min(radii_list)
    r_SD = np.std(radii_list)
    return r_avg, r_max, r_min, r_SD

## Edge graph calculations
# Calculate edge volumes
def egraph_volume_calc(g):
    radii = np.array(g.es['radius_avg'])
    radii2 = np.square(radii)
    lengths = np.array(g.es['length'])
    volumes = np.pi * radii2 * lengths  # Volume
    g.es['volume'] = volumes
    return g

# Surface area calculation
def egraph_sa_calc(g):
    # Calculate lateral surface area; ignore the caps
    # i.e., A = 2hrπ, not A = 2πrh + 2πr^2
    radii = np.array(g.es['radius_avg'])
    lengths = np.array(g.es['length'])
    surf_areas = 2 * np.pi * radii * lengths # Lateral surface area    
    g.es['surface_area'] = surf_areas
    return g

# Calculate edge tortuosities
def egraph_tortuosity_calc(g, resolution, sources=None, targets=None):
    # Find cord length of the edge
    if sources is None:
        sources = [e.source for e in g.es()]
        targets = [e.target for e in g.es()]
    source_coords = g.vs[sources]['v_coords']
    target_coords = g.vs[targets]['v_coords']

    deltas = source_coords - target_coords
    squares = (deltas * resolution)**2
    cord_lengths = np.sqrt(np.sum(squares, axis=1))
    
    # Calculate torutosity
    lengths = g.es["Length"]
    tortuosities = lengths / cord_lengths
    g.es["tortuosity"] = tortuosities
    
    return g
  

##########################
### Segment Processing ###
##########################
# Create a list of the coords and radii of the vertices of extracted 1-vertex segments.
# (Can either be 2- or 3-vertices long)
def small_seg_path(g, segment, segment_ids=None, resolution=None, centerline_smoothing=True, pruning=False):
    # Check to see if we're filtering segments or not
    if segment_ids: # Needed for pruning where there are no seg ids
        vert = segment_ids[segment[0]].index
    else:
        vert = segment[0]
    
    # Find point list of the segment
    point_list = g.neighbors(vert)
    point_list.insert(1, vert) # Insert vert into middle or right
    
    if pruning:
        segment_length = feature_extraction(g, point_list, resolution, centerline_smoothing=centerline_smoothing, pruning=True)
        return segment_length
    
    return point_list


# Create a list of the coords and radii of the vertices of extracted segments.
def large_seg_path(g, gsegs, segment, segment_ids, resolution=None, centerline_smoothing=True, pruning=False):    
    # First find the endpoints of our segment.
    degrees = gsegs.degree(segment)
    endpoints = [segment[i] for i, d in enumerate(degrees) if d == 1]
    
    if len(endpoints) == 2:
        # Find the ordered path of vertices between each endpoint.
        # The indices of this path will be relative
        path = gsegs.get_shortest_paths(endpoints[0], to=endpoints[1], output='vpath')[0]

        # Add true indices of our segment path to the point_list.
        point_list = [segment_ids[point].index for point in path]
        
        # Extend the point_list by any neighbors on either end of the segment in the original graph.
        end_neighborhood = point_list[0:2] + point_list[-2:]
        for i in range(2):
            for neighbor in g.neighbors(point_list[-i]):
                if neighbor not in end_neighborhood:
                    if i == 0:
                        point_list.insert(0, neighbor)
                    else:
                        point_list.append(neighbor)
                        
    # Loops in the vasculature...
    elif len(endpoints) != 2:
        point_list = loop_path(gsegs, segment, segment_ids)

    if pruning:
        return feature_extraction(g, point_list, resolution, centerline_smoothing=centerline_smoothing, pruning=True)

    return point_list

## Filtering Function  
# Find length of isolated segments in the dataset.
# Decided to have a separate function for this one because there 
    # is no gsegs subgraph for this process. 
def large_seg_filter(g, segment, resolution, centerline_smoothing=True):
    # First find the endpoints of our segment.
    degs = g.degree(segment)
    endpoints = [segment[loc] for loc, deg in enumerate(degs) if deg == 1]

    if len(endpoints) == 2:
        # Find coords of ordered path.
        point_list = g.get_shortest_paths(endpoints[0], to=endpoints[1], output='vpath')[0]
        point_coords = np.array(g.vs[point_list]['v_coords'])
    
    # Loops in the vasculature...
    elif len(endpoints) != 2:
        point_list = loop_path(g, segment)
                
    # Interpolate points for a smoothed centerline.
    if centerline_smoothing:
        point_coords = seg_interpolate(point_coords, np.mean(g.vs[point_list]['v_radius'])/ImProc.min_resolution)

    # Calculate segment length from our interpolated coordinates
    segment_length = length_calc(point_coords, resolution)
       
    return segment_length    


# Map out the point list for loops in the vasculature
def loop_path(gsegs, segment, segment_ids=None):
    try:
        loop = []
        # Choose a random first point.
        v1 = segment[0]
        loop.append(v1)
        previous = v1
                    
        # Now loop through the points until we find the first point.
        looped = False
        i = 0
        size = len(segment)
        # Start with random point in the segment. 
        while looped == False:
            if i > size: # Safe guard
                looped = True
                break
            # Get neighbors of that point. Make sure the neighbors don't match the 2nd to previous added.
            # Add them to the loop if they don't.
            ns = gsegs.neighbors(loop[-1]) 
            if ns[0] != previous and ns[0] != v1:
                loop.append(ns[0])
            elif ns[1] != previous and ns[1] != v1:
                loop.append(ns[1])
            else:
                looped = True
            previous = loop[-2]
            i += 1
            
        # Convert back into graph units.
        if segment_ids:
            point_list = [segment_ids[point].index for point in loop]
        else:
            point_list = loop
            
        return point_list
    
    except:
        # If there is some odd case that slipped through...
        return [segment_ids[v] for v in segment[0:2]]
        
        



##########################
### Feature Processing ###
##########################
# Result recording
def record_results(g, features, edges, reduce_graph):        
    segment_count = len(features)
    volumes = np.zeros(segment_count)
    surface_areas = np.zeros(segment_count)
    lengths = np.zeros(segment_count)
    tortuosities = np.zeros(segment_count)
    radii_avg = np.zeros(segment_count)
    radii_max = np.zeros(segment_count)
    radii_min = np.zeros(segment_count)
    radii_SD = np.zeros(segment_count)
    vis_radii = np.zeros(segment_count)
    coords_lists = []
    radii_lists = []
    
    for i, feature in enumerate(features):
        volumes[i] = feature.volume_or_PAF
        surface_areas[i] = feature.surface_area
        lengths[i] = feature.length
        tortuosities[i] = feature.tortuosity
        radii_avg[i] = feature.radius_avg
        radii_max[i] = feature.radius_max
        radii_min[i] = feature.radius_min
        
        if reduce_graph:
            # Z,Y,X -> X,Y,Z for visualization
            feature.coords_list[:,[0,2]] = feature.coords_list[:,[2,0]] 
            vis_radii[i] = feature.vis_radius
            coords_lists.append(feature.coords_list)
            radii_lists.append(feature.radii_list)    
                
    if reduce_graph:
        GProc.simplify_graph(g, edges, volumes, surface_areas,
                                lengths, tortuosities,
                                radii_avg, radii_max, radii_min, radii_SD,
                                vis_radii, coords_lists, radii_lists)
    
    return volumes, surface_areas, lengths, tortuosities, radii_avg, radii_max, radii_min, radii_SD        

# Input to extract features from segments
def segment_feature_extraction(top, bottom):
    features = []
    edges = []
    
    for segment in segments[top:bottom]:
        if len(segment) == 1:
            ordered_segment = small_seg_path(g, segment, segment_ids)
        elif len(segment) > 1:
            ordered_segment = large_seg_path(g, gsegs, segment, segment_ids)
        if save_edges:
            edges.append([ordered_segment[0], ordered_segment[-1]])
        features.append(feature_extraction(g, ordered_segment, g_res, image_dim=im_dim, image_shape=im_shape,
                                           centerline_smoothing=cl_smoothing, visualize=save_edges))
    return [features, edges]

# Input to extract features from between-branch point segments
def branch_segment_feature_extraction(top, bottom):
    features = []
    edges = []
    
    for segment in branch_segments[top:bottom]:
        ends = [branch_ids[segment.target].index, branch_ids[segment.source].index]
        if save_edges:
            edges.append(ends)
        features.append(feature_extraction(g, ends, g_res, image_dim=im_dim, image_shape=im_shape,
                                           centerline_smoothing=cl_smoothing, visualize=save_edges))
      
    return [features, edges]      

# Extract features from vertex graphs.
def vgraph_analysis(graph, resolution, centerline_smoothing, reduce_graph, 
                    image_dim, image_shape, verbose=False):
    features = []
    edges = []

    # Set up the global variables for forked multiprocessing
    global g, g_res, cl_smoothing, save_edges, im_dim, im_shape
    g = graph # Pointer to graph, not a copy
    g_res = resolution.copy()
    cl_smoothing = centerline_smoothing
    save_edges = reduce_graph
    im_dim = image_dim
    im_shape = image_shape
    
    ## First extract results from segments that aren't between branch points
        # This represents the vast majority of segments 
    if verbose:
        print ("Analyzing large segments...", end='\r')
    global gsegs, segments, segment_ids
    segment_ids = g.vs.select(_degree_lt = 3)
    gsegs = g.subgraph(segment_ids)   
    segments = list(gsegs.components())
    
    seg_count = len(segments)
    workers = cpu_count()
    if helpers.unix_check() and seg_count > workers:
        results = helpers.multiprocessing_input(segment_feature_extraction, seg_count,
                                                workers, sublist=True)
        for result in results:
            features.extend(result[0])
            edges.extend(result[1])
    else:
        features, edges = segment_feature_extraction(0, seg_count)
        
    # Global cleanup
    del(gsegs, segments, segment_ids)
    
    
    ## Now extract features from between-branch point segments
         # These have typically 2-3 vertices
    if verbose:
        print ("Analyzing large segments", end='\r')         
    global branch_segments, branch_ids
    branch_ids = g.vs.select(_degree_gt = 2)
    gbifs = g.subgraph(branch_ids)    
    branch_segments = gbifs.es() # Can slice this iterator

    seg_count = len(branch_segments)
    workers = cpu_count()
    if helpers.unix_check() and seg_count > workers:
        results = helpers.multiprocessing_input(branch_segment_feature_extraction,
                                                seg_count, workers, sublist=True)
        for result in results:
            features.extend(result[0])
            edges.extend(result[1])
    else:
        b_features, b_edges = branch_segment_feature_extraction(0, seg_count)
        features.extend(b_features)
        edges.extend(b_edges)
    
    # Global variable cleanup
    del(g, branch_segments, branch_ids, g_res, cl_smoothing, save_edges, im_dim, im_shape)
    
    if verbose:
        print ("Organizing results...", end='\r')
    # Return the results and reduce the graph if saving graph or visualizing
    return record_results(graph, features, edges, reduce_graph)
    
    
# Extract features from edge graphs
def egraph_analysis(g):
    # Build numpy arrays for each feature
    volumes = np.zeros(g.ecount())
    surface_areas = np.zeros(g.ecount())
    lengths = np.zeros(g.ecount())
    tortuosities = np.zeros(g.ecount())
    radii_avg = np.zeros(g.ecount())
    radii_max = np.zeros(g.ecount())
    radii_min = np.zeros(g.ecount())
    radii_SD = np.zeros(g.ecount()) 
    vis_radii = np.zeros(g.ecount())
    
    features = {'volume':volumes, 'surface_area':surface_areas,'length':lengths,
                'tortuosity':tortuosities, 
                'radius_avg':radii_avg, 'radius_min':radii_max, 
                'radius_min':radii_min, 'radius_SD':radii_SD, 'vis_radius':vis_radii}
    
    attributes = g.edge_attributes()
    for i,e in enumerate(g.es()):
        for attribute in attributes:
            if attribute not in ['hex', 'ROI_ID']:
                features[attribute][i] = e[attribute]
    
    return volumes, surface_areas, lengths, tortuosities, radii_avg, radii_max, radii_min, radii_SD


###################
### Feature I/O ###
###################
# Main function for extracting the features from our dataset.
def feature_input(g, resolution, filename, image_dim=3, image_shape=None,
                  graph_type='Centerlines', ROI_name='None', ROI_volume='NA',
                  centerline_smoothing=True, save_seg_results=False, 
                  reduce_graph=False, verbose=False):
        
    # Check to make sure that the graph has remaining vessels
    if not g.vs():
        return [filename, ROI_name, 'Empty dataset'], ['Empty Dataset']
        
    if verbose:
        t1 = pf()   
        print ('Analyzing dataset...             ', end='\r')
            
    # Extract features from the graph
    if graph_type == 'Centerlines':
        volumes_or_PAFs, surface_areas, lengths, tortuosities, radii_avgs, radii_maxes, radii_mins, radii_SD = vgraph_analysis(g, resolution, centerline_smoothing, reduce_graph, image_dim, image_shape, verbose=verbose)    
    else:
        volumes_or_PAFs, surface_areas, lengths, tortuosities, radii_avgs, radii_maxes, radii_mins, radii_SD = egraph_analysis(g)

    if verbose:
        print ("Analyzing whole-network features...", end='\r')
    ### Prepare results for excel export
    ## Whole-network features
    # Length
    network_length = np.sum(lengths)
    segment_count = lengths.shape[0]
    segment_partitioning = segment_count / network_length

    # Volume/Percent Area Fraction
    if image_dim == 3:
        network_volume_or_PAF = np.sum(volumes_or_PAFs)
    elif image_dim == 2:
        network_volume_or_PAF = np.sum(volumes_or_PAFs) if image_shape else 'NA'

    # Surface area
    network_SA = np.sum(surface_areas)
    
    # Brach points and end points    
    bs = g.vs.select(_degree_gt = 2)
    branchpoints = len(bs)
    es = g.vs.select(_degree = 1)
    endpoints = len(es)
    
    # ROI Volume
    if not isinstance(ROI_volume, str): # 'NA' for non-annotated volumes
        ROI_volume *= np.prod(resolution)
    
    network_features = [filename, ROI_name, ROI_volume, network_volume_or_PAF, network_length, network_SA, branchpoints, endpoints, lengths.shape[0], segment_partitioning]
    
    ## Segment characteristics
    avg_radius = np.mean(radii_avgs)
    avg_length = np.mean(lengths)
    
    avg_tortuosity = np.mean(tortuosities)
    
    # Average volume/PAF of each segment
    if image_dim == 3:
        avg_volume_or_PAF = np.mean(volumes_or_PAFs)
    elif image_dim == 2:
        avg_volume_or_PAF = np.mean(volumes_or_PAFs) if image_shape else 'NA' # For 2D graphs
    
    avg_SA = np.mean(surface_areas)
    
    segment_features = [avg_radius, avg_length, avg_tortuosity, avg_volume_or_PAF, avg_SA]
    
    # Add current results to our results list.
    results = network_features + segment_features
    
    ## Distributions
    # Find histogram of radii distributions    
    bins = np.arange(0, 22)
    bins[21] = 500
    radii_bins = np.histogram(radii_avgs, bins)[0]
    # Add these histogram values to our results.
    results += radii_bins.tolist()
            
    # Create tortuosity and length bins 
    tortuosity_bins = [''] * 21
    length_bins = [''] * 21
    SA_bins = [''] * 21
    
    # Find mean tortuosity & lengths of vessels in bins.
    for i in range(21):
        locations = np.argwhere((radii_avgs >= bins[i]) & (radii_avgs < bins[i+1])).transpose()[0]
        if len(locations) > 0:
            tortuosity_bins[i] = np.sum(tortuosities[locations]) / len(locations)
            length_bins[i] = np.sum(lengths[locations]) / len(locations)
            SA_bins[i] = np.sum(surface_areas[locations]) / len(locations)
    
    results += length_bins + tortuosity_bins + SA_bins
    segment_results = None
    if save_seg_results:
        ids = np.arange(0, volumes_or_PAFs.shape[0])
        segment_results = np.array([ids, volumes_or_PAFs, lengths, surface_areas, tortuosities,
                                    radii_avgs, radii_maxes, radii_mins, radii_SD]).T.tolist()
    if verbose:
        print (f"Feature extraction completed in {pf() - t1:0.2f} seconds.")
        
    return results, segment_results