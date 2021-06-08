# -*- coding: utf-8 -*-

import numpy as np
from time import perf_counter, sleep

# Volume Visualization packages
import pyvista as pv
from pyvistaqt import BackgroundPlotter
import vtk
from vtk import vtkWindowedSincPolyDataFilter
import mcubes
import matplotlib.pyplot as plt

from Library import Feature_Extraction as featext

# Tube mesh generation for our dataset. Based on undirected graph.
def py_plot(graph, resolution, verbose=False):
    g = graph
    segment_ids = g.vs.select(_degree_lt = 3)
    gsegs = g.subgraph(segment_ids)
    segments = gsegs.clusters()
    
    # for v in g.vs():
    #     z, y, x = v["v_coords"]
    #     coords = np.array([x, y, z])
    #     v["v_coords"] = coords
    
    if verbose:
        print ("Preparing splines...")
    
    # Network and scaled view spline blocks.
    network_view = pv.MultiBlock()
    scaled_view = pv.MultiBlock()
    
    # Prepare lists for our endpoint and branchpoint glyphs
    segcap_coords = []
    segend_rad_scalar = []
    segend_scaled_rad = []
    segend_len = []
    segend_tort = []
    seg_branchcoords = []
    seg_branchradii = []
    seg_endcoords = []
    seg_endradii = []
        
    for segment in segments:
        seg_size = len(segment)
        
        ## Point lists
        # Prepare point list for single-vertex segments
        if seg_size == 1:
            coords_list, radii_list, segment_length, avg_radius, tortuosity, end_degrad = featext.small_segs(g, gsegs, segment, segment_ids, Visualization=True)
        
        # Prepare point list for two-vertex segments.
        elif seg_size > 1:
            coords_list, radii_list, segment_length, avg_radius, tortuosity, end_degrad = featext.large_segs(g, gsegs, segment, segment_ids, Visualization=True)    
                
        ## Load our segment information into the spline and glyph meshes.
        try:
            ## Make the segment splines. This chooses the number of spline points for smoother viewing.
            factor = 1
            if segment_length < 5:
                factor = 40
            elif segment_length < 20:
                factor = 20
            elif segment_length < 40:
                factor = 10
            elif segment_length < 60:
                factor = 5
            elif segment_length < 100:
                factor = 3
            else:
                factor = 2
            
            interpolation = int(segment_length * factor) # How many points total to render.
            spline = pv.Spline(coords_list, interpolation)
            # spline = pv.Spline(coords_list)
            # Prepare our scalars
            segment_length *= resolution
            radius = avg_radius * resolution
            tortuosity = tortuosity.astype('float32') # Need to type match this for later.
            spline['Length'] = [segment_length]
            spline['Radius'] = [radius]
            spline['Tortuosity'] = [tortuosity]
                        
            ## TODO Vary radius of vessels? Cost-benefit...
            # radii_list = np.array(radii_list) # Create interpolated range for new points.
            
            # Network objects         
            network_spline = spline.tube(radius=0.7, capping=False)
            network_view.append(network_spline)
                        
            # Scaled objects
            # Make the tube
            n_sides = 20
            if avg_radius > 4: # 3:
                n_sides = 40
            
            scaled_spline = spline.tube(radius=avg_radius, n_sides=n_sides, capping=False)
            scaled_view.append(scaled_spline)
            
            # Add points to our endcap & BEs glyphs.
            for i in range(-1, 1):
                segend_len.append(segment_length)
                segend_rad_scalar.append(radius)
                segend_scaled_rad.append(avg_radius)
                segend_tort.append(tortuosity)
                segcap_coords.append(coords_list[i])
                
                # Add to our branch/end glyphs
                if end_degrad[i][0] == 1:
                    seg_endcoords.append(coords_list[i])
                    scaled_radius = avg_radius * 1.15
                    seg_endradii.append(scaled_radius)
                else:
                    seg_branchcoords.append(coords_list[i])
                    scaled_radius = avg_radius * 1.2
                    seg_branchradii.append(scaled_radius)
            
        except:
            if verbose:
                print ("Couldn't add segment:")
                print (coords_list)
    
    ## Find 2-vert segments between branchpoints
    bif_ids = g.vs.select(_degree_gt = 2)
    gbifs = g.subgraph(bif_ids)
    
    for e in gbifs.es():
        v1 = gbifs.vs[e.source]
        v2 = gbifs.vs[e.target]
        avg_radius = (v1['v_radius'] + v2['v_radius']) / 2
        #Downsize a bit here because the avgs are higher than the surrounding segments, typically. Makes visualization offputting.
        spline = pv.Line(v1['v_coords'], v2['v_coords'])
        
        # Make the scalars
        length = e['edge_length'] * resolution
        radius = avg_radius * resolution
        a = np.array([1], dtype=np.float32)
        tortuosity = a[0] #Can't mix types 
        spline['Length'] = [length]
        spline['Radius'] = [radius]
        spline['Tortuosity'] = [tortuosity]
        
        # Make the tube        
        avg_radius /= 1.25 # Reduce the size of these segments for visualization purposes, as they can overpower other averaged segments.     
        if avg_radius < 0.5:
            avg_radius = 0.5
        network_spline = spline.tube(radius=0.7)
        scaled_spline = spline.tube(radius=avg_radius, capping=False)

        # Add spline to our splines multiblock.
        network_view.append(network_spline)
        scaled_view.append(scaled_spline)
        
        # Add endcaps to our endcap multiglyph.
        for i in range(2):
            segend_len.append(length)
            segend_rad_scalar.append(radius)
            segend_scaled_rad.append(avg_radius)
            segend_tort.append(1)
            
            # And add points to our branchpoints multiglyph
            scaled_radius = avg_radius * 1.5
            seg_branchradii.append(scaled_radius) 
        segcap_coords.append(v1['v_coords'])
        segcap_coords.append(v2['v_coords'])
        seg_branchcoords.append(v1['v_coords'])
        seg_branchcoords.append(v2['v_coords'])

    ## Create glyphed datases from our != 2 verts.    
    ## Network
    # Caps
    nc_pd = pv.PolyData(segcap_coords)
    nc_pd['Length'] = segend_len
    nc_pd['Radius'] = segend_rad_scalar
    nc_pd['Tortuosity'] = segend_tort
    network_caps = nc_pd.glyph(geom=pv.Sphere(radius=0.7), scale=None)
    
    # Branches
    nb_pd = pv.PolyData(seg_branchcoords)
    network_branches = nb_pd.glyph(geom=pv.Sphere(radius=1.2))

    # Ends
    ne_pd = pv.PolyData(seg_endcoords)
    network_ends = ne_pd.glyph(geom=pv.Sphere(radius=1.0))
    
    ## Scaled
    # Caps
    sc_pd = pv.PolyData(segcap_coords)
    sc_pd['Length'] = segend_len
    sc_pd['Radius'] = segend_rad_scalar
    sc_pd['size'] = segend_scaled_rad
    sc_pd['Tortuosity'] = segend_tort
    sc_pd.set_active_scalars('size')
    scaled_caps = sc_pd.glyph(geom=pv.Sphere(radius=1,phi_resolution=45, theta_resolution=45), scale=True)
    
    # Branches
    sb_pd = pv.PolyData(seg_branchcoords)
    sb_pd['Radius'] = seg_branchradii
    sb_pd.set_active_scalars('Radius')
    scaled_branches = sb_pd.glyph(geom=pv.Sphere(radius=1), scale=True)
    
    # Ends
    se_pd = pv.PolyData(seg_endcoords)
    se_pd['Radius'] = seg_endradii
    se_pd.set_active_scalars('Radius')
    scaled_ends = se_pd.glyph(geom=pv.Sphere(radius=1), scale=True)
   
    # Combine our multiblock of PolyData into a single unstructured grid. 
    # This creates a single actor rather than n=#segments actors.
    # See my question here: https://github.com/pyvista/pyvista-support/issues/420
    # Thanks to G.Favelier
    network_view = network_view.combine()
    network_view = network_view.extract_surface()
    scaled_view = scaled_view.combine()
    scaled_view = scaled_view.extract_surface()
    
    return network_view, network_caps, network_branches, network_ends, scaled_view, scaled_caps, scaled_branches, scaled_ends
    
# Smoothing function for our marching cubes.
def vtk_smooth(poly, n_iter, angle = 45, band = 0.1):
    smoother = vtkWindowedSincPolyDataFilter()
    smoother.SetInputData(poly)
    smoother.SetNumberOfIterations(n_iter)
    smoother.BoundarySmoothingOn()
    smoother.SetFeatureAngle(angle)
    smoother.SetEdgeAngle(angle)
    smoother.SetPassBand(band)
    smoother.NormalizeCoordinatesOn()
    smoother.Update()
    
    return smoother.GetOutput()    

# Orignal view and smoothed view generation.
def vol_plot(volume, subdivide=True, verbose=False):
    t1 = perf_counter()
    
    # Build our original volume.
    
    volume_points = np.where(volume == 1)
    volume_points = np.array((volume_points[0],volume_points[1],volume_points[2])).T
    border_points = []
    for point in volume_points:
        z, y, x = point
        if np.sum(volume[z-1:z+2, y-1:y+2, x-1:x+2]) < 27:
            border_points.append([z, y, x])


    original_mesh = pv.PolyData(border_points)
    original_mesh_geom = pv.Cube()
    original_volume = original_mesh.glyph(geom=original_mesh_geom)

    # Build our isosurface
    # Get isosurface from the scalar volume using marching cubes.
    verts, faces = mcubes.marching_cubes(volume, 0)
    
    length = len(faces)
    insert = np.full((length, 1), 3)
    faces = np.append(insert, faces, 1)
    faces = faces.astype(int)
    
    if verbose:
        print (f"Marching: {perf_counter - t1}")
    
    # Get the smoothed volume.
    isosurface = pv.PolyData(verts, faces=faces)
    
    if subdivide:
        divided = isosurface.subdivide(1, subfilter='butterfly')
        smoothed = vtk_smooth(divided, 20, 25, 0.01)
        
    else:
        smoothed = vtk_smooth(isosurface, 20, 25, 0.01)
    
    
    return original_volume, smoothed 

# Loading dock for mesh generation.
def generate(graph, volume, resolution=1, app=False, gen_tubes=True, gen_volume=True, movie=True, verbose=False, title=None, iteration=0):
    t1 = perf_counter()
    if verbose:
        print ("Plotting dataset...")
    
    if gen_volume:
        original_volume, smoothed_volume = vol_plot(volume, verbose)
    
    if gen_tubes:
        network_view, network_caps, network_branches, network_ends, scaled_view, scaled_caps, scaled_branches, scaled_ends = py_plot(graph, resolution, verbose)
               
    if not app: 
        if movie == True:
            print ("Loading mesh...")
            cmap_theme = plt.cm.get_cmap('jet')
            plotter = pv.Plotter(multi_samples=4,window_size=[2928, 1824])
            plotter.add_mesh(scaled_caps, scalars='Radius', smooth_shading=False, show_scalar_bar=False, pickable=False, clim=[1.35, 20],cmap=cmap_theme)
            actor = plotter.add_mesh(scaled_view,scalars='Radius',smooth_shading=False, show_scalar_bar=False, pickable=False,clim=[1.35, 20], cmap=cmap_theme)
            mapper = actor.GetMapper()
            plotter.scalar_bars.add_scalar_bar(vertical=False, title='Radius (µm)', mapper=mapper, n_colors=256,
                                               position_x=0.55, width=0.4)#width=0.4, position_x=0.55)  # x = 0.93, w = 0.05, title_font_size=40, label_font_size=36
            # plotter.add_mesh(network_branches, color='orange', smooth_shading=True)
            # plotter.add_mesh(original_volume, opacity=0.2, ambient=0.1, specular=0, diffuse=1, color='#C6C6C6', smooth_shading=True)
            # plotter.add_mesh(smoothed_volume, opacity=0.3, diffuse=1)
            # print (f"Loading completed in {perf_counter() - t1:0.2f} seconds.")
            viewup = [0,-1,0]
            if title is not None:
                title = str(title) + '.mov'
            else: 
                title = 'movie.mov'
            path = plotter.generate_orbital_path(factor=3, n_points=360, viewup=viewup)
            # if iteration == 0:
            #     plotter.show(auto_close=False)
            # plotter.show(auto_close=False)
            plotter.open_movie(title)
            plotter.orbit_on_path(path, step=0.001, write_frames=True, viewup=viewup)
            plotter.close()
            
        else:            
            if verbose:
                print ("Loading meshes...")
            p = pv.Plotter()
            # p = BackgroundPlotter()
            # actor = p.add_mesh(scaled_view, scalars='Radius', smooth_shading=True, show_scalar_bar=False)
            # p.add_mesh(scaled_caps, scalars='Radius',smooth_shading=True, show_scalar_bar=False)
            # p.add_mesh(scaled_branches, color='red', smooth_shading=True)
            # p.add_mesh(scaled_ends, color='yellow',smooth_shading=True)
            p.add_mesh(network_view, scalars='Radius', smooth_shading=True)
            p.add_mesh(network_caps, scalars='Radius', smooth_shading=True)
            p.add_mesh(network_branches, color="red", smooth_shading=True)
            p.add_mesh(network_ends, color="yellow", smooth_shading=True)
            # p.add_mesh(smoothed_volume, opacity=0.4)
            # p.add_mesh(original_volume,ambient=0.3, specular=0.0, diffuse=1, color='white', show_edges=True)
            print (f"Plotting completed in {perf_counter() - t1:0.2f} seconds.")
            # print (p.camera.position)
            def toggle_camera(state):
                print (p.camera_position)
            p.add_checkbox_button_widget(toggle_camera, value=False)
            p.camera_position = (
[(0.7584925030221868, 13.23658967224327, 29.986160657137223),
 (14.122056176190235, 12.285297664792594, 31.509275827728032),
 (0.06578280115286594, 0.9968004281005257, 0.04540407042426071)])      # mapper = actor.GetMapper()
            # p.scalar_bars.add_scalar_bar(mapper = mapper, title='Radius (µm)')
            # plotter.app.exec()
            p.show()
                        
        return

    else:
        if gen_tubes and gen_volume:
            meshes = [original_volume, smoothed_volume, 
                      network_view, network_caps, network_branches, network_ends, 
                      scaled_view, scaled_caps, scaled_branches, scaled_ends]
            return meshes
        
        elif gen_tubes and not gen_volume:
            meshes = [None, None, 
                      network_view, network_caps, network_branches, network_ends, 
                      scaled_view, scaled_caps, scaled_branches, scaled_ends]
            return meshes
        else:
            meshes = [original_volume, smoothed_volume, 
                      None, None, None, None, 
                      None, None, None, None]
            return meshes

