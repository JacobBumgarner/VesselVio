
"""
Preconstructed graph input and output
Copyright © 2021, Jacob Bumgarner
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright © 2021 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


from os import path, mkdir, remove
import pandas

import igraph as ig
import numpy as np

from Library import Feature_Extraction as FeatExt
from Library import helpers


###########################
### Loading graph files ###
###########################
## iGraph compatible file formats
# Base graph construction for v and e graphs.
def construct_base_graph(raw_g, a_key):
    g = ig.Graph()
    g.add_vertices(raw_g.vcount())
    
    # Add edges to the graph
    edges = np.zeros((raw_g.ecount(), 2), dtype=int)
    
    for i in range(raw_g.ecount()):
        edges[i] = raw_g.es[i].tuple
    g.add_edges(edges)
    
    # Add vertex coordinates to the graph
    X = raw_g.vs[a_key.X]
    Y = raw_g.vs[a_key.Y]
    Z = raw_g.vs[a_key.Z]
    
    coords = np.stack([Z, Y, X], axis=1)
    g.vs['v_coords'] = coords

    return g

## Construct a vertex-based graph
def build_vert_graph(raw_g, a_key, resolution, Visualize=False):
    g = construct_base_graph(raw_g, a_key)    
    
    # Add radius features. The rest are calculated by the program for now.
    radii = np.array(raw_g.vs[a_key.vertex_radius])
    g.vs['v_radius'] = radii
    
    if Visualize:
        vis_radii = radii/np.min(resolution)
        g.vs['vis_radius'] = vis_radii
    else:
        g.vs['vis_radius'] = 0
            
    return g


## Construct an edge-based graph
def build_edge_graph(raw_g, a_key, resolution, Visualize=False):
    g = construct_base_graph(raw_g, a_key)  
    
    ## Populate our new graph with the features
    # Add radius features
    radii = np.array(raw_g.es[a_key.radius_avg])
    g.es['radius_avg'] = radii
        
    if Visualize:
        vis_radii = radii / np.min(resolution)
        g.es['vis_radius'] = vis_radii
    else:
        g.es['vis_radius'] = 0
    
    # Length
    g.es['length'] = raw_g.es[a_key.length]
    
    # Tortuosity
    if a_key.tortuosity:
        g.es['tortuosity'] = raw_g.es[a_key.tortuosity]
    else:
        g = FeatExt.egraph_tortuosity_calc(g, resolution)
    
    # Volume
    if a_key.volume:
        g.es['volume'] = raw_g.es[a_key.volume]
    else:
        g = FeatExt.egraph_volume_calc(g)
    
    # Surface Area
    if a_key.surface_area:
        g.es['surface_area'] = raw_g.es[a_key.surface_area]
    else:
        surf_areas = FeatExt.egraph_sa_calc(g)
        g.es['surface_area'] = surf_areas
        
    if a_key.edge_hex:
        # rgb = [helpers.hex_to_rgb(hex) for hex in raw_g.es[a_key.edge_hex]]
        g.es['hex'] = raw_g.es[a_key.edge_hex]
        if 'ROI_ID' in raw_g.es.attributes():
            g.es['ROI_ID'] = raw_g.es['ROI_ID']
    
    return g


## CSV Loading
# Load vertex information
def load_csv_vertices(filename, delimiter, graph_type, a_key, resolution, Visualize=False):
    data = pandas.read_csv(filename, delimiter=delimiter)
    # Construct graph and add vertices with their coords.
    g = ig.Graph()
    g.add_vertices(len(data))
    
    X = data[a_key.X]
    Y = data[a_key.Y]
    Z = data[a_key.Z]
    
    coords = np.stack([Z, Y, X], axis=1)
    g.vs['v_coords'] = coords
        
    if graph_type == 'Centerlines':     
        radii = data[a_key.vertex_radius]
        g.vs['v_radius'] = radii
        
        if Visualize:
            vis_radii = radii / np.min(resolution)
            g.vs['vis_radius'] = vis_radii
        else:
            g.vs['vis_radius'] = 0
    
    return g


def load_csv_edges(g, filename, delimiter, graph_type, a_key, resolution, Visualize=False):
    data = pandas.read_csv(filename, delimiter=delimiter)
    sources = data[a_key.edge_source]
    targets = data[a_key.edge_target]
    
    edges = np.stack([sources, targets], axis=1)
    g.add_edges(edges)
    
    # Populate edge if edge-based graph
    if graph_type == 'Branches':
        # Average Radius
        radii = np.array(data[a_key.radius_avg])
        g.es['radius_avg'] = radii
        if Visualize:
            g.es['vis_radius'] = radii / np.min(resolution)
        else:
            g.es['vis_radius'] = 0
        
        # Length
        g.es['length'] = data[a_key.length]
        
        # Tortuosity 
        if a_key.tortuosity:
            g.es['tortuosity'] = data[a_key.tortuosity]
        else:
            g = FeatExt.egraph_tortuosity_calc(g, resolution, sources, targets)
            
        # Volume
        if a_key.volume:
            g.es['volume'] = data[a_key.volume]
        else:
            g = FeatExt.egraph_volume_calc(g)
            
        # Surface area
        if a_key.surface_area:
            g.es['surface_area'] = data[a_key.surface_area]
        else:
            g = FeatExt.egraph_sa_calc(g)

        if a_key.edge_hex:
            # rgb = [helpers.hex_to_rgb(hex) for hex in data[a_key.edge_hex]]
            g.es['hex'] = data[a_key.edge_hex]

    return g
        

# Basepath for constructing csv graphs.
def construct_csv_graph(filename, g_options, resolution, Visualize=False):
    
    # Load vertices
    g = load_csv_vertices(filename['Vertices'], g_options.delimiter, g_options.graph_type, g_options.a_key, resolution, Visualize=Visualize)
    
    # Load edges
    g = load_csv_edges(g, filename['Edges'], g_options.delimiter, g_options.graph_type, g_options.a_key, resolution, Visualize=Visualize)

    return g
        
        
# Remove isolated vertices from our graph 
def delete_isolated(g):
    isolated = g.vs.select(_degree = 0)
    g.delete_vertices(isolated)
    return g

## Main loading dock for graph processing
def graph_loading_dock(filename, g_options, resolution, Visualize=False):
    if g_options.file_format != 'csv':
        raw_g = ig.load(filename)
        
        if g_options.graph_type == 'Centerlines':
            g = build_vert_graph(raw_g, g_options.a_key, resolution, Visualize=Visualize)
                            
        elif g_options.graph_type == 'Branches':
            g = build_edge_graph(raw_g, g_options.a_key, resolution, Visualize=Visualize) 

    elif g_options.file_format == 'csv':
        g = construct_csv_graph(filename, g_options, resolution, Visualize=Visualize)
                
    # Filter isolated vertices
    g = delete_isolated(g)

    return g

 
##########################
### Saving graph files ###
##########################
def save_graph(g, filename, results_dir, main_thread=True, caching=False, verbose=False):
    if verbose:
        print ("Saving graph...", end='\r')
        
    if not g.vs():
        return
    
    # Save Coords as XYZ values
    points = np.array(g.vs['v_coords'])
    g.vs['X'] = points[:, 2]
    g.vs['Y'] = points[:, 1]
    g.vs['Z'] = points[:, 0]
    
    # Get rid of unneeded attributes
    if main_thread:
        del(g.vs['v_radius'])
        del(g.vs['vis_radius'])
    del(g.es['radii_list'])
    del(g.es['coords_list'])
    del(g.vs['v_coords'])
    
    if caching:
        return g
    
    # Get the dir and name for our graph.
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    results_dir = path.join(results_dir, 'Graphs')
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    file = path.join(results_dir, filename + '.' + 'graphml')
    
    # save the graph
    g.write(file)
    
    return

def save_cache(filename, results_dir):
    # Get the dir and name for our graph.
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    results_dir = path.join(results_dir, 'Graphs')
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    
    # Get the cached result
    g = ig.read(helpers.get_graph_cache())
    remove(helpers.get_graph_cache())
    
    # save the graph
    file = path.join(results_dir, filename + '.' + 'graphml')
    g.write(file)
    
    return

def cache_graph(graph):
    cache_path = helpers.get_graph_cache()
    if path.isfile(cache_path):
        g = ig.read(cache_path)
    
    else:
        g = ig.Graph()
        
    g += graph
    
    g.write(cache_path)
    
    return

###############
### Testing ###
###############
if __name__ == '__main__':
    vertices = '/Users/jacobbumgarner/Desktop/synthetic_graph_1/1_b_3_0/1_b_3_0_nodes_processed.csv'
    edges = '/Users/jacobbumgarner/Desktop/synthetic_graph_1/1_b_3_0/1_b_3_0_edges_processed.csv'
    
    filename = {'Vertices': vertices, 'Edges':edges, 'Delimiter': ';'}
    format = 'graphml'
    eorv_graph = 'Edge'
    a_key = {# Vertices
             'X': 'pos_x', 'Y':'pos_y', 'Z':'pos_z', 
             'Radius':'avgRadiusAvg',
             # Edges
             'Source':'node1id', 'Target':'node2id',
             'Length':'length', 'Tortuosity':'curveness',
             'Volume':'volume', 'Surface Area':None
             }
    resolution = np.array([1,1,1])
    graph_loading_dock(filename, 'csv', eorv_graph, a_key, resolution, verbose=True)