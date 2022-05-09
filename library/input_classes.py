"""
Input classes used to carry options for the various components of the pipeline.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os

from library import helpers


class VisualizationFiles:
    def __init__(
        self,
        dataset_type="Volume",
        file1=None,
        file2=None,
        annotation_data=None,
        annotation_type="None",
        visualized=None,
    ):
        self.dataset_type = dataset_type
        self.file1 = file1
        self.file2 = file2
        self.annotation_data = annotation_data
        self.annotation_type = annotation_type
        self.visualized_file = visualized

    def clear(self):
        for item in self.__dict__:
            self.__dict__[item] = None
        self.annotation_type = "None"

    def file1_name(self):
        return os.path.basename(self.file1) if self.file1 else "None"

    def file2_name(self):
        if self.file2:
            if os.path.isdir(self.file2):
                return self.file2
            elif os.path.isfile(self.file2):
                return os.path.basename(self.file2)
        else:
            return "None"

    def clear_annotation(self):
        self.file2 = None
        self.annotation_type = "None"
        self.annotation_data = None


class AnalysisOptions:
    def __init__(
        self,
        results_folder,
        resolution,
        prune_length,
        filter_length,
        max_radius,
        save_segment_results,
        save_graph,
        image_dimensions=3,
    ):
        self.results_folder = results_folder
        self.resolution = resolution
        self.prune_length = prune_length
        self.filter_length = filter_length
        self.max_radius = max_radius
        self.save_seg_results = save_segment_results
        self.save_graph = save_graph
        self.image_dimensions = image_dimensions
        self.graph_file = False


class VisualizationOptions:
    def __init__(
        self,
        visualize,
        load_simplified,
        load_scaled,
        load_network,
        load_original,
        load_smoothed,
        scalars="Radius",
        cmap="viridis",
        show_branches=False,
        show_ends=False,
        create_movie=False,
        movie_title=None,
        viewup=[1, 1, 1],
        render_annotations=False,
        rendering_quality=0,
    ):
        # Rendering options
        self.visualize = visualize
        self.load_simplified = load_simplified
        self.rendering_quality = (
            rendering_quality  # 0, 1, 2 (0 best, 2 worst based on index of combo box)
        )

        # Mesh construction instructions
        self.load_scaled = load_scaled
        self.load_network = load_network
        self.load_original = load_original
        self.load_smoothed = load_smoothed

        # Scalar options
        self.scalars = scalars
        self.cmap = cmap
        self.render_annotations = render_annotations

        # VVT options
        self.show_branches = show_branches
        self.show_ends = show_ends
        self.create_movie = create_movie
        self.movie_title = movie_title
        self.viewup = viewup


class AnnotationOptions:
    def __init__(
        self, annotation_filepath, atlas_filepath, annotation_type, annotation_regions
    ):
        self.annotation_file = annotation_filepath
        self.annotation_atlas = atlas_filepath
        self.annotation_type = annotation_type
        self.annotation_regions = annotation_regions


class GraphOptions:
    def __init__(
        self,
        file_format="GraphML",
        graph_type=None,
        clique_filtering=None,
        centerline_smoothing=None,
        attribute_key=None,
        delimiter=None,
    ):
        self.file_format = file_format.lower()
        self.graph_type = graph_type  # Either Centerlines or Branches
        self.filter_cliques = clique_filtering
        self.smooth_centerlines = centerline_smoothing
        self.a_key = attribute_key
        self.delimiter = delimiter


class AttributeKey:
    def __init__(
        self,
        X,
        Y,
        Z,
        vertex_radius,
        edge_radius,
        length,
        volume,
        surface_area,
        tortuosity,
        edge_source,
        edge_target,
        vis_radius=None,
        edge_hex=None,
    ):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.vertex_radius = vertex_radius
        self.radius_avg = edge_radius
        self.length = length
        self.volume = volume
        self.surface_area = surface_area
        self.tortuosity = tortuosity
        self.edge_source = edge_source
        self.edge_target = edge_target
        self.vis_radius = vis_radius
        self.edge_hex = edge_hex


#####################
### Movie Classes ###
#####################
class MovieOptions:
    def __init__(self, path, resolution, fps, frame_count, camera_path):
        self.filepath = path
        self.resolution = resolution
        self.fps = fps
        self.frame_count = frame_count
        self.camera_path = camera_path


class PyVistaMeshes:
    def __init__(
        self,
        network=None,
        network_caps=None,
        network_branches=None,
        network_ends=None,
        scaled=None,
        scaled_caps=None,
        scaled_branches=None,
        scaled_ends=None,
        original=None,
        smoothed=None,
        id_hex_dict=None,
    ):

        # Network tubes
        self.network = network
        self.network_caps = network_caps
        self.scaled = scaled
        self.scaled_caps = scaled_caps

        # Branches/Ends
        self.network_branches = network_branches
        self.network_ends = network_ends
        self.scaled_branches = scaled_branches
        self.scaled_ends = scaled_ends

        # Volumes
        self.original = original
        self.smoothed = smoothed

        # Annotation colors stored for randomization
        self.id_hex_dict = id_hex_dict

        self.vessels = [
            self.network,
            self.network_caps,
            self.network_branches,
            self.network_ends,
            self.scaled,
            self.scaled_caps,
            self.scaled_branches,
            self.scaled_ends,
        ]

    def iter_vessel_meshes(self):
        vessels = [
            self.network,
            self.network_caps,
            self.network_branches,
            self.network_ends,
            self.scaled,
            self.scaled_caps,
            self.scaled_branches,
            self.scaled_ends,
        ]
        return vessels

    def update_vessel_scalars(self, scalar):
        if self.network:
            self.network.set_active_scalars(scalar)
            self.network_caps.set_active_scalars(scalar)
        if self.scaled:
            self.scaled.set_active_scalars(scalar)
            self.scaled_caps.set_active_scalars(scalar)
        return

    def update_branch_scalars(self, scalar):
        if self.network:
            self.network_branches.set_active_scalars(scalar)
        if self.scaled:
            self.scaled_branches.set_active_scalars(scalar)

    def update_end_scalars(self, scalar):
        if self.network:
            self.network_ends.set_active_scalars(scalar)
        if self.scaled:
            self.scaled_ends.set_active_scalars(scalar)

    def reset(self):
        items = list(self.__dict__.keys())
        for item in items:
            del self.__dict__[item]
            self.__dict__[item] = None


class PyVistaActors:
    def __init__(
        self, vessels=None, vessel_caps=None, branches=None, ends=None, volume=None
    ):

        # Network tubes
        self.vessels = vessels
        self.vessel_caps = vessel_caps

        # Branches/Ends
        self.branches = branches
        self.ends = ends

        # Volumes
        self.volume = volume

    def iter_actors(self):
        for item in self.__dict__:
            yield (self.__dict__[item])

    def iter_vessels(self):
        for item in self.__dict__:
            if item != "volume":
                yield (self.__dict__[item])

    def destroy_vessel_actors(self, plotter):
        for key in ["vessels", "vessel_caps", "branches", "ends"]:
            actor = self.__dict__[key]
            if actor:
                helpers.remove_legend(plotter, actor)
                plotter.remove_actor(actor, reset_camera=False)
                self.__dict__[actor] = None

    def destroy_volume_actors(self, plotter):
        if self.volume:
            self.volume = None
            helpers.remove_legend(plotter, self.volume)
            plotter.remove_actor(self.volume, reset_camera=False)

    def reset(self):
        items = list(self.__dict__.keys())
        for item in items:
            del self.__dict__[item]
            self.__dict__[item] = None


##############
### Movies ###
##############
class OrbitActors:
    def __init__(
        self, path=None, path_direction=None, camera=None, lens=None, camera_legs=None
    ):
        self.path = path
        self.path_direction = path_direction
        self.camera = camera
        self.lens = lens
        self.camera_legs = camera_legs
        return

    def iter_actors(self):
        for item in self.__dict__:
            yield (self.__dict__[item])

    def reset_actors(self):
        items = list(self.__dict__.keys())
        for item in items:
            del self.__dict__[item]
            self.__dict__[item] = None


class FlyThroughActors:
    """An object class used to hold the PyVista actors that help the user
    visualize the path that their flythrough movie will follow.

    Parameters
    ----------
    path_glyph: PyVista.UnstructuredGrid, optional

    returns: FlyThroughActors
    """

    def __init__(self, path_direction=None, start_sphere=None, end_sphere=None):
        self.path_direction = path_direction
        self.start_sphere = start_sphere
        self.end_sphere = end_sphere

    def iter_actors(self):
        for item in self.__dict__:
            yield (self.__dict__[item])

    def reset_actors(self):
        items = list(self.__dict__.keys())
        for item in items:
            del self.__dict__[item]
            self.__dict__[item] = None


class MovieExportOptions:
    def __init__(self, movie_type, key_frames):
        self.movie_type = movie_type
        self.key_frames = key_frames
