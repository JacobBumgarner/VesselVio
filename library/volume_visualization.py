"""
The volume visualization page, built entirely with PyVista.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from multiprocessing import cpu_count
from time import perf_counter as pf

import matplotlib
import matplotlib.pyplot as plt
import mcubes
import numpy as np
import pyvista as pv

from library import helpers, input_classes as IC, volume_processing as VolProc
from numba import njit, prange


############################
### Volume Visualization ###
############################
@njit()
def init_filters():
    North = [0, 1, 1]
    South = [2, 1, 1]
    East = [1, 1, 2]
    West = [1, 1, 0]
    Up = [1, 0, 1]
    Down = [1, 2, 1]
    return np.array([West, East, Down, Up, South, North]) - 1


@njit(parallel=True, fastmath=True)
def find_borders(volume, volume_points):
    shape = len(volume_points)
    filters = init_filters()
    border_filter = np.full(volume_points.shape[0], False)
    for i in range(6):
        o = filters[i]
        for n in prange(shape):
            z, y, x = volume_points[n]
            if not volume[z + o[0], y + o[1], x + o[2]]:
                border_filter[n] = True
    return border_filter


@njit()
def identify_nonzero(volume):
    points = np.vstack(np.nonzero(volume)).T
    return points


# Original view and smoothed view generation.
def vol_plot(
    volume,
    g,
    build_original,
    build_smoothed,
    status_updater=None,
    subdivide=True,
    verbose=False,
):

    if status_updater:
        status_updater.emit(["Preparing volume for visualization...", 70])

    if verbose:
        t = pf()
        print("Preparing volume for visualization...", end="\r")

    # Find coordinates of all of the structures to keep in the volume.
    clusters = g.components()
    keep_coords = []
    for c in clusters:
        keep_coords.append(g.vs[c[0]]["v_coords"])

    # For visualization purposes, filter the deleted segments' voxels
    keep_coords = np.array(keep_coords, dtype=np.int_)
    volume = VolProc.filter_volume(volume, keep_coords)

    if verbose:
        print(f"Volume filtering completed in {pf() - t:0.2f} seconds.")

    # Build our original volume.
    # PyVista plots in x,y,z, so run a transpose to swap the axes.
    volume = volume.T
    original_mesh = None

    if build_original:
        if status_updater:
            status_updater.emit(["Generating original volume...", 70])

        volume_points = identify_nonzero(volume)
        border_filter = find_borders(volume, volume_points)
        border_points = volume_points[border_filter]

        original_pd = pv.PolyData(border_points)
        original_mesh = original_pd.glyph(geom=pv.Cube())

    # Build smoothed volume
    # Get isosurface from the scalar volume using marching cubes.
    smoothed_mesh = None
    if build_smoothed:
        if status_updater:
            status_updater.emit(["Generating smoothed volume...", 70])

        verts, faces = mcubes.marching_cubes(volume, 0)

        length = len(faces)
        insert = np.full((length, 1), 3)
        faces = np.append(insert, faces, 1)
        faces = faces.astype(int)

        # Get the smoothed volume.
        isosurface = pv.PolyData(verts, faces=faces)

        if subdivide:
            divided = isosurface.subdivide(1, subfilter="butterfly")
            smoothed = divided.smooth(
                n_iter=75, relaxation_factor=0.05, boundary_smoothing=True
            )
            smoothed_mesh = smoothed.smooth(
                n_iter=20, relaxation_factor=0.15, boundary_smoothing=True
            )
        else:
            smoothed_mesh = isosurface.smooth()

    return original_mesh, smoothed_mesh


##########################
### Tube Visualization ###
##########################
# 0, 1, 2; 0 highest, 2 lowest
def get_rendering_features(rendering_quality):
    if rendering_quality == 0:
        n_sides, theta_phi, tube_points = 20, 30, 8
    elif rendering_quality == 1:
        n_sides, theta_phi, tube_points = 10, 20, 4
    elif rendering_quality == 2:
        n_sides, theta_phi, tube_points = 5, 10, 2
    return n_sides, theta_phi, tube_points


def add_line_attributes(line, e, annotation):
    line["Radius"] = [e["radius_avg"]]
    line["Length"] = [e["length"]]
    line["Tortuosity"] = [e["tortuosity"]]
    line["Volume"] = [e["volume"]]
    line["Surface Area"] = [e["surface_area"]]

    if annotation:
        line["Original_RGB"] = [e["original_rgb"]]
        line["Shifted_RGB"] = [e["shifted_rgb"]]
        line["Rainbow_RGB"] = [e["rainbow_rgb"]]
        line["ids"] = [e["ROI_ID"]]

    return line


# Step bins. Includes starting number.
# Distribute points along bins from left to right until gone
def construct_interpolation_bins(radii, points):
    intp_bins = np.ones(len(radii) - 1, dtype=np.int_)
    i = 0
    points -= len(radii)
    while points > 0:
        intp_bins[i] += 1

        points -= 1
        i = i + 1 if i < intp_bins.shape[0] - 1 else 0
    return intp_bins


def normalize_radii(radii):
    mean = np.full(radii.shape[0], np.mean(radii))
    radii = mean + ((radii - mean) / mean) / 3
    return radii


# Interpolate the radii based on contrusted interpolation bins
def interpolate_radii(radii, points):
    intp_bins = construct_interpolation_bins(radii, points)
    intp_radii = np.zeros(points)

    start = 0
    stop = 0
    for i in range(len(radii) - 1):
        stop += intp_bins[i]
        intp_radii[start:stop] = np.linspace(
            radii[i], radii[i + 1], intp_bins[i], endpoint=False
        )
        start = stop
    intp_radii[-1] = radii[-1]
    return intp_radii


def update_radii_end_caps(g, e, radii):
    for v in [e.source, e.target]:
        r_location = (
            0
            if np.sum(np.abs(g.vs[v]["v_coords"] - e["coords_list"][0])) < 0.001
            else -1
        )
        if g.degree(v) == 1:
            g.vs[v]["end_radius"] = radii[r_location]
        else:
            g.vs[v]["branch_radius"].append(radii[r_location])
    return


# Detailed graph view
def create_splines(bottom, top):
    network_tubes = []
    scaled_tubes = []

    for s in segments[bottom:top]:
        interpolation = min(s["coords_list"].shape[0] * tube_points, 500)
        line = pv.Spline(s["coords_list"], interpolation)

        # Create tubes
        line = add_line_attributes(line, s, add_annotations)
        if construct_network:
            # Network tube
            network_tube = line.tube(radius=0.7, n_sides=tube_sides, capping=False)
            network_tubes.append(network_tube)

        # Scaled tube, first get vis radii, interpolate them, then set as size
        if construct_scaled:
            scaled_tube = line.tube(
                radius=s["vis_radius"], n_sides=tube_sides, capping=False
            )
            scaled_tubes.append(scaled_tube)

    return [network_tubes, scaled_tubes]


# Create simplified graphs
def create_lines(bottom, top):
    network_tubes = []
    scaled_tubes = []

    for s in segments[bottom:top]:
        source = g.vs[s.source]["v_coords"]
        target = g.vs[s.target]["v_coords"]
        line = pv.Line(source, target)

        # Create tubes
        line = add_line_attributes(line, s, add_annotations)

        if construct_network:
            # Network tube
            # Capping must be on for the annotations to work, not sure why
            network_tube = line.tube(radius=0.7, n_sides=tube_sides)
            network_tubes.append(network_tube)

        if construct_scaled:
            # Scaled tube
            scaled_tube = line.tube(radius=s["vis_radius"], n_sides=tube_sides)
            scaled_tubes.append(scaled_tube)

    return [network_tubes, scaled_tubes]


def tube_creation_io(graph, network, scaled, annotations, graph_type, graph_reduction):
    global g, segments, construct_network, construct_scaled, add_annotations
    g = graph
    construct_network = network
    construct_scaled = scaled
    add_annotations = annotations

    network_tubes = []
    scaled_tubes = []

    segments = g.es()
    seg_count = len(segments)
    workers = cpu_count()
    if helpers.unix_check() and g.ecount() > workers:
        if graph_type == "Branches" or graph_reduction:
            results = helpers.multiprocessing_input(
                create_lines, seg_count, workers, sublist=True
            )
        else:
            results = helpers.multiprocessing_input(
                create_splines, seg_count, workers, sublist=True
            )

        for result in results:
            network_tubes.extend(result[0])
            scaled_tubes.extend(result[1])

    else:
        if graph_type == "Branches" or graph_reduction:
            network_tubes, scaled_tubes = create_lines(0, seg_count)
        else:
            network_tubes, scaled_tubes = create_splines(0, seg_count)

    return network_tubes, scaled_tubes


# Tube mesh generation for our dataset. Based on undirected graph.
def graph_plot(meshes, g, graph_type, vis_options, status_updater):
    # Prep the options
    reduce_graph = vis_options.load_simplified
    build_network = vis_options.load_network
    build_scaled = vis_options.load_scaled
    render_annotations = vis_options.render_annotations

    # Rendering quality option:
    global tube_sides, theta_phi, tube_points
    tube_sides, theta_phi, tube_points = get_rendering_features(
        vis_options.rendering_quality
    )

    # Z,Y,X -> X,Y,Z
    points = np.array(g.vs["v_coords"])
    points[:, [0, 2]] = points[:, [2, 0]]
    if len(points) == 0:
        return
    g.vs["v_coords"] = points

    if render_annotations:
        # send graph to the helpers function to add shifted and rainbow colors
        g = helpers.annotation_colorization_input(g, meshes)

    ## Tube construction
    if status_updater:
        status_updater.emit(["Generating tubes...", 70])
    network_tubes, scaled_tubes = tube_creation_io(
        g, build_network, build_scaled, render_annotations, graph_type, reduce_graph
    )

    if build_network:
        network = pv.MultiBlock(network_tubes)
        network = network.combine()
        network = network.extract_surface()
        meshes.network = network

    if build_scaled:
        scaled = pv.MultiBlock(scaled_tubes)
        scaled = scaled.combine()
        scaled = scaled.extract_surface()
        meshes.scaled = scaled

    ## End caps
    if status_updater:
        status_updater.emit(["Generating end points...", 70])

    size = g.vcount()
    radii = np.zeros(size)
    lengths = np.zeros(size)
    tortuosities = np.zeros(size)
    volumes = np.zeros(size)
    surface_areas = np.zeros(size)
    vis_radii = np.zeros(size)

    if add_annotations:
        original_colors = []
        shifted_colors = []
        rainbow_colors = []
        cap_ids = []

        end_original_RGB = []
        end_shifted_RGB = []
        end_rainbow_RGB = []
        end_ids = []

        branches_original_RGB = []
        branches_shifted_RGB = []
        branches_rainbow_RGB = []
        branch_ids = []

    end_locations = []
    branch_locations = []

    ## Build end caps
    for i, v in enumerate(g.vs()):
        edges = g.es[g.incident(v)]
        max_r_loc = np.argmax(edges["radius_avg"])

        radii[i] = edges["radius_avg"][max_r_loc]
        lengths[i] = edges["length"][max_r_loc]
        tortuosities[i] = edges["tortuosity"][max_r_loc]
        surface_areas[i] = edges["surface_area"][max_r_loc]
        volumes[i] = edges["volume"][max_r_loc]
        vis_radii[i] = edges["vis_radius"][max_r_loc]

        if add_annotations:
            original_colors.append([edges["original_rgb"][max_r_loc]])
            shifted_colors.append([edges["shifted_rgb"][max_r_loc]])
            rainbow_colors.append([edges["rainbow_rgb"][max_r_loc]])
            cap_ids.append([edges["ROI_ID"][max_r_loc]])

        # Index end points and branch points
        if v.degree() == 1:
            end_locations.append(i)
            if add_annotations:
                end_original_RGB.append([edges["original_rgb"][max_r_loc]])
                end_shifted_RGB.append([edges["shifted_rgb"][max_r_loc]])
                end_rainbow_RGB.append([edges["rainbow_rgb"][max_r_loc]])
                end_ids.append([edges["ROI_ID"][max_r_loc]])

        elif v.degree() > 2:
            branch_locations.append(i)
            if add_annotations:
                branches_original_RGB.append([edges["original_rgb"][max_r_loc]])
                branches_shifted_RGB.append([edges["shifted_rgb"][max_r_loc]])
                branches_rainbow_RGB.append([edges["rainbow_rgb"][max_r_loc]])
                branch_ids.append([edges["ROI_ID"][max_r_loc]])

    coords = np.array(g.vs["v_coords"])

    # End cap mesh creation
    cap_pd = pv.PolyData(coords)
    cap_pd["Radius"] = radii
    cap_pd["Length"] = lengths
    cap_pd["Tortuosity"] = tortuosities
    cap_pd["Volume"] = volumes
    cap_pd["Surface Area"] = surface_areas

    if add_annotations:
        cap_pd["Original_RGB"] = original_colors
        cap_pd["Shifted_RGB"] = shifted_colors
        cap_pd["Rainbow_RGB"] = rainbow_colors
        cap_pd["ids"] = cap_ids

    # Network endcaps
    if build_network:
        meshes.network_caps = cap_pd.glyph(
            geom=pv.Sphere(
                radius=0.7, theta_resolution=theta_phi, phi_resolution=theta_phi
            ),
            scale=None,
        )

    # Scaled endcaps
    if build_scaled:
        cap_pd["size"] = vis_radii
        cap_pd.set_active_scalars("size")
        meshes.scaled_caps = cap_pd.glyph(
            geom=pv.Sphere(
                radius=1, theta_resolution=theta_phi, phi_resolution=theta_phi
            ),
            scale=True,
        )

    ## End points
    if status_updater:
        status_updater.emit(["Generating end and branch point identifiers...", 70])
    end_pd = pv.PolyData(coords[end_locations])

    if add_annotations:
        end_pd["Original_RGB"] = end_original_RGB
        end_pd["Shifted_RGB"] = end_shifted_RGB
        end_pd["Rainbow_RGB"] = end_rainbow_RGB
        end_pd["ids"] = end_ids

    # Network
    if build_network:
        meshes.network_ends = end_pd.glyph(
            geom=pv.Sphere(
                radius=1.15, theta_resolution=theta_phi, phi_resolution=theta_phi
            )
        )
    # Scaled
    if build_scaled:
        end_pd["size"] = vis_radii[end_locations] * 1.15
        end_pd.set_active_scalars("size")
        meshes.scaled_ends = end_pd.glyph(
            geom=pv.Sphere(
                radius=1, theta_resolution=theta_phi, phi_resolution=theta_phi
            ),
            scale=True,
        )

    ## Branch points
    branch_pd = pv.PolyData(coords[branch_locations])

    if add_annotations:
        branch_pd["Original_RGB"] = branches_original_RGB
        branch_pd["Shifted_RGB"] = branches_shifted_RGB
        branch_pd["Rainbow_RGB"] = branches_rainbow_RGB
        branch_pd["ids"] = branch_ids

    # Network
    if build_network:
        meshes.network_branches = branch_pd.glyph(
            geom=pv.Sphere(
                radius=1.3, theta_resolution=theta_phi, phi_resolution=theta_phi
            )
        )
    # Scaled
    if build_scaled:
        branch_pd["size"] = vis_radii[branch_locations] * 1.2
        branch_pd.set_active_scalars("size")
        meshes.scaled_branches = branch_pd.glyph(
            geom=pv.Sphere(
                radius=1, theta_resolution=theta_phi, phi_resolution=theta_phi
            ),
            scale=True,
        )
    return meshes


# Loading dock for mesh generation.
def mesh_construction(
    graph,
    vis_options,
    volume=None,
    graph_type="Centerlines",
    iteration=0,
    application=False,
    status_updater=None,
    verbose=False,
):
    tic = pf()
    meshes = IC.PyVistaMeshes()
    if verbose:
        print("Plotting dataset...", end="\r")

    if volume is not None and vis_options.load_smoothed or vis_options.load_original:
        if verbose:
            print("Preparing volume...", end="\r")
        meshes.original, meshes.smoothed = vol_plot(
            volume,
            graph,
            vis_options.load_original,
            vis_options.load_smoothed,
            status_updater,
            verbose=verbose,
        )

    if vis_options.load_network or vis_options.load_scaled:
        if verbose:
            print("Preparing splines...", end="\r")
        meshes = graph_plot(meshes, graph, graph_type, vis_options, status_updater)

    if application:
        return meshes

    if not vis_options.create_movie:
        p = pv.Plotter(multi_samples=8, window_size=[2928, 1824], off_screen=True)
    else:
        # p = pv.Plotter(window_size=[1800,1800],lighting='light_kit')
        p = pv.Plotter(lighting="light_kit")

    if verbose:
        print("Loading meshes...      ", end="\r")
    cmap = plt.cm.get_cmap(vis_options.cmap)

    if vis_options.load_scaled:
        p.add_mesh(
            meshes.scaled,
            scalars=vis_options.scalars,
            smooth_shading=True,
            cmap=cmap,
            rgb=vis_options.render_annotations,
        )
        p.add_mesh(
            meshes.scaled_caps,
            scalars=vis_options.scalars,
            smooth_shading=True,
            cmap=cmap,
            rgb=vis_options.render_annotations,
        )
        if vis_options.show_branches:
            p.add_mesh(meshes.scaled_branches, color="orange", smooth_shading=True)
        if vis_options.show_ends:
            p.add_mesh(meshes.scaled_ends, color="red", smooth_shading=True)

    elif vis_options.load_network:
        p.add_mesh(
            meshes.network,
            scalars=vis_options.scalars,
            smooth_shading=True,
            cmap=cmap,
            rgb=vis_options.render_annotations,
        )
        p.add_mesh(
            meshes.network_caps,
            scalars=vis_options.scalars,
            smooth_shading=True,
            cmap=cmap,
            rgb=vis_options.render_annotations,
        )

        if vis_options.show_branches:
            p.add_mesh(meshes.network_branches, color="red", smooth_shading=True)
        if vis_options.show_ends:
            p.add_mesh(meshes.network_ends, color="yellow", smooth_shading=True)
    if vis_options.load_original:
        p.add_mesh(meshes.original)
    if vis_options.load_smoothed:
        p.add_mesh(meshes.smoothed, smooth_shading=True)

    if vis_options.create_movie:
        if verbose:
            print(f"Loading completed in {pf() - tic:0.2f} seconds.")
            print("Creating movie now...")

        # Prepare the movie
        if vis_options.movie_title:
            title = str(vis_options.movie_title) + ".mp4"
        else:
            title = "movie.mp4"
        path = p.generate_orbital_path(factor=5, n_points=60, viewup=vis_options.viewup)
        if iteration == 0:
            p.show(auto_close=False)

        p.open_movie(title)
        p.orbit_on_path(path, write_frames=True, viewup=vis_options.viewup, step=0.001)
        p.close()
        if verbose:
            print(f"Movie created in {pf() - tic:0.2f} seconds.")

    else:

        def toggle_camera(state):
            p.screenshot("/Users/jacobbumgarner/Desktop/Processed.png")
            print(p.camera_position)

        p.add_checkbox_button_widget(toggle_camera, value=False)

        if verbose:
            print(f"Plotting completed in {pf() - tic:0.2f} seconds.")

        light = pv.Light(light_type="headlight", intensity=0.1)
        p.add_light(light)
        p.show()

    return
