# -*- coding: utf-8 -*-

from enum import unique
import igraph as ig
import numpy as np
import time

from Library import Feature_Extraction as featext

from os import path, mkdir

from numba import njit


## Save graph files
def save_graph(g, points, filename, results_dir):
    # Get the dir and name for our graph.
    filename = path.splitext(path.basename(filename))[0]
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    results_dir = path.join(results_dir, 'Graphs')
    if path.exists(results_dir) == False:
        mkdir(results_dir)
    file = path.join(results_dir, filename + '.' + 'graphml')
    
    # We can't save our numpy coordinates into a graphml file
    # So we convert the to a list
    points = points.tolist()
    g.vs['v_coords'] = points
    g.write_graphml(file)

## Scanning orientations and dimension analyzer for edge detection.
def orientations(skeleton):
    # Prepration for edge point analysis. Directional edge detection based on C. Kirst's algorithm.
    z_dim, y_dim, x_dim = skeleton.shape #Redundant, but saves some text later on.
    shape = np.array((z_dim, y_dim, x_dim))
    
    # Matrix preparation for edge detetction
    # Point of interest rests at [1,1,1] in 3x3x3 array.
    scan = np.array(
    [[0, 2, 2],
    [1, 2, 2],
    [2, 2, 2],
    [0, 2, 1],
    [1, 2, 1],
    [2, 2, 1], # End of top slice
    [0, 1, 2],
    [1, 1, 2],
    [2, 1, 2],
    [2, 1, 1], # End of middle slice
    [0, 0, 2],
    [1, 0, 2],
    [2, 0, 2]]) # End of bottom slice
        

    for coords in scan:
        coords -= 1

    return scan, shape

## Simple array for length of edges in 3D space.
def edge_distances():
    edge_distance = np.array([[[0, 1],
                               [1, 1.4142135623730951]],
                              [[1, 1.4142135623730951],
                               [1.4142135623730951, 1.7320508075688772]]])
    
    return edge_distance

## Edge Detection
@njit
def identify_edges(skeleton, points, spaces, dimensions, edge_distance):    
    points = points
    edges = []
    edgelens = []
    
    vertex_index = np.zeros((dimensions[0]+1, dimensions[1]+1, dimensions[2]+1))
    
    # A 3D array that contains the index number of vertices at the point's at the element's location. Fast.
    for i, location in enumerate(points):
        vertex_index[location[0],location[1],location[2]] = int(i)
   
    
    for i, location in enumerate(points):
        z,y,x = location
        for coords in spaces:
            # Identifies edges of all voxels, border and not.
            if (z + coords[2] >= 0 and z + coords[2] < dimensions[0] 
            and y + coords[1] >= 0 and y + coords[1] < dimensions[1] 
            and x + coords[0] >= 0 and x + coords[0] < dimensions[2]):
                if vertex_index[z + coords[2], y + coords[1], x + coords[0]] > 0: 
                    target_index = int(vertex_index[z + coords[2], y + coords[1], x + coords[0]])
                    edge = (i, target_index)
                    edges.append(edge)  
                    
                    target_location = np.array([z + coords[2], y + coords[1], x + coords[0]])
                    delta = np.abs(location - target_location)
                    distance = edge_distance[delta[0], delta[1], delta[2]]
                    edgelens.append(distance)
    
    return edges, edgelens

## Clique Filtering
# I understand that this function is too large and ideally should call smaller functions.
# I started building it and ended up too deep to try to change it.
# Perhaps in the future if I have more time, this can be optimized. It's definitely a speed bottleneck, as I couldn't figure out how to parallelize it.

def filter_cliques(g, iteration):
    def f1(x):
        return x[1]
        
    g = g   
    cnum = [0] * 13
    
    # Remove 'cliques' from branchpoint connections
    # First, find branchpoints (vertices with > 2 edges) and create first subgraph.
    # New index of gsub acts as a relative index for bifurcations.
    bifurcations = g.vs.select(_degree_gt = 2)
    gsub = g.subgraph(bifurcations)
    # bifurcations = list(bifurcations)
    
    # We do a second pruning of these bifurcations to remove 1-edge vertices from cliques.
        # This "pruned" index acts as an index for the bifurcations, i.e., index of the index. Two layers deep now, so v = g.vs[bifurcation.vs[pruned.vs[n].index].index]
        # This wipes out multiple redundant classes of cliques that can be eliminated by the removal of 1-edge vertices.
        # E.g. reduces class 2 appearance drastically.
    pruned = gsub.vs.select(_degree_gt = 1)
    gsub = gsub.subgraph(pruned)

    # Identify components of subgraph. All cliques will have > 2 components.
    cliques = gsub.clusters()
    
    # Images of clique classes can be found ## TODO
    clique_count = [0]
    to_delete = []
    
    def small_filter(vertex):
        two_deg = []
        neighbors = gsub.neighbors(vertex)
        for n in neighbors:
            if gsub.degree(n) == 2:
                two_deg.append(n)
        if len(two_deg) == 2:
            candidates = []
            candidates.append([vertex, gsub.vs[vertex]["v_radius"]])
            for i in range(2):
                candidates.append([two_deg[i], gsub.vs[two_deg[i]]["v_radius"]])
            candidates = sorted(candidates, key=f1)
            if candidates[2][1] == candidates[1][1]:
                neighborhoods = [[]] * 3
                neighborhoods[0] = g.neighbors(bifurcations[candidates[0][0]].index)
                neighborhoods[1] = g.neighbors(bifurcations[candidates[1][0]].index)
                neighborhoods[2] = g.neighbors(bifurcations[candidates[0][0]].index)
                
                for i in range(3):
                    for n in neighborhoods[i]:
                        candidates[i][1] += g.vs[n]["v_radius"]     
                candidates = sorted(candidates, key=f1)
            if gsub.are_connected(candidates[0][0], candidates[1][0]):
                to_delete.append((bifurcations[pruned[candidates[0][0]].index].index,
                                    bifurcations[pruned[candidates[1][0]].index].index))

    def filter(i):    
        clique = cliques[i]
        clique_size = len(clique)
        
        # Selecting for cliques, not short chains of bifurcations. Redundant, but acts as a sanity check.
        if clique_size > 2:
            degrees = gsub.degree(clique)
            clique_count[0] += 1
            
            min_deg = min(degrees)
            max_deg = max(degrees)
            
            # Filters up class 1 cliques based on size and neighborhood weight.
            if clique_size == 3 and min_deg > 1:
                cnum[0] += 1
                
                # Extract radii values from our vertices.
                v0r = gsub.vs[clique[0]]["v_radius"]
                v1r = gsub.vs[clique[1]]["v_radius"]
                v2r = gsub.vs[clique[2]]["v_radius"]
                
                # Find the number of unique radii to learn how to deal with clique.
                radii = np.array([v0r, v1r, v2r])
                unique_values = np.unique(radii)
                
                clique_dict = {clique[0]:v0r,
                                clique[1]:v1r,
                                clique[2]:v2r}

                clique_dict = sorted(clique_dict.items(),key=f1) # Sorts the dict based on the vertex radii.
                clique_dict = [list(v_r) for v_r in clique_dict] # List of tuples -> list of lists
                
                # Easiest subclass - delete the edge between two smallest vertices.
                # Based on heirarchy of vessel sizes.
                # if len(unique_values) == 3:
                #         to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                    
                # # Next subclass - find the weights of the two largest candidate branchpoints.
                # # Delete the spurious edge between the lowest weighted candidate and the smallest vertex.
                # elif len(unique_values) == 2:
                #     neighborhoods = [[]] * 2
                #     neighborhoods[0] = g.neighbors(bifurcations[pruned[clique_dict[1][0]].index].index)
                #     neighborhoods[1] = g.neighbors(bifurcations[pruned[clique_dict[2][0]].index].index)
                             
                #     # Add neighbor weights to the radius weight. 
                #     # Within-clique weights are included, but we already have duplicates so this doesn't matter.
                #     # e.g. v0r=1, v1r=2, v2r=2. wv1r=5, wv2r=5 The neighbor weights matter now.
                #     for i in range(2):
                #         for n in neighborhoods[i]:
                #             clique_dict[i+1][1] += g.vs[n]["v_radius"]       
                    
                #     clique_dict = sorted(clique_dict, key=f1)
                    
                #     # Remove edges between the lowest weighted candidates.
                #     to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                    
                # # Most expensive subclass.
                # # Fine the weights of all three candidates. Then, delete the edges between the smallest two candidates.
                # # If the candidates have 2-3 similarities, the edge between the first two candidates in the weight-sorted list is deleted.
                # else:
                neighborhoods = [[]] * 3
                neighborhoods[0] = g.neighbors(bifurcations[clique_dict[0][0]].index)
                neighborhoods[1] = g.neighbors(bifurcations[clique_dict[1][0]].index)
                neighborhoods[2] = g.neighbors(bifurcations[clique_dict[2][0]].index)
                
                for i in range(3):
                    for n in neighborhoods[i]:
                        clique_dict[i][1] += g.vs[n]["v_radius"]
                    
                clique_dict = sorted(clique_dict, key=f1)
                
                to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, 
                                    bifurcations[pruned[clique_dict[1][0]].index].index))
        
            # Filters up class 2-4 cliques
            if clique_size == 4:
                # Filters class 2 cliques.
                if min_deg == 1 and max_deg == 3:
                    cnum[1] += 1
                    candidates = []
                    for vertex in clique:
                        if gsub.degree(vertex) > 1:
                            candidates.append([vertex, gsub.vs[vertex]["v_radius"]])
                        
                    candidates = sorted(candidates, key=f1)
                    # If there is a largest candidate, delete edge between the smallest two.
                    if candidates[2][1] > candidates [1][1]:
                        to_delete.append((bifurcations[pruned[candidates[0][0]].index].index,
                                            bifurcations[pruned[candidates[1][0]].index].index))
                    else:
                        neighborhoods = [[]] * 3
                        neighborhoods[0] = g.neighbors(bifurcations[candidates[0][0]].index)
                        neighborhoods[1] = g.neighbors(bifurcations[candidates[1][0]].index)
                        neighborhoods[2] = g.neighbors(bifurcations[candidates[2][0]].index)
                        for i in range(3):
                            for n in neighborhoods[i]:
                                candidates[i][1] += g.vs[n]["v_radius"]
                        candidates = sorted(candidates, key=f1)
                        to_delete.append((bifurcations[pruned[candidates[0][0]].index].index,
                                            bifurcations[pruned[candidates[1][0]].index].index))
                                            
                # Filters class 3 cliques by size of 3-branch vertices.
                elif min_deg == 2 and max_deg == 3:
                    cnum[2] += 1
                    candidates = []
                    for vertex in clique:
                        candidate = None
                        if gsub.degree(vertex) == 3:
                            candidate = [vertex, gsub.vs[vertex]["v_radius"]]
                        if candidate:
                            candidates.append(candidate)
                    # If r0 is bigger, candidate 1 is removed, and vice versa.
                    if candidates[0][1] > candidates[1][1]:
                        togo = candidates[1][0]
                    elif candidates[1][1] > candidates[0][1]:
                        togo = candidates[0][0]
                        
                    # If the candidates are the same, weight them based on their neighborhood radii.
                    # The largest weight wins. 
                    else:
                        neighborhoods = [[]] * 2
                        neighborhoods[0] = g.neighbors(bifurcations[pruned[candidates[0][0]].index].index)
                        neighborhoods[1] = g.neighbors(bifurcations[pruned[candidates[1][0]].index].index)
                        
                        for i in range(2):
                            for n in neighborhoods[i]:
                                candidates[i][1] += g.vs[n]["v_radius"]
                        
                        candidates = sorted(candidates, key=f1)

                        # Select the smallest candidate (or first in list if identical weights) for spurious edge deletion. 
                        togo = candidates[0][0]
                    
                    # Delete the spurious edges to the selected candidate from the 2-degree clique vertices.
                    for vertex in clique:
                        if gsub.degree(vertex) == 2:
                            # Needed to ensure connection, prevents unnecesary crashes from non-class 3 cliques that get through the filter.
                            if gsub.are_connected(vertex, togo):
                                to_delete.append((bifurcations[pruned[togo].index].index, bifurcations[pruned[vertex].index].index))
                
                # Deals with class 4 cliques by maintaining edges only to the largest candidate.
                if min_deg == 3 and max_deg == 3:
                    cnum[3] += 1
                    v0r = gsub.vs[clique[0]]["v_radius"]
                    v1r = gsub.vs[clique[1]]["v_radius"]
                    v2r = gsub.vs[clique[2]]["v_radius"]
                    v3r = gsub.vs[clique[3]]["v_radius"]
                    
                    # Find the number of unique radii to learn how to deal with clique.
                    radii = np.array([v0r, v1r, v2r, v3r])
                    unique_values = np.unique(radii)
                    
                    clique_dict = {clique[0]:v0r,
                                    clique[1]:v1r,
                                    clique[2]:v2r,
                                    clique[3]:v3r}
                    
                    clique_dict = sorted(clique_dict.items(),key=f1) # Sorts the dict based on the vertex radii.
                    # Convert list of tuples into list of lists.
                    # Keeping dict tag because it is a 'modified' dict.
                    clique_dict = [list(v_r) for v_r in clique_dict]
                   
                    # As long as there are more than one different sizes of radii, we can identify our largest candidate for proper deletion.
                    if len(unique_values) != 1:
                        # Determine whether we have a single largest radius.
                        # If so, this is the easiest subclass - delete edges between smallest radii.
                        if clique_dict[2][1] != clique_dict[3][1]:
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[1][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                            
                        # If we have two large radii, we compare their weights.
                        # After weight comparison, we delete spurious edges from the lowest weighted candidate.
                        elif clique_dict[2][1] != clique_dict[1][1]:
                            neighborhoods = [[]] * 2
                            neighborhoods[0] = g.neighbors(bifurcations[clique_dict[2][0]].index)
                            neighborhoods[1] = g.neighbors(bifurcations[clique_dict[3][0]].index)
                            
                            # Add neighbor weights
                            for i in range(2):
                                for n in neighborhoods[i]:
                                    clique_dict[i+2][1] += g.vs[n]["v_radius"]
                            
                            # Sort dict to find lowest 3 removals.
                            clique_dict = sorted(clique_dict, key=f1)
                            
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[1][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                        
                        # If there are three candidate radii, we identify the weights.
                        # This implementation deletes the smallest weighted candidate OR the first smallest weighted candidate.
                        else:
                            neighborhoods = [[]] * 3
                            neighborhoods[0] = g.neighbors(bifurcations[clique_dict[1][0]].index)
                            neighborhoods[1] = g.neighbors(bifurcations[clique_dict[2][0]].index)
                            neighborhoods[2] = g.neighbors(bifurcations[clique_dict[3][0]].index)
                            
                            for i in range(3):
                                for n in neighborhoods[i]:
                                    clique_dict[i+1][1] += g.vs[n]["v_radius"]                        
                                    
                            clique_dict = sorted(clique_dict, key=f1)
                            
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                            to_delete.append((bifurcations[pruned[clique_dict[1][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                    
                    # If all of our candidate vertices share identical radii, we run a similar process as above.
                    # We delete the edges between the smallest weighted vertex OR the edges of the first in our small-weight list.
                    else:
                        neighborhoods = [[]] * 4
                        neighborhoods[0] = g.neighbors(bifurcations[clique_dict[0][0]].index)
                        neighborhoods[1] = g.neighbors(bifurcations[clique_dict[1][0]].index)
                        neighborhoods[2] = g.neighbors(bifurcations[clique_dict[2][0]].index)
                        neighborhoods[3] = g.neighbors(bifurcations[clique_dict[3][0]].index)

                        for i in range(4):
                            for n in neighborhoods[i]:
                                clique_dict[i][1] += g.vs[n]["v_radius"]
                            
                        clique_dict = sorted(clique_dict, key=f1)
                        
                        to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[1][0]].index].index))
                        to_delete.append((bifurcations[pruned[clique_dict[0][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))
                        to_delete.append((bifurcations[pruned[clique_dict[1][0]].index].index, bifurcations[pruned[clique_dict[2][0]].index].index))

            # Filters up class 5-12 and h1 cliques based on centrality.
            elif clique_size > 4 and clique_size < 11:                
                # Prunes class 5  cliques by pruning spurious edges of outer cliques based on radius weighting.
                if clique_size == 6 and min_deg == 2 and max_deg == 3:
                    cnum[4] += 1               
                    for vertex in clique:
                        if gsub.degree(vertex) == 3:
                            small_filter(vertex)
                        ## Older method
                        ## Delete 2-2 edges

                # Filters class 6 & 7 cliques
                elif clique_size == 5 and max_deg == 4:
                    # Filters class 6 cliques based on radius of mini-cliques
                    # Keeps branchpoint status of 4-degree point.
                    if min_deg == 2:
                        cnum[5] += 1
                        blacklist = [] # Blacklist to avoid adding duplicate edges for deletion.
                        for vertex in clique:
                            if vertex in blacklist:
                                continue
                            if gsub.degree(vertex) == 2:
                                candidates = []
                                neighbors = gsub.neighbors(vertex)
                                if len(neighbors) == 2:
                                    candidates = []
                                    candidates.append([vertex, gsub.vs[vertex]["v_radius"]])
                                    for i in range(2):
                                        blacklist.append(neighbors[i]) # Add neighbors to blacklist. This will only affect 2-degree neighbors
                                        candidates.append([neighbors[i], gsub.vs[neighbors[i]]["v_radius"]])
                                    candidates = sorted(candidates, key=f1)
                                    if candidates[2][1] == candidates[1][1]:
                                        neighborhoods = [[]] * 3
                                        neighborhoods[0] = g.neighbors(bifurcations[candidates[0][0]].index)
                                        neighborhoods[1] = g.neighbors(bifurcations[candidates[1][0]].index)
                                        neighborhoods[2] = g.neighbors(bifurcations[candidates[0][0]].index)
                                        
                                        for i in range(3):
                                            for n in neighborhoods[i]:
                                                candidates[i][1] += g.vs[n]["v_radius"]     
                                        candidates = sorted(candidates, key=f1)
                                    to_delete.append((bifurcations[pruned[candidates[0][0]].index].index,
                                                    bifurcations[pruned[candidates[1][0]].index].index))
                                                                         
                    # Filters class 7 cliques based on degree of connectivity
                    else:
                        cnum[6] += 1
                        for vertex in clique:
                            if gsub.degree(vertex) != 4:
                                neighbors = gsub.neighbors(vertex) # Returns the neighbors.
                                for neighbor in neighbors:
                                    # Remove spurious edge.
                                    if gsub.degree(neighbor) != 4:
                                        if gsub.are_connected(vertex, neighbor):
                                            gsub.delete_edges([(vertex, neighbor)])
                                            to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))
                
                # Filters class 8 cliques based on centrality. Needs a second iteration to entirely correct clique.
                elif max_deg == 4 and min_deg == 1:
                    cnum[7] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 3:
                            neighbors = gsub.neighbors(vertex) # Returns the neighbors.
                            for neighbor in neighbors:
                                # Remove spurious edge.
                                if gsub.degree(neighbor) != 4:
                                    if gsub.are_connected(vertex, neighbor):
                                        gsub.delete_edges([(vertex, neighbor)])
                                        to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))
                
                # Filters class 9 cliques based on centrality. 
                # Converts into class 1/2 for deletion on second iteration.
                elif clique_size > 6 and clique_size < 10 and min_deg == 1:
                    cnum[8] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 3:
                            small_filter(vertex)
                        ## OLD
                        ## Delete 2-2 edges

                # Filters class 10 cliques based on centrality. Converts class 1/3 for removal on second iteration.
                elif clique_size > 8 and min_deg == 2:
                    cnum[9] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 3:
                            small_filter(vertex)
                            ## Old method
                            ## Delete 3-2
                            # neighbors = gsub.neighbors(vertex)
                            # for neighbor in neighbors:
                            #     if gsub.degree(neighbor) == 2:
                            #         gsub.delete_edges([(vertex, neighbor)])
                            #         to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))
    
                # Filters class 11 cliques.
                elif clique_size == 8 and max_deg == 4 and min_deg == 2:
                    cnum[10] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 2:
                            neighbors = gsub.neighbors(vertex) # Returns the neighbors.
                            for neighbor in neighbors:
                                # Remove spurious edge.
                                if gsub.degree(neighbor) == 2:
                                    if gsub.are_connected(vertex, neighbor):
                                        gsub.delete_edges([(vertex, neighbor)])
                                        to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))
                                        
                # Filters class 12 cliques based on centrality. Needs a 2nd iteration to completely remove. 
                elif clique_size == 7 and min_deg == 2:
                    cnum[11] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 2:
                            neighbors = gsub.neighbors(vertex) # Returns the neighbors.
                            for neighbor in neighbors:
                                # Remove spurious edge.
                                if gsub.degree(neighbor) == 2:
                                    if gsub.are_connected(vertex, neighbor):
                                        gsub.delete_edges([(vertex, neighbor)])
                                        to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))
                
                # Filters class 13 cliques to removed in 2nd iteration as class 1 cliques.
                elif clique_size == 6 and max_deg == 5:
                    cnum[12] += 1
                    for vertex in clique:
                        if gsub.degree(vertex) == 3:
                            neighbors = gsub.neighbors(vertex) # Returns the neighbors.
                            for neighbor in neighbors:
                                # Remove spurious edge.
                                if gsub.degree(neighbor) == 2:
                                    if gsub.are_connected(vertex, neighbor):
                                        gsub.delete_edges([(vertex, neighbor)])
                                        to_delete.append((bifurcations[pruned[vertex].index].index, bifurcations[pruned[neighbor].index].index))

                # Deals with class h1 cliques by size of 3-branch vertices. 
                # elif clique_size == 5 and min_deg == 1:
                #     candidates = []
                #     for vertex in clique: 
                #         if gsub.degree(vertex) == 3:
                #             candidates.append(vertex)
                #     scans = []
                    
                #     for i in candidates:
                #         scans.append([])
                    
                #     identifier = 2
                    
                #     for i in range(len(scans)):
                #         scans[i] = gsub.neighbors(candidates[i])
                    
                #     for num, scan in enumerate(scans):
                #         for v in scan:
                #             neighbors = gsub.neighbors(v)
                #             for neighbor in neighbors:
                #                 if gsub.degree(neighbor) == 1:
                #                     identifier = num
                            
                #     if identifier == 0:
                #         candidates[0] = candidates[-1]
                    
                #     elif identifier == 1:
                #         candidates[1] = candidates[-1]
                                            
                    
                #     r0 = gsub.vs[candidates[0]]["v_radius"]
                #     if len(candidates) > 1:
                #         r1 = gsub.vs[candidates[1]]["v_radius"]
                    
                #     # If r0 is bigger, candidate 1 is removed, and vice versa.
                #     if r0 > r1:
                #         togo = candidates[1]
                #     elif r1 > r0:
                #         togo = candidates[0]
                        
                #     # If the candidates are the same, weight them based on their neighborhood radii.
                #     # The larger weight wins. 
                #     else:
                #         r0ns = g.neighbors(bifurcations[pruned[candidates[0]].index].index)
                #         r1ns = g.neighbors(bifurcations[pruned[candidates[1]].index].index)
                        
                #         rweights = [0,0]
                        
                #         # Calculate the weights of the candidates.
                #         for n in r0ns:
                #             rweights[0] += g.vs[n]["v_radius"]
                #         for n in r1ns:
                #             rweights[1] += g.vs[n]["v_radius"]
                        
                #         # Select the smallest candidate for spurious edge deletion.
                #         if rweights[0] > rweights[1]:
                #             togo = candidates[0]
                #         elif rweights[0] < rweights[1]:
                #             togo = candidates[1]
                            
                #         # If our local neighborhood search fails, we filter the first candidate in our list.
                #         else:
                #             togo = candidates[0]
                    
                #     # Delete the spurious edges to the selected candidate from the 2-degree clique vertices.
                #     for vertex in clique:
                #         if gsub.degree(vertex) != 1:
                #             # Needed to ensure connection, prevents unnecesary crashes from non-class 3 cliques that get through the filter.
                #             if gsub.are_connected(vertex, togo):
                #                 gsub.delete_edges([(togo, vertex)])
                #                 to_delete.append((bifurcations[pruned[togo].index].index, bifurcations[pruned[vertex].index].index))
                #                 # g.delete_edges([(bifurcations[pruned[togo].index].index, bifurcations[pruned[vertex].index].index)])

    # Tried running this in parallel at one point but didn't have any success.
    # Longest I've seen it take is ~20s, but on average it's 2-3s/graph for filtering. 
    # Future implementation?
    [filter(i) for i in range(len(cliques))]
    g.delete_edges(to_delete)
    # print (cnum)
    return clique_count[0]

# Remove short connected endpoint segments from the main graph. 
# g, resolution, prune_length, verbose=False
def prune_endsegs(g, resolution, prune_length, verbose=False):
    # Because we need to prune before we do analysis, as this could alter the removal of small segments, 
    # We need to find a rough estimate of how long each segment is. Rather than generating a bspline for
    # Each segment in the graph and finding its length, we only find the bsplines for segments below our end filter.
    # We find the maximum segments needed for the prune length with our resolution size.
    end_filter = prune_length / resolution # Find number of verts needed for minimum size
    # dec = 1 - (end_filter % 1) # Round up.
    # if dec > 0:
    #     end_filter = int(end_filter + dec)
    
        
    segment_ids = g.vs.select(_degree_lt = 3) # Store ids of our segment vertices
    gsegs = g.subgraph(segment_ids)
    segments = gsegs.clusters() # Find segments)
    
    # Prune only the connected endpoints here. 
    # Isolated segments are pruned later with flood filling in volproc.
    vertices_togo = []
    pruned = 0
    for segment in segments:
        num_verts = len(segment)
        if num_verts <= end_filter:
            ends = 0
            togo = []
            # Isolate endpoint segments
            for vertex in segment:
                # Examine degree of each vertex.
                if gsegs.degree(vertex) < 2:
                    # If 1 or 0, check main graph degree.
                    if g.degree(segment_ids[vertex].index) == 1:
                        ends += 1
                if ends == 2:
                    break
            
            # If endpoint segment, calculate the size. 
            if ends == 1:
                # Send off to our feature extraction to find the size
                if num_verts == 1:
                    segment_length = featext.small_segs(g, gsegs, segment, segment_ids, pruning=True)
                
                elif num_verts > 1:
                    segment_length = featext.large_segs(g, gsegs, segment, segment_ids, pruning=True)
                        
                if segment_length < prune_length:    
                    pruned += 1
                    for vertex in segment:
                        togo.append(segment_ids[vertex].index)
                    vertices_togo.extend(togo)
    
    if verbose:
        print (f"Pruned {pruned} segments")
    g.delete_vertices(vertices_togo)
    
    

## Graph creation
def create_graph(skeleton, skeleton_radii, points, resolution, prune_length, verbose=False):
    if verbose: 
        print ("Creating Graph...")
    tic = time.perf_counter()
    
    # Create graph, populate graph with correct number of vertices.    
    g = ig.Graph()
    g.add_vertices(len(points))
    
    # Populate vertices with cartesian coordinates and radii
    g.vs["v_coords"] = points
    g.vs["v_radius"] = skeleton_radii
            
    # Detect edges and add them to the graph
    edge_distance = edge_distances()
    spaces, dimensions = orientations(skeleton)
        
    edges, edgelens = identify_edges(skeleton, points, spaces, dimensions, edge_distance)
    g.add_edges(edges)
    g.es["edge_length"] = edgelens

    
    # Filter spurious bifurcations. 
    # G will update without needing to be returned, as it is mutable.
    unfiltered_bifs = len(g.vs.select(_degree_gt = 2))
    if verbose:
        print ("Filtering cliques...")
    remaining_cliques = 0
    i = 0
    t1 = time.perf_counter()
    for i in range(5):
        clique_count = filter_cliques(g, i)
        
        if i == 0:
            total_cliques = clique_count
        
        if remaining_cliques == clique_count:
            if verbose:
                filtered_bifs = len(g.vs.select(_degree_gt = 2))
                t2 = time.perf_counter()
                print (f"Removed {unfiltered_bifs - filtered_bifs} spurious bifurcations from ", end='')
                if remaining_cliques > 0:
                    print (f"{total_cliques - remaining_cliques} cliques in {t2 - t1:0.2f} seconds.")
                    print (f"{remaining_cliques} unprocessed clique(s) remain.")
                    
                else: 
                    print (f"{total_cliques} identified cliques in {t2 - t1:0.2f} seconds.")
                
            break
            
        if i > 0:
            remaining_cliques = clique_count
    
    # Prune connected endpoint segments based on a user-defined length
    if prune_length > 0:
        prune_endsegs(g, resolution, prune_length, verbose=verbose) # G will update without a return. Stored as a mutable object.
        prune_endsegs(g, resolution, resolution, verbose=False)
    
    return g