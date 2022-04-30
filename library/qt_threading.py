"""
QThreads used to run the analysis and visualization pipelines for the GUI.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os

# from imageio import get_writer
from time import perf_counter as pf
from time import sleep

import igraph as ig
import nibabel
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from library import annotation_processing as AnnProc
from library import feature_extraction as FeatExt
from library import graph_io as GIO
from library import graph_processing as GProc
from library import helpers
from library import image_processing as ImProc
from library import input_classes as IC
from library import results_export as ResExp
from library import volume_processing as VolProc
from library import volume_visualization as VolVis


################
### Analysis ###
################
class VolumeThread(QThread):
    button_lock = pyqtSignal(int)
    selection_signal = pyqtSignal(int)
    analysis_status = pyqtSignal(list)

    def __init__(
        self, analysis_options, volume_files, annotation_files, annotation_data
    ):
        QThread.__init__(self)
        self.running = False
        self.gen_options = analysis_options
        self.volume_files = volume_files
        self.annotation_files = annotation_files
        self.annotation_data = annotation_data

    def run(self):
        # Prep the options and runtime variables
        self.running = True
        self.button_lock.emit(1)
        gen_options = self.gen_options
        volume_files = self.volume_files
        annotation_files = self.annotation_files
        annotation_data = self.annotation_data
        self.disk_space_error = 0

        # Make sure the resolution is in the proper format
        resolution = ImProc.prep_resolution(gen_options.resolution)

        if gen_options.annotation_type == "None":
            annotation_data = {None: None}
        elif gen_options.annotation_type == "RGB":
            ROI_array = AnnProc.prep_RGB_array(annotation_data)
        elif gen_options.annotation_type == "ID":
            ROI_array = AnnProc.prep_id_array(annotation_data)

        # Iterate through files
        for i, volume_file in enumerate(volume_files):
            tic = pf()
            file_analyzed = True  # Used to prevent overwriting errors

            for j, ROI_name in enumerate(annotation_data.keys()):
                speeds = []

                ## File initialization
                if self.running == False:
                    self.analysis_status.emit([i, "Canceled."])
                    break
                self.selection_signal.emit(i)
                self.analysis_status.emit(
                    [i, "Loading file...", f"{j}/{len(annotation_data.keys())}"]
                )

                filename = ImProc.get_filename(volume_file)

                #######
                speeds.append(filename)
                a = pf()
                #######

                ## Volume processing
                volume, image_shape = ImProc.load_volume(volume_file)
                if not ImProc.volume_check(volume, loading=True):
                    file_size = helpers.get_file_size(volume_file, GB=True)
                    self.analysis_status.emit([i, "Error: Unable to read image."])
                    file_analyzed = False
                    break

                if ROI_name:
                    ROI_id = j % 255
                    if j % 255 == 0:
                        if not helpers.check_storage(volume_file):
                            file_size = helpers.get_file_size(volume_file, GB=True)
                            self.analysis_status.emit(
                                [i, f"Error: Insufficient disk space"]
                            )
                            if file_size > self.disk_space_error:
                                self.disk_space_error = file_size
                            file_analyzed = False
                            break

                        self.analysis_status.emit([i, f"Labeling volume..."])
                        ROI_sub_array = ROI_array[j : j + 255]
                        ROI_volumes, minima, maxima = AnnProc.volume_labeling_input(
                            volume,
                            annotation_files[i],
                            ROI_sub_array,
                            gen_options.annotation_type,
                        )

                        if ROI_volumes is None:
                            self.analysis_status.emit([i, f"Error labeling volume..."])
                            file_analyzed = False
                            break

                    ROI_volume = ROI_volumes[ROI_id]
                    if ROI_volume > 0:
                        self.analysis_status.emit([i, f"Segmenting {ROI_name}..."])
                        point_minima, point_maxima = minima[ROI_id], maxima[ROI_id]
                        volume = AnnProc.segmentation_input(
                            point_minima, point_maxima, ROI_id + 1
                        )
                        # point_minima += 1

                    # Make sure the volume is still present after ROI segmentation
                    if not ROI_volume or not ImProc.volume_check(volume):
                        self.analysis_status.emit([i, f"ROI not in dataset..."])
                        # Cache results
                        ResExp.cache_result([filename, ROI_name, "ROI not in dataset."])
                        continue
                else:
                    volume, point_minima = VolProc.volume_prep(volume)
                    ROI_name, ROI_volume = "None", "NA"

                #####
                speeds.append(pf() - a)
                s = pf()
                #####

                # Pad the volume for skeletonization
                volume = VolProc.pad_volume(volume)

                # Skeletonizing
                self.analysis_status.emit([i, "Skeletonizing volume..."])
                points = VolProc.skeletonize(volume)

                # Radius calculations
                self.analysis_status.emit([i, "Measuring radii..."])
                skeleton_radii, vis_radii = VolProc.radii_calc_input(
                    volume, points, resolution, gen_vis_radii=gen_options.save_graph
                )

                # Treat 2D images as if they were 3D
                if volume.ndim == 2:
                    points, volume, volume_shape = ImProc.reshape_2D(points, volume)
                else:
                    volume_shape = volume.shape

                del volume
                volume = None

                if self.running == False:
                    self.analysis_status.emit([i, "Canceled."])
                    break

                ####
                speeds.append(pf() - s)
                g = pf()
                ####

                ## Graph construction.
                self.analysis_status.emit([i, "Reconstructing network..."])
                graph = GProc.create_graph(
                    volume_shape, skeleton_radii, vis_radii, points, point_minima
                )

                ######
                speeds.append(pf() - g)
                fp = pf()
                ######

                if gen_options.prune_length:
                    self.analysis_status.emit([i, "Pruning end points..."])
                    GProc.prune_input(graph, gen_options.prune_length, resolution)

                self.analysis_status.emit([i, "Filtering isolated segments..."])
                GProc.filter_input(graph, gen_options.filter_length, resolution)

                #####
                speeds.append(pf() - fp)
                r = pf()
                #####

                self.analysis_status.emit([i, "Analyzing features..."])
                result, seg_results = FeatExt.feature_input(
                    graph,
                    resolution,
                    filename,
                    image_dim=gen_options.image_dimensions,
                    image_shape=image_shape,
                    ROI_name=ROI_name,
                    ROI_volume=ROI_volume,
                    save_seg_results=gen_options.save_seg_results,
                    reduce_graph=gen_options.save_graph,
                )

                #### COMMENT BEFORE FLIGHT ####
                #### COMMENT BEFORE FLIGHT ####
                # speeds.append(pf() - r)
                # result.extend(speeds)
                #### COMMENT BEFORE FLIGHT ####
                #### COMMENT BEFORE FLIGHT ####

                ResExp.cache_result(result)  # Cache results

                self.analysis_status.emit([i, "Exporting segment results..."])
                if gen_options.save_seg_results:
                    ResExp.write_seg_results(
                        seg_results, gen_options.results_folder, filename, ROI_name
                    )

                if gen_options.save_graph:
                    if ROI_name != "None":
                        color = annotation_data[ROI_name]["colors"][0]
                        if type(color) == list:
                            color = helpers.rgb_to_hex(color)
                        graph.es["hex"] = color
                        graph.es["ROI_ID"] = j

                    graph = GIO.save_graph(
                        graph, filename, gen_options.results_folder, caching=True
                    )
                    GIO.cache_graph(graph)

            if gen_options.save_graph:
                self.analysis_status.emit([i, "Saving graph..."])
                GIO.save_cache(filename, gen_options.results_folder)

            if self.running and file_analyzed:
                speed = helpers.get_time(tic)
                self.analysis_status.emit(
                    [i, f"Analyzed in {speed}.", f"{j+1}/{len(annotation_data.keys())}"]
                )

        if self.running:
            ResExp.write_results(
                gen_options.results_folder, gen_options.image_dimensions
            )

        # Make sure we delete the labeled_cache_volume if it exists
        ImProc.clear_labeled_cache()

        self.button_lock.emit(0)
        self.running = False
        return

    # Cancel option.
    def stop(self):
        self.running = False


class GraphThread(QThread):
    button_lock = pyqtSignal(int)
    selection_signal = pyqtSignal(int)
    analysis_status = pyqtSignal(list)

    def __init__(self, analysis_options, graph_options, column1_files, column2_files):
        QThread.__init__(self)
        self.running = False
        self.gen_options = analysis_options
        self.graph_options = graph_options

        if not column2_files:
            column2_files = [None for _ in range(len(column1_files))]
        self.files = zip(column1_files, column2_files)

    def run(self):
        self.running = True
        gen_options = self.gen_options
        graph_options = self.graph_options
        self.button_lock.emit(1)

        resolution = ImProc.prep_resolution(gen_options.resolution)

        for i, file in enumerate(self.files):
            if not self.running:
                self.analysis_status.emit([i, "Canceled."])
                continue
            tic = pf()
            self.selection_signal.emit(i)
            self.analysis_status.emit([i, "Importing graph..."])
            filename = ImProc.get_filename(file[0])
            if graph_options.file_format == "csv":
                graph_file = {"Vertices": file[0], "Edges": file[1]}
            else:
                graph_file = file[0]

            graph = GIO.graph_loading_dock(graph_file, graph_options, resolution)

            if (
                graph_options.graph_type == "Centerlines"
                and graph_options.filter_cliques
            ):
                self.analysis_status.emit([i, "Filtering cliques..."])
                GProc.clique_filter_input(graph)

            if gen_options.prune_length:
                self.analysis_status.emit([i, "Pruning end points..."])
                GProc.prune_input(
                    graph,
                    gen_options.prune_length,
                    resolution,
                    graph_options.smooth_centerlines,
                    graph_options.graph_type,
                )

            self.analysis_status.emit([i, "Filtering isolated segments..."])
            GProc.filter_input(
                graph,
                gen_options.filter_length,
                resolution,
                centerline_smoothing=graph_options.smooth_centerlines,
                graph_type=graph_options.graph_type,
            )

            self.analysis_status.emit([i, "Analyzing graph..."])
            result, seg_result = FeatExt.feature_input(
                graph,
                resolution,
                filename,
                image_dim=gen_options.image_dimensions,
                graph_type=graph_options.graph_type,
                centerline_smoothing=graph_options.smooth_centerlines,
                save_seg_results=gen_options.save_seg_results,
                reduce_graph=gen_options.save_graph,
            )

            self.analysis_status.emit([i, "Saving results..."])
            ResExp.cache_result(result)
            if gen_options.save_seg_results:
                ResExp.write_seg_results(
                    seg_result, gen_options.results_folder, filename, ROI_Name="None"
                )

            if gen_options.save_graph:
                self.analysis_status.emit([i, "Saving graph..."])
                graph.es["hex"] = [["FFFFFF"]]
                GIO.save_graph(
                    graph, filename, gen_options.results_folder, main_thread=False
                )

            if self.running:
                speed = helpers.get_time(tic)
                self.analysis_status.emit([i, f"Analyzed in {speed}."])

        if self.running:
            self.analysis_status.emit([i, "Exporting results..."])
            ResExp.write_results(
                gen_options.results_folder, gen_options.image_dimensions
            )
            self.analysis_status.emit([i, f"Analyzed in {speed}."])

        self.button_lock.emit(0)
        self.running = False
        return

    # Cancel option.
    def stop(self):
        self.running = False


#####################
### Visualization ###
#####################
class VolumeVisualizationThread(QThread):
    button_lock = pyqtSignal(int)
    analysis_status = pyqtSignal(list)  # ['Status', %]
    mesh_emit = pyqtSignal(IC.PyVistaMeshes)
    failure_emit = pyqtSignal(int)

    def __init__(self, analysis_options, visualization_options, analysis_files):
        QThread.__init__(self)
        self.running = False
        self.gen_options = analysis_options
        self.vis_options = visualization_options
        self.analysis_files = analysis_files

    def run(self):
        self.complete = False
        self.running = True
        self.button_lock.emit(1)
        gen_options = self.gen_options
        vis_options = self.vis_options
        volume_file = self.analysis_files.file1
        annotation_file = self.analysis_files.file2
        annotation_type = self.analysis_files.annotation_type
        annotation_data = self.analysis_files.annotation_data

        # Make sure the resolution is in the proper format
        resolution = ImProc.prep_resolution(gen_options.resolution)

        if annotation_type == "None":
            annotation_data = {None: None}
        elif annotation_type == "RGB":
            ROI_array = AnnProc.prep_RGB_array(annotation_data)
        elif annotation_type == "ID":
            ROI_array = AnnProc.prep_id_array(annotation_data)

        # Single file generation
        main_graph = ig.Graph()  # main graph for final visualization

        # Progress bar update values
        ROI_count = len(annotation_data.keys())
        progress = 0
        step_weight = (70 / ROI_count) / 8

        # Iterate through the ROI's or single file and generate graphs
        for i, ROI_name in enumerate(annotation_data.keys()):
            ## File initialization
            if not self.running:
                self.analysis_status.emit(["Canceled", 0])
                break
            self.analysis_status.emit(["Loading file...", progress])
            filename = ImProc.get_filename(volume_file)

            ## Volume processing
            volume, image_shape = ImProc.load_volume(volume_file)
            if not ImProc.volume_check(volume, loading=True):
                self.analysis_status.emit(["Error: Unable to read image.", 0])
                break
            progress += step_weight

            if ROI_name:

                ROI_id = i % 255
                if i % 255 == 0:
                    # Make sure there is enough disk space for the labeled_volume file
                    if not helpers.check_storage(volume_file):
                        file_size = helpers.get_file_size(volume_file, GB=True)
                        self.analysis_status.emit(
                            [
                                f"Visualization cancelled: Not enough disk space.<br>>{file_size:.f}GB of free space needed.",
                                0,
                            ]
                        )
                        self.failure_emit.emit(1)
                        self.running = False
                        self.complete = True
                        return

                    self.analysis_status.emit([f"Labeling volume...", progress])
                    ROI_sub_array = ROI_array[i : i + 255]
                    ROI_volumes, minima, maxima = AnnProc.volume_labeling_input(
                        volume, annotation_file, ROI_sub_array, annotation_type
                    )
                    if ROI_volumes is None:
                        self.analysis_status.emit([f"Error labeling volume...", 0])
                        break

                ROI_volume = ROI_volumes[ROI_id]
                if ROI_volume > 0:
                    self.analysis_status.emit([f"Segmenting {ROI_name}...", progress])
                    point_minima, point_maxima = minima[ROI_id], maxima[ROI_id]
                    volume = AnnProc.segmentation_input(
                        point_minima, point_maxima, ROI_id + 1
                    )

                if not ROI_volume or not ImProc.volume_check(volume):
                    progress += step_weight * 7
                    self.analysis_status.emit([f"ROI not in dataset...", progress])
                    continue

            else:
                volume, point_minima = VolProc.volume_prep(volume)
                ROI_name, ROI_volume = "None", "NA"

            # Pad the volume for skeletonization
            volume = VolProc.pad_volume(volume)

            # Skeletonizing
            progress += step_weight
            self.analysis_status.emit(["Skeletonizing volume...", progress])
            points = VolProc.skeletonize(volume)

            # Radius calculations
            progress += step_weight
            self.analysis_status.emit(["Measuring radii...", progress])
            skeleton_radii, vis_radii = VolProc.radii_calc_input(
                volume, points, resolution, gen_vis_radii=True
            )

            if volume.ndim == 2:
                points, volume, volume_shape = ImProc.reshape_2D(points, volume)
            else:
                volume_shape = volume.shape

            # Delete volume or now
            del volume
            volume = None

            ## Graph construction.
            progress += step_weight
            self.analysis_status.emit(["Reconstructing network...", progress])
            graph = GProc.create_graph(
                volume_shape, skeleton_radii, vis_radii, points, point_minima
            )

            progress += step_weight
            if gen_options.prune_length > 0:
                self.analysis_status.emit(["Pruning end points...", progress])
                GProc.prune_input(graph, gen_options.prune_length, resolution)

            progress += step_weight
            self.analysis_status.emit(["Filtering isolated segments...", progress])
            GProc.filter_input(graph, gen_options.filter_length, resolution)

            if not self.running:
                self.analysis_status.emit(["Canceled", 0])
                break

            # Don't need the results, but we do need to reduce the graph
            progress += step_weight
            self.analysis_status.emit(["Analyzing features...", progress])
            _, _ = FeatExt.feature_input(
                graph,
                resolution,
                filename,
                image_dim=gen_options.image_dimensions,
                image_shape=image_shape,
                ROI_name=ROI_name,
                ROI_volume=ROI_volume,
                reduce_graph=True,
            )

            ## add mesh colors
            if vis_options.render_annotations:
                if ROI_name != "None":
                    color = annotation_data[ROI_name]["colors"][0]
                    if type(color) == list:
                        color = helpers.rgb_to_hex(color)
                    graph.es["hex"] = color
                    graph.es["ROI_ID"] = i

            if ROI_name != "None":
                status = f"{ROI_name} analysis complete."
            else:
                status = "Analysis complete."
            progress += step_weight
            self.analysis_status.emit([status, progress, f"{i+1}/{ROI_count}"])

            if not self.running:
                self.analysis_status.emit(["Canceled", 0])
                break

            main_graph += graph
            del graph

        if not self.running:
            self.analysis_status.emit(["Canceled", 0])

        ### add visualization
        if self.running:
            if main_graph.vcount():
                self.analysis_status.emit(["Generating meshes...", 70])

                # Send the volume to be visualized if
                # one of the volume visualization options were selected
                # Volume is already None,
                # so it won't be visualized if neither were selected
                if any(
                    [self.vis_options.load_original, self.vis_options.load_smoothed]
                ):
                    volume, _ = ImProc.load_volume(volume_file)
                    volume = ImProc.prep_numba_compatability(volume)
                    volume = VolProc.pad_volume(volume)
                    if volume.ndim == 2:
                        _, volume, _ = ImProc.reshape_2D(points, volume)

                meshes = VolVis.mesh_construction(
                    main_graph,
                    vis_options,
                    volume,
                    application=True,
                    status_updater=self.analysis_status,
                )
            else:
                self.analysis_status.emit(
                    ["Visualization cancelled: Volume has no vessels.", 0]
                )
                self.failure_emit.emit(1)
                self.running = False

        if self.running:
            self.analysis_status.emit(
                ["Mesh construction complete: Loading volumes...", 100]
            )
            self.mesh_emit.emit(meshes)

        # Make sure we delete the labeled_cache_volume if it exists
        ImProc.clear_labeled_cache()

        self.running = False
        self.complete = True
        return

    # Cancel option.
    def stop(self):
        self.running = False


class GraphVisualizationThread(QThread):
    button_lock = pyqtSignal(int)
    analysis_status = pyqtSignal(list)  # ['Status', %]
    mesh_emit = pyqtSignal(IC.PyVistaMeshes)
    failure_emit = pyqtSignal(int)

    def __init__(
        self, analysis_options, graph_options, visualization_options, analysis_files
    ):
        QThread.__init__(self)
        self.running = False
        self.gen_options = analysis_options
        self.graph_options = graph_options
        self.vis_options = visualization_options
        self.analysis_files = analysis_files

    def run(self):
        self.running = True
        gen_options = self.gen_options
        graph_options = self.graph_options
        vis_options = self.vis_options
        file = [self.analysis_files.file1, self.analysis_files.file2]
        self.button_lock.emit(1)

        resolution = ImProc.prep_resolution(gen_options.resolution)

        if not self.running:
            self.analysis_status.emit(["Canceled."])
            self.failure_emit.emit(1)
            return

        self.analysis_status.emit(["Importing graph...", 0])
        filename = ImProc.get_filename(file[0])
        if graph_options.file_format == "csv":
            graph_file = {"Vertices": file[0], "Edges": file[1]}
        else:
            graph_file = file[0]

        # Cover exceptions raised by incorrect graph loading.
        try:
            graph = GIO.graph_loading_dock(
                graph_file, graph_options, resolution, Visualize=True
            )
        except Exception as error:
            self.analysis_status.emit(
                [
                    f"Graph loading error: Check that all options were correct when loading the graph.",
                    0,
                ]
            )
            self.failure_emit.emit(1)
            return

        if graph_options.graph_type == "Centerlines" and graph_options.filter_cliques:
            self.analysis_status.emit(["Filtering cliques...", 15])
            GProc.clique_filter_input(graph)

        if gen_options.prune_length:
            self.analysis_status.emit(["Pruning end points...", 30])
            GProc.prune_input(
                graph,
                gen_options.prune_length,
                resolution,
                graph_options.smooth_centerlines,
                graph_options.graph_type,
            )

        self.analysis_status.emit(["Filtering isolated segments...", 45])
        GProc.filter_input(
            graph,
            gen_options.filter_length,
            resolution,
            centerline_smoothing=graph_options.smooth_centerlines,
            graph_type=graph_options.graph_type,
        )

        if not self.running:
            self.analysis_status.emit(["Canceled."])
            self.failure_emit.emit(1)
            return

        self.analysis_status.emit(["Analyzing graph...", 60])
        _, _ = FeatExt.feature_input(
            graph,
            resolution,
            filename,
            image_dim=gen_options.image_dimensions,
            graph_type=graph_options.graph_type,
            centerline_smoothing=graph_options.smooth_centerlines,
            reduce_graph=True,
        )

        if not self.running:
            self.analysis_status.emit(["Canceled."])
            self.failure_emit.emit(1)
            return

        self.analysis_status.emit(["Generating meshes...", 70])
        meshes = VolVis.mesh_construction(
            graph,
            vis_options,
            graph_type=self.graph_options.graph_type,
            application=True,
        )

        if self.running:
            self.analysis_status.emit(["Mesh construction complete", 100])
            self.mesh_emit.emit(meshes)

        self.running = False
        return

    # Cancel option.
    def stop(self):
        self.running = False


######################
### Movie Creation ###
######################
# is it possible to start the thread and only have it move when it's called?
class MovieThread(QThread):
    write_frame = pyqtSignal()
    rendering_complete = pyqtSignal()
    progress_update = pyqtSignal(int)

    def __init__(self, plotter, path):
        super().__init__()
        self.plotter = plotter
        self.path = path
        self.rendering = True
        self.next_frame = 0
        self.current_frame = 0
        self.started = False

    def run(self):
        ### Honestly I'm not sure why it works, but I've added two buffer
        # points to this QThread. Without them, the thread was somehow
        # outrunning the frame writing of the main thread.
        self.plotter.camera_position = self.path[0]
        self.plotter.render()
        sleep(0.75)  # First buffer

        while self.rendering:
            if not self.started:
                self.write_frame.emit()
                self.started = True
            elif self.current_frame != self.next_frame:
                self.plotter.camera_position = self.path[self.next_frame]
                self.plotter.renderer.ResetCameraClippingRange()
                self.plotter.update()
                self.progress_update.emit(self.current_frame)
                self.current_frame = self.next_frame
                sleep(0.01)  # Repeating buffer for each frame
                self.write_frame.emit()

        self.rendering_complete.emit()
        return


################
### JIT Init ###
################
# Run a tiny volume through the pipeline to prep the JIT functions that need it
def prepare_compilers():
    resolution = np.array([1.0, 1.0, 1.0])
    file = os.path.join(helpers.get_cwd(), "library", "volumes", "JIT_volume.nii")
    file = helpers.std_path(file)
    volume, image_shape = ImProc.load_volume(file)
    volume, point_minima = VolProc.volume_prep(volume)
    volume = VolProc.pad_volume(volume)
    volume_shape = volume.shape
    points = VolProc.skeletonize(volume)
    skeleton_radii, vis_radii = VolProc.radii_calc_input(
        volume, points, resolution, gen_vis_radii=True
    )
    graph = GProc.create_graph(
        volume_shape, skeleton_radii, vis_radii, points, point_minima
    )
    GProc.prune_input(graph, 5, resolution)
    GProc.filter_input(graph, 5, resolution)
    _, _ = FeatExt.feature_input(
        graph, resolution, "None", image_dim=3, reduce_graph=True
    )

    # Not necessary - but for sanity
    del volume
    del graph
