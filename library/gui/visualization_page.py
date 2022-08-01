"""
The PyQt5 code used to create the visualization page for the program.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os
import sys

import numpy as np
import pyvista as pv
from PyQt5.Qt import pyqtSlot
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QWidget,
)
from pyvistaqt import QtInteractor

from library import (
    helpers,
    image_processing as ImProc,
    input_classes as IC,
    qt_threading as QtTh,
)
from library.annotation.tree_processing import RGB_duplicates_check
from library.file_processing import dataset_io
from library.gui import AnalysisOptionsWidget, GraphOptionsWidget, qt_objects as QtO
from library.gui.annotation_page import RGB_Warning
from library.gui.movie_widgets import MovieDialogue, RenderDialogue


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.plotter = QtInteractor(parent=self)

        self.setWindowTitle("Annotation Testing")
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        layout = QtO.new_layout(None, "H", True, "None")
        self.centralWidget.setLayout(layout)

        annotationpage = VisualizationPage(self.plotter)

        layout.addWidget(annotationpage)

        self.show()


class VisualizationPage(QSplitter):
    def __init__(self, plotter, mainWindow):
        super().__init__()
        self.plotter = plotter
        self.update_plotter_resolution(1)
        self.meshes = IC.PyVistaMeshes()
        self.actors = IC.PyVistaActors()
        self.files = IC.VisualizationFiles()
        self.graph_options = IC.GraphOptions()

        # self.splitterMoved.connect(self.redraw_widgets)
        ## Default loading file
        default_file = os.path.join(
            helpers.get_cwd(), "library", "volumes", "Demo Volume.nii"
        )
        default_file = helpers.std_path(default_file)
        self.files.file1 = str(default_file)
        ## Page layout setup
        pageLayout = QtO.new_layout(self, no_spacing=True)

        self.optionsColumn = QtO.new_widget(fixed_width=210)
        optionsLayout = QtO.new_layout(self.optionsColumn, "V", margins=(5, 10, 5, 10))
        self.optionsScroll = QtO.new_scroll(self.optionsColumn)
        self.optionsScroll.setFixedWidth(235)

        self.loadingBox = TopWidget(self, self.plotter, mainWindow)
        self.loadingBox.visualizeButton.clicked.connect(self.prepare_visualization)
        self.loadingBox.loadingButton.clicked.connect(self.load_files)

        self.generalOptions = GeneralOptions(self.plotter)
        self.tubeOptions = TubeOptions(
            self.plotter, self.meshes, self.actors, self.generalOptions
        )
        self.volumeOptions = VolumeOptions(self.plotter, self.meshes, self.actors)

        line1 = QtO.new_line()
        QtO.add_widgets(
            optionsLayout,
            [
                self.loadingBox,
                line1,
                self.generalOptions,
                5,
                self.tubeOptions,
                5,
                self.volumeOptions,
                0,
            ],
        )

        QtO.add_widgets(pageLayout, [self.optionsScroll, self.plotter])

        return

    ## Visualization functions
    def prepare_visualization(self):
        visualizer = VisualizationDialog(
            self.files,
            self.graph_options,
            self.plotter,
            self.actors,
            self.meshes,
        )
        if visualizer.exec_():
            # Update the filename and meshes
            self.files.visualized_file = self.files.file1_name()
            self.meshes = visualizer.meshes
            self.loadingBox.update_rendered(self.files.visualized_file)

            # Update the plotter resolution
            self.update_plotter_resolution(visualizer.analysis_options.resolution)

            # Clear the old actors from the scene
            self.tubeOptions.remove_tube_actors()
            self.volumeOptions.remove_volume_actors()

            # Add the new meshes to the tubeOptions and volumeOptions classes
            self.tubeOptions.load_meshes(self.meshes, self.files.annotation_type)
            self.volumeOptions.load_meshes(self.meshes)

            # Update the meshes in the scene
            self.update_meshes(visualizer.analysis_options.image_dimensions)
            del visualizer
        else:
            if visualizer.visualizing:
                visualizer.a_thread.quit()
            del visualizer
        return

    def update_meshes(self, dimensions):
        tube_lock = False if self.meshes.network or self.meshes.scaled else True
        self.tubeOptions.tubeBox.setDisabled(tube_lock)
        volume_lock = False if self.meshes.original or self.meshes.smoothed else True
        self.volumeOptions.volumeBox.setDisabled(volume_lock)

        self.tubeOptions.noTubes.setChecked(True)
        self.volumeOptions.noVolume.setChecked(True)

        if dimensions == 2:
            self.tubeOptions.vesselScalar.setItemText(3, "PAF %")
        elif dimensions == 3:
            self.tubeOptions.vesselScalar.setItemText(3, "Volume")

        if self.meshes.network:
            self.tubeOptions.networkTubes.setChecked(True)
        elif self.meshes.scaled:
            self.tubeOptions.scaledTubes.setChecked(True)
        elif self.meshes.original:
            self.volumeOptions.originalVolume.setChecked(True)
        elif self.meshes.smoothed:
            self.volumeOptions.smoothedVolume.setChecked(True)

        self.plotter.reset_camera()
        return

    def update_plotter_resolution(self, resolution):
        resolution = ImProc.prep_resolution(resolution)
        self.plotter._vv_resolution = np.flip(resolution)  # Flip due to PyVista
        return

    # Update meshes for all of the widgets
    def file_warning(self):
        msgBox = QMessageBox()
        message = "Files must be loaded before visualization!"
        msgBox.setText(message)
        msgBox.exec_()
        return

    def load_files(self):
        loader = LoadingDialog()
        if loader.exec_():
            self.files = loader.files
            self.graph_options = loader.prepare_graph_options()
            self.loadingBox.update_loaded(self.files.file1_name())
        del loader
        return

    # # Housekeeping
    # def redraw_widgets(self):
    #     sizes = self.sizes()
    #     if sizes[0]:
    #         self.optionsScroll.update()
    #         self.optionsColumn.update()


class VisualizationDialog(QDialog):
    def __init__(self, files, graph_options, plotter, actors, meshes):
        super().__init__()
        self.files = files
        self.graph_options = graph_options
        self.plotter = plotter
        self.actors = actors
        self.meshes = meshes
        self.visualizing = False

        pageLayout = QtO.new_layout(self, "V", spacing=0)

        self.setWindowTitle("Visualization")

        ## Four rows
        ## Top row
        self.topWidget = QtO.new_widget()
        topLayout = QtO.new_layout(self.topWidget, margins=0)

        # Top left
        topLeft = QtO.new_widget()
        topLeftLayout = QtO.new_layout(topLeft, "V", no_spacing=True)
        tlHeader = QLabel("<b>Visualization Options")

        leftGroup = QGroupBox()
        leftGroupLayout = QtO.new_layout(leftGroup, "V", spacing=10)

        vesselHeader = QLabel("<b>Vessel Visualization")
        self.loadNetwork = QtO.new_checkbox("Vessel centerlines")
        self.loadNetwork.setChecked(True)
        self.loadScaled = QtO.new_checkbox("Scaled vessels")

        qualityLayout = QtO.new_layout(no_spacing=True)
        qualityHeader = QLabel("Rendering Quality:")
        self.renderingQuality = QtO.new_combo(["High", "Medium", "Low"], 110)
        QtO.add_widgets(qualityLayout, [qualityHeader, 0, self.renderingQuality])

        volumeHeader = QLabel("<b>Volume Visualization")
        self.loadOriginal = QtO.new_checkbox("Original volume")
        self.loadSmoothed = QtO.new_checkbox("Smoothed volume")

        # Lock if analyzing graph or annotated dataset
        topLeft_widgets = [
            vesselHeader,
            self.loadNetwork,
            self.loadScaled,
            qualityLayout,
            0,
            volumeHeader,
            self.loadOriginal,
            self.loadSmoothed,
        ]

        # Conditional additions
        if (
            self.files.dataset_type == "Volume"
            and self.graph_options.graph_type != "Centerlines"
        ):
            typeLayout = QtO.new_layout(no_spacing=True)
            reducedHeader = QLabel("Network rendering:")
            self.reducedNetwork = QtO.new_combo(["Detailed", "Simplified"], 110)
            tip = "Simplified networks are less detailed but render more quickly. "
            self.reducedNetwork.setToolTip(tip)
            reducedHeader.setToolTip(tip)
            QtO.add_widgets(typeLayout, [reducedHeader, 0, self.reducedNetwork])
            topLeft_widgets.insert(3, typeLayout)

        QtO.add_widgets(leftGroupLayout, topLeft_widgets)

        QtO.add_widgets(topLeftLayout, [tlHeader, leftGroup])

        # Top right layout
        topRight = QWidget()
        topRightLayout = QtO.new_layout(topRight, "V", no_spacing=True)
        trHeader = QLabel("<b>Analysis Options")

        analysisBox = QGroupBox()
        analysisLayout = QtO.new_layout(analysisBox, no_spacing=True)
        self.analysisOptions = AnalysisOptionsWidget(visualizing=True)

        # If a centerline graph was loaded, add centerline smoothing buttons
        if self.files.dataset_type == "Graph":
            # Disable the volume loading buttons if we're loading a graph
            self.loadOriginal.setDisabled(True)
            self.loadSmoothed.setDisabled(True)

            # Add centerline smoothing & clique removal options if loading
            # a centerline-based graph
            if self.graph_options.graph_type == "Centerlines":
                self.centerlineLine = QtO.new_widget()
                clLayout = QtO.new_layout(self.centerlineLine, margins=0)
                self.centerlineSmoothing = QtO.new_checkbox("Centerline smoothing")
                QtO.add_widgets(clLayout, [self.centerlineSmoothing])

                self.cliqueLine = QtO.new_widget()
                cliqueLayout = QtO.new_layout(self.cliqueLine, margins=0)
                self.cliqueFiltering = QtO.new_checkbox("Clique filtering")
                QtO.add_widgets(cliqueLayout, [self.cliqueFiltering])
                widgets = [4, self.centerlineLine, 8, self.cliqueLine]
                QtO.add_widgets(
                    self.analysisOptions.rightOptionsLayout, widgets, "Left"
                )

        QtO.add_widgets(analysisLayout, [self.analysisOptions])

        QtO.add_widgets(topRightLayout, [trHeader, analysisBox])

        QtO.add_widgets(topLayout, [topLeft, topRight])

        ## title row
        fileRow = QWidget()
        fileRowLayout = QtO.new_layout(fileRow)

        loadedHeader = QLabel("<b>Loaded file:")
        file = self.files.file1_name()
        self.loadedFile = QtO.new_line_edit(file, "Center", 180, True)
        widgets = [0, loadedHeader, self.loadedFile]
        if self.files.annotation_type != "None" and self.files.dataset_type == "Volume":
            self.processedHeader = QLabel("<b>Analyzed regions:")
            processed = f"0/{len(self.files.annotation_data.keys())}"
            self.processedEdit = QtO.new_line_edit(processed, "Center", 80, True)
            widgets += [5, self.processedHeader, self.processedEdit]
        widgets += [0]

        QtO.add_widgets(fileRowLayout, widgets)

        ## (second) middle row
        middleWidget = QtO.new_widget()
        middleLayout = QtO.new_layout(middleWidget, margins=0)

        progressWidget = QtO.new_widget()
        progressLayout = QtO.new_layout(progressWidget, "V")
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBarText = QLabel("<center>Waiting...")
        QtO.add_widgets(progressLayout, [self.progressBar, self.progressBarText])

        QtO.add_widgets(middleLayout, [progressWidget])

        # bottom widget
        bottomWidget = QtO.new_widget()
        bottomLayout = QtO.new_layout(bottomWidget, margins=0)
        self.cancelButton = QtO.new_button("Cancel", self.cancel_visualization)
        QtO.button_defaulting(self.cancelButton, False)
        self.startButton = QtO.new_button("Visualize", self.init_visualization)
        QtO.button_defaulting(self.startButton, True)

        self.helpButton = QtO.new_help_button(self.rendering_help)
        QtO.button_defaulting(self.helpButton, False)
        QtO.add_widgets(
            bottomLayout,
            [0, self.cancelButton, self.startButton, self.helpButton],
        )

        QtO.add_widgets(
            pageLayout, [self.topWidget, fileRow, middleWidget, bottomWidget]
        )

        self.resize()
        return

    def rendering_help(self):
        return

    def check_boxes(self):
        a = self.loadNetwork.isChecked()
        b = self.loadScaled.isChecked()
        c = self.loadOriginal.isChecked()
        d = self.loadSmoothed.isChecked()
        return any([a, b, c, d])

    def init_visualization(self):
        if not self.check_boxes():
            self.render_warning()
            return

        self.prepare_visualization_options()
        self.analysis_options = self.analysisOptions.prepare_options(visualization=True)
        if self.files.dataset_type == "Volume":
            self.init_volume_visualization()

        elif self.files.dataset_type == "Graph":
            self.init_graph_visualization()

        for actor in self.actors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor, reset_camera=False)
                helpers.remove_legend(self.plotter, actor)

        self.actors.reset()
        self.meshes.reset()

        self.a_thread.analysis_status.connect(self.update_progress)
        self.a_thread.button_lock.connect(self.button_lock)
        self.a_thread.mesh_emit.connect(self.complete_visualization)
        self.a_thread.failure_emit.connect(self.failed_visualization)
        self.a_thread.start()
        self.visualizing = True
        return

    def init_volume_visualization(self):
        self.a_thread = QtTh.VolumeVisualizationThread(
            self.analysis_options, self.vis_options, self.files
        )
        return

    def init_graph_visualization(self):
        if self.graph_options.graph_type == "Centerlines":
            self.graph_options.smooth_centerlines = self.centerlineSmoothing.isChecked()
            self.graph_options.filter_cliques = self.cliqueFiltering.isChecked()
        self.a_thread = QtTh.GraphVisualizationThread(
            self.analysis_options,
            self.graph_options,
            self.vis_options,
            self.files,
        )
        return

    # Visualization thread connections
    def update_progress(self, update):
        self.progressBarText.setText(f"<center>{update[0]}")
        self.progressBar.setValue(update[1])
        if self.files.annotation_type != "None" and len(update) == 3:
            self.processedEdit.setText(update[2])
        return

    def button_lock(self, lock):
        self.startButton.setDisabled(lock)
        self.helpButton.setDisabled(lock)
        self.topWidget.setDisabled(lock)

    def complete_visualization(self, meshes):
        self.meshes = meshes
        self.a_thread.quit()
        self.accept()
        return

    def failed_visualization(self, status):
        self.visualizing = False
        self.a_thread.quit()
        return

    def prepare_visualization_options(self):
        # Graph reduction
        if (
            self.files.dataset_type == "Volume"
            and self.graph_options.graph_type != "Centerlines"
        ):
            simplified = (
                True if self.reducedNetwork.currentText() == "Simplified" else False
            )
        else:
            simplified = False

        render_annotations = False if self.files.annotation_type == "None" else True

        rendering_quality = self.renderingQuality.currentIndex()

        self.vis_options = IC.VisualizationOptions(
            True,
            simplified,
            self.loadScaled.isChecked(),
            self.loadNetwork.isChecked(),
            self.loadOriginal.isChecked(),
            self.loadSmoothed.isChecked(),
            render_annotations=render_annotations,
            rendering_quality=rendering_quality,
        )
        return

    def render_warning(self):
        msgBox = QMessageBox()
        message = "At least one component needs to be rendered!"
        msgBox.setText(message)
        msgBox.exec_()

    def cancel_visualization(self):
        if self.visualizing:
            if not self.close_warning():
                return
            self.update_progress(["Canceling...", 0])
            self.a_thread.stop()
            self.a_thread.quit()
            # self.cancelButton.setDisabled(True)
            # while not self.a_thread.complete:
            #     sleep(1)
        self.reject()
        return

    def closeEvent(self, event):
        self.cancel_visualization()
        event.ignore()
        return

    def close_warning(self):
        dialog = QDialog()
        layout = QtO.new_layout(dialog, "V")
        message = QLabel("Are you sure you want to cancel the visualization?")
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.No | QDialogButtonBox.Yes)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        QtO.add_widgets(layout, [message, buttonBox])
        return dialog.exec_()

    # Window size management
    def resize(self):
        self.window().setFixedSize(self.window().sizeHint())
        return


class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.files = IC.VisualizationFiles()

        pageLayout = QtO.new_layout(self, "V", spacing=0)

        ## Top and bottom structured layout
        # top
        pageHeader = QLabel("<b>Dataset Loading")
        topWidget = QGroupBox()
        topLayout = QtO.new_layout(topWidget)

        # top left
        topLeft = QtO.new_widget(fixed_width=180)
        topLeftLayout = QtO.new_layout(topLeft, "V")

        typeHeader = QLabel("<b>Dataset Type:")
        self.datasetType = QtO.new_combo(["Volume", "Graph"], connect=self.toggle_type)

        annHeader = QLabel("<b>Annotation Type:")
        self.annotationType = QtO.new_combo(
            ["None", "ID", "RGB"], connect=self.annotation_options
        )
        self.annotationType.currentIndexChanged.connect(self.update_JSON)

        # Load annotation
        self.loadAnnotationFile = QtO.new_widget()
        aFileLayout = QtO.new_layout(self.loadAnnotationFile, "V", margins=0)

        loadJSON = QtO.new_button("Load JSON", self.load_annotation_file)
        loadJSON.setToolTip(
            "Load annotation file created using the Annotation Processing tab."
        )
        QtO.button_defaulting(loadJSON, False)
        loaded = QLabel("<center>Loaded JSON:")
        self.loadedJSON = QtO.new_line_edit("None", "Center", locked=True)
        self.JSONdefault = self.loadedJSON.styleSheet()
        self.loadAnnotationFile.setVisible(False)
        QtO.add_widgets(aFileLayout, [loadJSON, loaded, self.loadedJSON], "Center")

        QtO.add_widgets(
            topLeftLayout,
            [
                typeHeader,
                self.datasetType,
                annHeader,
                self.annotationType,
                self.loadAnnotationFile,
                0,
            ],
            "Center",
        )

        ## top right
        self.topRight = QtO.new_widget(fixed_width=400)
        topRightLayout = QtO.new_layout(self.topRight, "H", margins=0)
        lineLayout = QtO.new_form_layout(None, "Center")

        file1Widget = QtO.new_widget()
        file1Layout = QtO.new_layout(file1Widget, margins=0)
        self.file1Header = QLabel("Volume file:")
        self.file1Edit = QtO.new_line_edit("None", "Center", 180, locked=True)
        selectFile1 = QtO.new_button("Select...", self.select_file1)
        QtO.button_defaulting(selectFile1, False)
        QtO.add_widgets(file1Layout, [self.file1Edit, selectFile1])

        self.file2Widget = QtO.new_widget()
        file2Layout = QtO.new_layout(self.file2Widget, margins=0)
        self.file2Header = QLabel("Annotation file:")
        self.file2Edit = QtO.new_line_edit("None", "Center", 180, locked=True)
        selectFile2 = QtO.new_button("Select...", self.select_file2)
        QtO.button_defaulting(selectFile2, False)
        QtO.add_widgets(file2Layout, [self.file2Edit, selectFile2])
        self.file2Widget.setVisible(False)
        self.file2Header.setVisible(False)

        QtO.add_form_rows(
            lineLayout,
            [
                [self.file1Header, file1Widget],
                [self.file2Header, self.file2Widget],
            ],
        )
        QtO.add_widgets(topRightLayout, [lineLayout], "Center")

        # add top row widgets
        line = QtO.new_line("V", 2)
        QtO.add_widgets(topLayout, [topLeft, line, self.topRight])

        ## Graph options box
        self.bottomWidget = QtO.new_widget()
        bottomLayout = QtO.new_layout(self.bottomWidget, "V", no_spacing=True)
        graphHeader = QLabel("<b>Graph File Options")
        bottomBox = QGroupBox()
        bottomBoxLayout = QtO.new_layout(bottomBox, no_spacing=True)
        self.graphOptions = GraphOptionsWidget()

        self.graphOptions.graphFormat.currentIndexChanged.connect(self.toggle_type)
        self.graphOptions.centerlineLine.setVisible(False)
        self.graphOptions.clLabel.setVisible(False)
        self.graphOptions.cliqueFiltering.setVisible(False)
        self.graphOptions.cliqueLabel.setVisible(False)

        # Add edge hex color identifier
        colorHeaderWidget = QtO.new_widget()
        colorHeaderLayout = QtO.new_layout(colorHeaderWidget, "V", no_spacing=True)
        edgeColorHeader = QLabel("<center><b>Edge color identifier:")
        QtO.add_widgets(colorHeaderLayout, [10, edgeColorHeader])
        self.hexPresent = QtO.new_checkbox(
            "Graph contains hex colors", self.lock_hex_color_edit
        )
        hexHeader = QLabel("Edge hex color:")
        self.edgeHexEdit = QtO.new_line_edit("hex")
        QtO.add_form_rows(
            self.graphOptions.middleColumn,
            [
                colorHeaderWidget,
                self.hexPresent,
                [hexHeader, self.edgeHexEdit],
            ],
        )
        self.edgeHexEdit.setDisabled(True)

        # connect button to lock the edit
        self.graphOptions.graphType.currentIndexChanged.connect(
            self.lock_hex_color_edit
        )

        QtO.add_widgets(bottomBoxLayout, [self.graphOptions])

        QtO.add_widgets(bottomLayout, [graphHeader, bottomBox])
        self.bottomWidget.setVisible(False)

        ## Load / Cancel
        buttonLine = QtO.new_widget()
        buttonLayout = QtO.new_layout(buttonLine, margins=0)

        cancel = QtO.new_button("Cancel", self.reject)
        QtO.button_defaulting(cancel, False)
        accept = QtO.new_button("Load", self.return_files)
        QtO.button_defaulting(accept, True)
        accept.setDefault(True)
        accept.setAutoDefault(True)

        QtO.add_widgets(buttonLayout, [0, cancel, accept])

        ## add
        QtO.add_widgets(
            pageLayout,
            [pageHeader, topWidget, self.bottomWidget, 10, buttonLine],
        )

        self.resize()

    ## Text toggling for file line headers
    def toggle_type(self):
        lock_annotation = False
        show_line2 = False
        if self.datasetType.currentText() == "Graph":
            lock_annotation = True
            self.annotationType.setCurrentIndex(0)
            if self.graphOptions.graphFormat.currentText() == "CSV":
                show_line2 = True

        self.file2Widget.setVisible(show_line2)
        self.file2Header.setVisible(show_line2)
        self.bottomWidget.setVisible(lock_annotation)
        self.annotationType.setDisabled(lock_annotation)
        self.update_headers()
        self.files.clear()
        return

    def lock_hex_color_edit(self):
        lock = False
        if self.graphOptions.graphType.currentText() == "Centerlines":
            lock = True
            self.hexPresent.setDisabled(lock)
        elif self.graphOptions.graphType.currentText() == "Branches":
            self.hexPresent.setDisabled(False)
            if not self.hexPresent.isChecked():
                lock = True
                self.files.clear_annotation()
            else:
                self.files.annotation_type = "ID"
        self.edgeHexEdit.setDisabled(lock)

        return

    def update_headers(self):
        line1_text = "Volume file:"
        line2_text = "Annotation file:"
        show_line2 = False
        if self.datasetType.currentText() == "Graph":
            line2_text = "Graph edges file:"
            format = self.graphOptions.graphFormat.currentText()
            if format == "CSV":
                show_line2 = True
                line1_text = "Graph vertices file:"
            else:
                line1_text = f"{format} file:"
        elif self.datasetType.currentText() == "Volume":
            if self.annotationType.currentIndex():
                show_line2 = True
            if self.annotationType.currentText() == "RGB":
                line2_text = "Annotation folder:"

        self.file1Header.setText(line1_text)
        self.file2Header.setText(line2_text)
        self.file1Edit.setText("None")
        self.file2Edit.setText("None")
        self.file2Widget.setVisible(show_line2)
        self.resize()
        self.files.clear()

    ## File selection
    def select_file1(self):
        if self.datasetType.currentText() == "Volume":
            file = dataset_io.load_volume_file()
        else:
            graph_type = self.graphOptions.graphFormat.currentText()
            file = dataset_io.load_graph_file(graph_type)

        if file:
            self.files.file1 = file
        self.file1Edit.setText(self.files.file1_name())
        return

    def select_file2(self):
        if self.datasetType.currentText() == "Volume":
            if self.annotationType.currentText() == "ID":
                file = dataset_io.load_nii_annotation_file()
            else:
                file = dataset_io.load_RGB_folder()
        else:
            graph_type = self.graphOptions.graphFormat.currentText()
            file = dataset_io.load_graph_file(graph_type)

        if file:
            self.files.file2 = file
        self.file2Edit.setText(self.files.file2_name())
        return

    ## JSON file loading
    def annotation_options(self):
        # Clear the annotation if swapped to None
        visible = True if self.annotationType.currentIndex() else False
        self.files.annotation_type = self.annotationType.currentText()
        self.loadAnnotationFile.setVisible(visible)
        self.file2Widget.setVisible(visible)
        self.file2Header.setVisible(visible)

        if not visible:
            self.files.clear_annotation()

        self.update_headers()
        return

    def load_annotation_file(self):
        loaded_file = dataset_io.load_JSON()

        if loaded_file:
            with open(loaded_file) as f:
                annotation_data = json.load(f)
                if (
                    len(annotation_data) != 1
                    or "VesselVio Annotations" not in annotation_data.keys()
                ):
                    self.JSON_error("Incorrect filetype!")
                else:
                    # If loading an RGB filetype, make sure there's no duplicate colors.
                    if (
                        self.annotationType.currentText() == "RGB"
                        and RGB_duplicates_check(
                            annotation_data["VesselVio Annotations"]
                        )
                    ):
                        if RGB_Warning().exec_() == QMessageBox.No:
                            return

                    self.loadedJSON.setStyleSheet(self.JSONdefault)
                    filename = os.path.basename(loaded_file)
                    self.loadedJSON.setText(filename)
                    self.files.annotation_data = annotation_data[
                        "VesselVio Annotations"
                    ]
        return

    def JSON_error(self, warning):
        self.loadedJSON.setStyleSheet("border: 1px solid red;")
        self.loadedJSON.setText(warning)
        return

    def update_JSON(self):
        if self.annotationType.currentText() == "None":
            self.annotation_data = None
            self.loadedJSON.setText("None")
        return

    ## Window size management
    def resize(self):
        self.window().setFixedSize(self.window().sizeHint())
        return

    ## Final option management
    def prepare_graph_options(self):
        graph_options = self.graphOptions.prepare_options()
        if (
            self.graphOptions.graphType.currentText() == "Branches"
            and self.hexPresent.isChecked()
        ):
            graph_options.a_key.edge_hex = self.edgeHexEdit.text()
        return graph_options

    def return_files(self):
        complete = True
        if not self.files.file1:
            complete = False
        self.files.dataset_type = self.datasetType.currentText()
        if self.files.dataset_type == "Volume":
            self.files.annotation_type = self.annotationType.currentText()
            self.files.dataset_type = "Volume"
            if self.files.annotation_type != "None":
                if not self.files.file2:
                    complete = False
                elif not self.files.annotation_data:
                    complete = False
                    self.JSON_error("Load annotation file")
        else:
            if self.graphOptions.graphFormat.currentText() == "CSV":
                if not self.files.file2:
                    complete = False

        if not complete:
            self.visualization_warning()
            return
        else:
            self.accept()

    # Warning
    def visualization_warning(self):
        warning = QMessageBox()
        warning.setText("Select all files for visualization.")
        warning.exec_()


class TopWidget(QWidget):
    def __init__(
        self, splitter: QSplitter, plotter: pv.Plotter, mainWindow: QMainWindow
    ):
        super().__init__()
        self.splitter = splitter
        self.plotter = plotter
        self.mainWindow = mainWindow
        self.visualized_file = "None"

        ## Layout
        boxLayout = QtO.new_layout(self, "V", margins=0)

        loadedLabel = QLabel("<b>Loaded file:")
        self.loadedFile = QtO.new_line_edit("Demo Volume.nii", "Center", 180, True)

        self.loadingButton = QtO.new_button("Load Files", None)
        self.visualizeButton = QtO.new_button("Visualize", None)

        self.screenshotButton = QtO.new_button("Save image...", self.screenshot, 120)
        self.screenshotButton.setToolTip(
            "Saves a screenshot of the current view into the results directory selected on the anlaysis page."
        )

        self.movieButton = QtO.new_button("Save movie...", self.movie, 120)
        self.movieButton.setToolTip(
            "Save an orbit or fly-through movie of the visualized dataset."
        )

        # self.saveMeshButton = QtO.new_button("Save Mesh", self.save_mesh, 120)

        QtO.add_widgets(
            boxLayout,
            [
                loadedLabel,
                self.loadedFile,
                5,
                self.loadingButton,
                self.visualizeButton,
                self.screenshotButton,
                self.movieButton,
                # self.saveMeshButton,
            ],
            "Center",
        )

    ## Loading file dialog initialization
    def update_loaded(self, filename):
        self.loadedFile.setText(filename)
        return

    def update_rendered(self, filename=None):
        if filename:
            self.visualized_file = filename
        self.visualized_file = os.path.splitext(filename)[0]
        return

    ## Screenshot capturing
    def screenshot(self):
        screenshotDialogue = ScreenshotDialogue(
            self.plotter, self.visualized_file, self.mainWindow
        )
        screenshotDialogue.accepted.connect(self.toggle_splitter)
        screenshotDialogue.rejected.connect(self.toggle_splitter)
        self.toggle_splitter(lock=True)
        screenshotDialogue.show()
        return

    def movie(self):
        self.toggle_splitter(lock=True)
        self.movieDialogue = MovieDialogue(self.plotter, self.mainWindow)
        self.movieDialogue.accepted.connect(self.render_movie)
        self.movieDialogue.rejected.connect(self.delete_movie_dialogue)
        self.movieDialogue.show()
        return

    def render_movie(self):
        # Create the dialogue popup
        self.renderDialog = RenderDialogue(
            self.plotter, self.movieDialogue.movie_settings
        )
        self.renderDialog.exec_()
        self.delete_movie_dialogue()
        return

    def save_mesh(self):
        filename = "/Users/jacobbumgarner/Desktop/Synthetic Vasculature.obj"
        self.plotter.export_obj(filename)

    def delete_movie_dialogue(self):
        try:
            del self.movieDialogue
        except AttributeError:
            pass
        self.toggle_splitter(lock=False)
        return

    def toggle_splitter(self, lock=False):
        self.splitter.setSizes([not lock, 1])
        self.mainWindow.leftMenu.setDisabled(lock)
        for i in range(self.splitter.count()):
            self.splitter.handle(i).setDisabled(lock)
        return


class ScreenshotDialogue(QDialog):
    def __init__(self, plotter, visualized_file, mainWindow):
        super().__init__(mainWindow)
        self.plotter = plotter

        self.setWindowTitle("Save Screenshot")

        self.screenshot_dir = helpers.load_screenshot_dir()
        filename = self.check_name(visualized_file, self.screenshot_dir, 0)
        self.filename = filename

        # Page Layout
        pageLayout = QtO.new_layout(self, "V", spacing=5)

        # Resolution Line
        self.resolutionWidget = QtO.new_widget()
        resolutionLayout = QtO.new_layout(self.resolutionWidget, margins=0)
        resolutionLabel = QLabel("Resolution:")
        self.imageResolution = QtO.new_combo(
            ["Current", "720p", "1080p", "1440p", "2160p"], 120
        )
        self.imageResolution.setCurrentIndex(2)
        QtO.add_widgets(resolutionLayout, [0, resolutionLabel, self.imageResolution, 0])

        ## File path line
        self.filePathWidget = QtO.new_widget()
        filePathLayout = QtO.new_layout(self.filePathWidget, no_spacing=True)
        titleLabel = QLabel("Save path:")
        self.pathEdit = QtO.new_line_edit(self.filename, width=200, locked=True)
        changePathButton = QtO.new_button("Change...", self.get_save_path)
        QtO.add_widgets(
            filePathLayout, [titleLabel, 5, self.pathEdit, 5, changePathButton]
        )

        QtO.button_defaulting(changePathButton, False)

        ## Buttons line
        self.buttons = QtO.new_widget()
        buttonLayout = QtO.new_layout(self.buttons)
        cancelButton = QtO.new_button("Cancel", self.reject)
        captureButton = QtO.new_button("Capture", self.prep_screenshot)
        QtO.add_widgets(buttonLayout, [0, cancelButton, captureButton])

        QtO.button_defaulting(cancelButton, False)
        QtO.button_defaulting(captureButton, True)

        ## Capture message
        self.captureMessage = QLabel("<center><b>Saving screenshot...")
        self.captureMessage.hide()

        ## Add the widgets
        QtO.add_widgets(
            pageLayout,
            [
                self.resolutionWidget,
                self.filePathWidget,
                self.buttons,
                self.captureMessage,
            ],
        )

        self.window().setFixedSize(self.window().sizeHint())
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        return

    def prep_screenshot(self):
        self.setFixedSize(200, 70)
        self.resolutionWidget.hide()
        self.filePathWidget.hide()
        self.buttons.hide()
        self.captureMessage.show()
        resolution = self.imageResolution.currentText()
        if resolution != "Current":
            X, Y = helpers.get_resolution(resolution)
            self.plotter.resize(X, Y)
            self.plotter.render()
        QTimer.singleShot(750, self.take_screenshot)
        return

    def take_screenshot(self):
        # Make sure the parent directory actually exists before saving the image
        helpers.prep_media_dir(self.filename)
        self.plotter.screenshot(self.filename)
        self.accept()
        return

    def check_name(self, filename, results_dir, depth):
        basename = filename + "_0%03d" % depth + ".png"
        filepath = helpers.prep_media_path(results_dir, basename)
        if os.path.exists(filepath):
            return self.check_name(filename, results_dir, depth + 1)
        else:
            return filepath

    def get_save_path(self):
        filename = helpers.get_save_file(
            "Save screenshot as...", self.screenshot_dir, "png"
        )
        if filename:
            self.filename = filename
            self.pathEdit.setText(self.filename)
        return


class GeneralOptions(QWidget):
    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter  # pointer to main plotter
        genLayout = QtO.new_layout(self, "V", no_spacing=True)

        optionsBox = QGroupBox()
        boxLayout = QtO.new_layout(optionsBox, "V")
        boxHeader = QLabel("<b>General Options")

        self.showAxes = QtO.new_checkbox("Show axes", self.toggle_axes)
        self.showBounds = QtO.new_checkbox("Show bounding box", self.toggle_bounds)
        self.showGrid = QtO.new_checkbox("Show grid", self.toggle_grid)
        self.showLegend = QtO.new_checkbox("Show legend")
        self.showLegend.setDisabled(True)

        # Legend options

        ## Form layout
        legendFormLayout = QtO.new_form_layout()
        legendHelp = "Visualization options for the legend"
        self.legendOptions = QtO.CollapsibleBox("Legend options", legendHelp)
        legendLayout = QtO.new_layout(orient="V", no_spacing=True)

        unitHeader = QLabel("Unit:")
        self.legendUnit = QtO.new_combo(["µm", "mm", "px"], 110)

        tickHeader = QLabel("Labels:")
        self.tickCount = QtO.new_combo(["5", "4", "3", "2"], 110)

        digitHeader = QLabel("Digits:")
        self.legendDigits = QtO.new_combo(["4", "3", "2", "1"], 110)
        self.legendDigits.setCurrentIndex(2)

        formatHeader = QLabel("Format:")
        self.legendFormat = QtO.new_combo(["Float", "Exponent", "Mixed"], 110)

        fcHeader = QLabel("Text color:")
        self.textColor = QtO.new_combo(["White", "Black"], 110)

        fontSizeHeader = QLabel("Text size:")
        font_options = [str(i) for i in range(28, 9, -2)]
        self.fontSize = QtO.new_combo(font_options, 110)
        self.fontSize.setCurrentIndex(4)

        orientationHeader = QLabel("Direction:")
        self.legendOrientation = QtO.new_combo(["Horizontal", "Vertical"], 110)

        QtO.add_form_rows(
            legendFormLayout,
            [
                [unitHeader, self.legendUnit],
                [tickHeader, self.tickCount],
                [digitHeader, self.legendDigits],
                [formatHeader, self.legendFormat],
                [fontSizeHeader, self.fontSize],
                [fcHeader, self.textColor],
                [orientationHeader, self.legendOrientation],
            ],
        )

        QtO.add_widgets(legendLayout, [legendFormLayout], "Center")
        self.legendOptions.setContentLayout(legendLayout)
        self.legendOptions.lock(True)
        # self.showLegend.stateChanged.connect(self.legendOptions.lock)

        changeBackground = QtO.new_button(
            "Background color...", self.update_background_color, 160
        )

        ## Add options to box
        QtO.add_widgets(
            boxLayout,
            [
                self.showAxes,
                self.showBounds,
                self.showGrid,
                self.showLegend,
                self.legendOptions,
            ],
        )
        boxLayout.addWidget(changeBackground, alignment=Qt.AlignCenter)

        ## Add to general layout
        QtO.add_widgets(genLayout, [boxHeader, optionsBox])

    ## General options
    def toggle_axes(self):
        if self.showAxes.isChecked():
            self.plotter.show_axes()
        else:
            self.plotter.hide_axes()

    def toggle_bounds(self):
        if self.showBounds.isChecked():
            self.plotter.add_bounding_box(reset_camera=False)
        else:
            self.plotter.remove_bounding_box()

    def toggle_grid(self):
        if self.showGrid.isChecked():
            self.plotter.show_bounds()

            ### A PR for the feature below was submitted to PyVista
            ### and will be implemented natively in when the PR is released
            axes_ranges = np.array(self.plotter.bounds)
            axes_ranges[::2] *= self.plotter._vv_resolution
            axes_ranges[1::2] *= self.plotter._vv_resolution
            axes_actor = self.plotter.renderer.cube_axes_actor
            axes_actor.SetXAxisRange(axes_ranges[0], axes_ranges[1])
            axes_actor.SetYAxisRange(axes_ranges[2], axes_ranges[3])
            axes_actor.SetZAxisRange(axes_ranges[4], axes_ranges[5])
        else:
            self.plotter.remove_bounds_axes()

    def update_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color = color.name()
            self.plotter.set_background(color=color)


class TubeOptions(QWidget):
    def __init__(self, plotter, meshes, actors, genOptions):
        super().__init__()
        # Initialization
        self.plotter = plotter
        self.meshes = meshes
        self.actors = actors
        self.genOptions = genOptions

        # Connect all of the legend toggling
        self.genOptions.showLegend.stateChanged.connect(self.toggle_legend)
        self.genOptions.legendUnit.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.fontSize.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.textColor.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.tickCount.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.legendDigits.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.legendFormat.currentIndexChanged.connect(self.toggle_legend)
        self.genOptions.legendOrientation.currentIndexChanged.connect(
            self.toggle_legend
        )
        self.mesh_clim = [0.01, 1]

        ### Main box layout
        tubeLayout = QtO.new_layout(self, orient="V", no_spacing=True)
        header = QLabel("<b>Vessel Visualization")
        self.tubeBox = QGroupBox()
        boxLayout = QtO.new_layout(self.tubeBox, "V", spacing=5)

        ## Tube visualization buttons
        tubeGroup = QFrame()
        tubeGroup.setStyleSheet("QFrame::{border: 0px;}")
        tubeGroupLayout = QtO.new_layout(tubeGroup, "V", margins=0)

        tubeButtons = QFrame()
        tubeButtons.setStyleSheet("border:0px;")
        tubeButtonLayout = QtO.new_layout(tubeButtons, "V", spacing=2, margins=0)
        self.noTubes = QtO.new_radio("None", None)
        self.noTubes.setChecked(True)
        self.noTubes.toggled.connect(self.remove_tube_actors)
        self.networkTubes = QtO.new_radio("Network Centerlines", self.add_vessels)
        self.scaledTubes = QtO.new_radio("Scaled Vessels", self.add_vessels)
        QtO.button_grouping([self.noTubes, self.networkTubes, self.scaledTubes])

        QtO.add_widgets(
            tubeButtonLayout,
            [self.noTubes, self.networkTubes, self.scaledTubes],
        )

        self.networkTubes.setDisabled(True)
        self.scaledTubes.setDisabled(True)

        ## Vessel color options - Three choices
        message = "Visualization options for rendered vasculature networks."
        self.tubeOptions = QtO.CollapsibleBox("Vessel Options", message)
        tubeOptionsLayout = QtO.new_layout(orient="V", margins=(10, 10, 0, 10))

        # Feature based color
        self.vesselFeatureColor = QtO.new_radio("Feature-Based Colors", None)
        self.vesselFeatureColor.setChecked(True)
        self.vesselFeatureColor.toggled.connect(self.update_vessel_feature)

        self.vesselScalarBox = QtO.new_widget()
        scalarBoxLayout = QtO.new_layout(self.vesselScalarBox, "V", no_spacing=True)
        self.vesselScalar = QtO.new_combo(
            ["Radius", "Length", "Tortuosity", "Volume", "Surface Area"],
            130,
            connect=self.update_vessel_feature,
        )
        self.cmap = QtO.new_combo(helpers.load_cmaps(), 130, connect=self.update_cmap)

        rangeLabel = QLabel("<center>Unit range:")
        unitMinMaxLine = QtO.new_widget()
        minmaxLayout = QtO.new_layout(unitMinMaxLine, no_spacing=True)
        self.unitMin = QtO.new_doublespin(
            0,
            1000000,
            0.1,
            decimals=2,
            connect=self.update_clim,
            connect_type="valueChanged",
        )
        unitTo = QLabel("to")
        self.unitMax = QtO.new_doublespin(
            0.01,
            1000000,
            1,
            decimals=2,
            connect=self.update_clim,
            connect_type="valueChanged",
        )
        QtO.add_widgets(minmaxLayout, [self.unitMin, unitTo, self.unitMax])

        self.resetRange = QtO.new_button("Reset range", self.reset_clim)

        QtO.add_widgets(
            scalarBoxLayout,
            [
                QLabel("Feature:"),
                self.vesselScalar,
                5,
                QLabel("Color map:"),
                self.cmap,
                5,
                rangeLabel,
                5,
                unitMinMaxLine,
                5,
                [self.resetRange, "Center"],
            ],
        )

        # Single color
        self.vesselSingleColor = QtO.new_radio("Single Color", self.update_vessel_color)
        self.vesselColorBox = QtO.new_widget()
        vColorLayout = QtO.new_layout(self.vesselColorBox, no_spacing=True)
        vColorHeader = QLabel("Color:")
        self.vesselColor = QtO.new_widget(20, 20, color=[255, 205, 5])
        self.updateVesselColor = QtO.new_button("Change...", self.color_change, 90)
        QtO.add_widgets(
            vColorLayout,
            [
                0,
                vColorHeader,
                4,
                self.vesselColor,
                4,
                self.updateVesselColor,
                0,
            ],
        )
        self.vesselColorBox.hide()

        # Annotation colors
        self.vesselAnnotationColor = QtO.new_radio(
            "Annotation Colors", self.update_vessel_annotation
        )
        self.vesselAnnotationBox = QtO.new_widget()
        vAnnotationLayout = QtO.new_layout(
            self.vesselAnnotationBox, "V", no_spacing=True
        )
        vAnnotationHeader = QLabel("Annotation color:")
        self.vesselAnnotationType = QtO.new_combo(
            ["Original", "Rainbow", "Shifted"],
            connect=self.update_vessel_annotation,
        )
        QtO.add_widgets(
            vAnnotationLayout, [vAnnotationHeader, self.vesselAnnotationType]
        )
        self.vesselAnnotationBox.hide()

        QtO.button_grouping(
            [
                self.vesselFeatureColor,
                self.vesselSingleColor,
                self.vesselAnnotationColor,
            ]
        )

        QtO.add_widgets(
            tubeOptionsLayout,
            [
                self.vesselFeatureColor,
                self.vesselScalarBox,
                self.vesselSingleColor,
                self.vesselColorBox,
                self.vesselAnnotationColor,
                self.vesselAnnotationBox,
            ],
        )

        self.tubeOptions.setContentLayout(tubeOptionsLayout)
        QtO.add_widgets(tubeGroupLayout, [tubeButtons, self.tubeOptions])

        ## Branches and ends
        # region
        beBox = QFrame()
        beBox.setStyleSheet("QFrame::{border:0px;}")
        beBoxLayout = QtO.new_layout(beBox, "V", margins=0)

        ## Branches
        self.showBranches = QtO.new_checkbox("Show branch points", self.add_branches)
        # Branch color box
        message = "Color options for rendered branch points."
        self.branchBox = QtO.CollapsibleBox("Branch Point Options", message)
        branchBoxLayout = QtO.new_layout(orient="V", margins=(10, 10, 0, 10))

        # single color
        self.branchSingleColor = QtO.new_radio("Single Color")
        self.branchSingleColor.setChecked(True)
        self.branchSingleColor.toggled.connect(self.update_branch_color)
        self.brColorLine = QtO.new_widget()
        brColorLayout = QtO.new_layout(self.brColorLine, no_spacing=True)
        brHeader = QLabel("Color:")
        self.branchColor = QtO.new_widget(20, 20, color=[255, 0, 0])
        self.updateBranchColor = QtO.new_button("Change...", self.color_change, 90)
        QtO.add_widgets(
            brColorLayout,
            [0, brHeader, 4, self.branchColor, 4, self.updateBranchColor, 0],
        )

        # annotation color
        self.branchAnnotationColor = QtO.new_radio(
            "Annotation Colors", self.update_branch_annotation
        )
        self.aBranchColorBox = QtO.new_widget()
        aBCBoxLayout = QtO.new_layout(self.aBranchColorBox, "V", no_spacing=True)
        branchAnnotationHeader = QLabel("Annotation color:")
        self.branchAnnotationType = QtO.new_combo(
            ["Original", "Rainbow", "Shifted"],
            connect=self.update_branch_annotation,
        )
        QtO.add_widgets(
            aBCBoxLayout, [branchAnnotationHeader, self.branchAnnotationType]
        )
        self.aBranchColorBox.hide()

        QtO.add_widgets(
            branchBoxLayout,
            [
                self.branchSingleColor,
                self.brColorLine,
                self.branchAnnotationColor,
                self.aBranchColorBox,
            ],
        )
        self.branchBox.setContentLayout(branchBoxLayout)

        # connect toggles for visibility
        self.showBranches.stateChanged.connect(self.branchBox.setVisible)
        self.branchSingleColor.toggled.connect(self.brColorLine.setVisible)
        self.branchAnnotationColor.toggled.connect(self.aBranchColorBox.setVisible)

        ## Ends
        self.showEnds = QtO.new_checkbox("Show end points", self.add_ends)
        # End color box
        message = "Color options for rendered end points."
        self.endBox = QtO.CollapsibleBox("End Point Options", message)
        endBoxLayout = QtO.new_layout(orient="V", margins=(10, 10, 0, 10))

        # Single color
        self.endSingleColor = QtO.new_radio("Single Color")
        self.endSingleColor.setChecked(True)
        self.endSingleColor.toggled.connect(self.update_end_color)
        self.endColorLine = QtO.new_widget()
        endColorLayout = QtO.new_layout(self.endColorLine, no_spacing=True)
        endHeader = QLabel("Color:")
        self.endColor = QtO.new_widget(20, 20, color=[0, 255, 0])
        self.updateEndColor = QtO.new_button("Change...", self.color_change, 90)
        QtO.add_widgets(
            endColorLayout,
            [0, endHeader, 4, self.endColor, 4, self.updateEndColor, 0],
        )

        # annotation color
        self.endAnnotationColor = QtO.new_radio(
            "Annotation Colors", self.update_end_annotation
        )
        self.aEndColorBox = QtO.new_widget()
        aECBoxLayout = QtO.new_layout(self.aEndColorBox, "V", no_spacing=True)
        endAnnotationHeader = QLabel("Annotation color:")
        self.endAnnotationType = QtO.new_combo(
            ["Original", "Rainbow", "Shifted"],
            connect=self.update_end_annotation,
        )
        QtO.add_widgets(aECBoxLayout, [endAnnotationHeader, self.endAnnotationType])
        self.aEndColorBox.hide()

        QtO.add_widgets(
            endBoxLayout,
            [
                self.endSingleColor,
                self.endColorLine,
                self.endAnnotationColor,
                self.aEndColorBox,
            ],
        )
        self.endBox.setContentLayout(endBoxLayout)

        # connect toggles for visibility
        self.showEnds.stateChanged.connect(self.endBox.setVisible)
        self.endSingleColor.toggled.connect(self.endColorLine.setVisible)
        self.endAnnotationColor.toggled.connect(self.aEndColorBox.setVisible)

        # Add the four regions to our beBox
        QtO.add_widgets(
            beBoxLayout,
            [self.showBranches, self.branchBox, self.showEnds, self.endBox, 5],
        )

        # endregion

        ## Randomizae annotation color
        self.randomizeAnnotations = QtO.new_button(
            "Randomize annotations...", self.randomize_annotation_color, 180
        )
        self.randomizeAnnotations.hide()

        ### Add all of the options to the box layout
        line0 = QtO.new_line()
        line1 = QtO.new_line()
        QtO.add_widgets(
            boxLayout,
            [
                tubeGroup,
                5,
                line0,
                beBox,
                line1,
                5,
                [self.randomizeAnnotations, "Center"],
            ],
        )

        QtO.add_widgets(tubeLayout, [header, self.tubeBox])

        self.tubeOptions.setVisible(False)
        self.tubeOptions.lock(True)
        self.branchBox.setVisible(False)
        self.branchBox.lock(True)
        self.endBox.setVisible(False)
        self.endBox.lock(True)

        self.tubeBox.setDisabled(True)

        return

    ## Mesh loading and removal
    # region
    def remove_tube_actors(self):
        self.showBranches.setChecked(False)
        self.showEnds.setChecked(False)
        self.genOptions.showLegend.setChecked(False)
        self.tubeOptions.lock(True)
        self.tubeOptions.setVisible(False)
        self.actors.destroy_vessel_actors(self.plotter)
        return

    @pyqtSlot()
    def add_vessels(self):
        if not self.sender().isChecked():
            return

        # Clear old actors in case switching from
        self.remove_tube_actors()
        self.tubeOptions.setVisible(True)
        self.tubeOptions.lock(False)

        # Get the vessel actors
        scalars = helpers.get_scalar(self.vesselScalar)
        if self.sender() == self.networkTubes:
            meshes = [self.meshes.network, self.meshes.network_caps]
        elif self.sender() == self.scaledTubes:
            meshes = [self.meshes.scaled, self.meshes.scaled_caps]

        # Add the actors
        scalars = helpers.get_scalar(self.vesselScalar)
        self.actors.vessels = self.plotter.add_mesh(
            meshes[0],
            scalars=scalars,
            smooth_shading=True,
            show_scalar_bar=False,
            reset_camera=False,
        )
        self.actors.vessel_caps = self.plotter.add_mesh(
            meshes[1],
            scalars=scalars,
            smooth_shading=True,
            show_scalar_bar=False,
            reset_camera=False,
        )

        # Update the colors for the vessels
        if self.vesselFeatureColor.isChecked():
            self.update_vessel_feature()
        elif self.vesselSingleColor.isChecked():
            self.update_vessel_color()
        elif self.vesselAnnotationColor.isChecked():
            self.update_vessel_annotation()

        # Update the size of the ends and Branches
        if self.showBranches.isChecked():
            self.add_branches()
        if self.showEnds.isChecked():
            self.add_ends()

        # Refresh the colormap
        self.update_cmap()
        return

    # region
    def add_branches(self):
        show_branches = True if self.showBranches.isChecked() else False

        # Wipe the actor
        if self.actors.branches:
            self.plotter.remove_actor(self.actors.branches, reset_camera=False)
            self.actors.branches = None

        if show_branches:
            # Add the correct meshes
            if self.networkTubes.isChecked():
                mesh = self.meshes.network_branches
            elif self.scaledTubes.isChecked():
                mesh = self.meshes.scaled_branches
            else:
                mesh = (
                    self.meshes.network_branches
                    if self.meshes.network
                    else self.meshes.scaled_branches
                )

            self.actors.branches = self.plotter.add_mesh(
                mesh,
                show_scalar_bar=False,
                smooth_shading=True,
                reset_camera=False,
            )

            # Update the colors
            if self.branchSingleColor.isChecked():
                self.update_branch_color()
            elif self.branchAnnotationColor.isChecked():
                self.update_branch_annotation()

        self.branchBox.lock(not show_branches)
        self.branchBox.setVisible(show_branches)
        return

    def add_ends(self):
        show_ends = True if self.showEnds.isChecked() else False

        # Wipe the actor
        if self.actors.ends:
            self.plotter.remove_actor(self.actors.ends, reset_camera=False)
            self.actors.ends = None

        if show_ends:
            # Add the correct meshes
            if self.networkTubes.isChecked():
                mesh = self.meshes.network_ends
            elif self.scaledTubes.isChecked():
                mesh = self.meshes.scaled_ends
            else:  # If neither are checked, default to the network
                mesh = (
                    self.meshes.network_ends
                    if self.meshes.network
                    else self.meshes.scaled_ends
                )

            self.actors.ends = self.plotter.add_mesh(
                mesh,
                show_scalar_bar=False,
                smooth_shading=True,
                reset_camera=False,
            )

            # Update the colors
            if self.endSingleColor.isChecked():
                self.update_end_color()
            elif self.endAnnotationColor.isChecked():
                self.update_end_annotation()

        self.endBox.lock(not show_ends)
        self.endBox.setVisible(show_ends)
        return

    # endregion
    # endregion

    ## Mesh clim updates based on genoptions changes
    # region
    @pyqtSlot()
    def update_clim(self):
        QtO.signal_block(True, [self.unitMin, self.unitMax])
        min = self.unitMin.value()
        max = self.unitMax.value()
        if self.sender() is self.unitMin and min >= max:
            max = min + 0.1
            self.unitMax.setValue(max)
        elif self.sender() is self.unitMax and max <= min:
            if min == 0.1:
                max = 0.2
                self.unitMax.setValue(max)
            else:
                min = max - 0.1
                self.unitMin.setValue(min)

        for actor in self.get_vessel_actors():
            mapper = actor.GetMapper()
            mapper.scalar_range = [min, max]

        QtO.signal_block(False, [self.unitMin, self.unitMax])
        return

    def reset_clim(self, loading=False):
        QtO.signal_block(True, [self.unitMin, self.unitMax])
        self.unitMin.setValue(self.mesh_clim[0])
        self.unitMax.setValue(self.mesh_clim[1])
        QtO.signal_block(False, [self.unitMin, self.unitMax])
        if not loading:
            self.update_clim()
        return

    def retrieve_mesh_clim(self):
        scalar = helpers.get_scalar(self.vesselScalar)
        if self.meshes.network:
            mesh = self.meshes.network
        elif self.meshes.scaled:
            mesh = self.meshes.scaled

        clim = helpers.get_clim(mesh, scalar)
        return clim

    # endregion

    ## Legend processing and button locking
    # region
    def toggle_legend(self):
        show = self.genOptions.showLegend.isChecked()
        if self.actors.vessels:
            actor = self.actors.vessels
        else:
            return

        title = self.vesselScalar.currentText()
        if title != "Tortuosity":
            unit = self.genOptions.legendUnit.currentText()
            if title == "Surface Area":
                unit = " (" + unit + "\u00b2)"
            elif title == "Volume":
                if unit == "px":
                    unit = " (vx)"
                else:
                    unit = " (" + unit + "\u00b3)"
            else:
                unit = " (" + unit + ")"
            title += unit

        if show:
            helpers.remove_legend(self.plotter, actor)
            # self.plotter.remove_scalar_bar()

            color = self.genOptions.textColor.currentText().lower()
            n_labels = int(self.genOptions.tickCount.currentText())

            # Font size
            size = int(self.genOptions.fontSize.currentText())
            title_size, label_size = size + 2, size

            digits = int(self.genOptions.legendDigits.currentText())
            if self.genOptions.legendFormat.currentText() != "Mixed":
                fmt = self.genOptions.legendFormat.currentText()
                fmt = "f" if fmt == "Float" else "E"
                fmt = f"%#.{digits}{fmt}"
            else:
                fmt = f"%#.{digits}G"

            vertical = self.genOptions.legendOrientation.currentText() == "Vertical"
            if vertical:
                width = 0.05
                height = 0.09 * n_labels
                x_pos = 0.92 - 0.02 * label_size / 16
                y_pos = 0.035
            else:
                width = 0.06 * n_labels
                height = min(0.08, 0.07 * label_size / 16)
                x_pos = 0.65 + (0.06 * (5 - n_labels))
                y_pos = 0.04

            ## Scalar bar removal issue with PyVista
            slot = min(self.plotter._scalar_bar_slots)
            self.plotter._scalar_bar_slots.remove(slot)
            self.plotter._scalar_bar_slot_lookup[title] = slot

            self.plotter.add_scalar_bar(
                title=title,
                mapper=actor.GetMapper(),
                n_labels=n_labels,
                color=color,
                title_font_size=title_size,
                label_font_size=label_size,
                width=width,
                height=height,
                position_x=x_pos,
                position_y=y_pos,
                vertical=vertical,
                n_colors=256,
                fmt=fmt,
            )

        else:
            helpers.remove_legend(self.plotter, actor)
            # self.plotter.remove_scalar_bar()
        self.genOptions.legendOptions.lock(not show)
        return

    def update_legend_lock(self):
        # Legend locking
        lock = (
            self.noTubes.isChecked()
            or self.vesselSingleColor.isChecked()
            or self.vesselAnnotationColor.isChecked()
        )
        if lock:
            self.genOptions.showLegend.setChecked(not lock)
        self.genOptions.showLegend.setDisabled(lock)
        self.genOptions.legendOptions.lock(lock)
        return

    def update_vessel_locking(
        self, show_feature=False, show_color=False, show_annotation=False
    ):
        self.vesselScalarBox.setVisible(show_feature)
        self.vesselColorBox.setVisible(show_color)
        self.vesselAnnotationBox.setVisible(show_annotation)
        self.update_legend_lock()
        return

    def toggle_randomization_lock(self):
        show = any(
            [
                self.vesselAnnotationColor.isChecked(),
                self.branchAnnotationColor.isChecked(),
                self.endAnnotationColor.isChecked(),
            ]
        )
        self.randomizeAnnotations.setVisible(show)

    # endregion

    ## Mesh color and scalar updating
    # region
    def update_vessel_feature(self):
        if not self.vesselFeatureColor.isChecked():
            return
        self.update_vessel_locking(show_feature=True)
        self.render_feature()
        return

    def update_vessel_color(self):
        if not self.vesselSingleColor.isChecked():
            return
        self.update_vessel_locking(show_color=True)
        rgb = helpers.get_widget_rgb(self.vesselColor)
        self.render_color(self.get_vessel_actors(), rgb)
        return

    def update_vessel_annotation(self):
        self.toggle_randomization_lock()
        if not self.vesselAnnotationColor.isChecked():
            return
        self.update_vessel_locking(show_annotation=True)
        annotation = f"{self.vesselAnnotationType.currentText()}_RGB"
        self.meshes.update_vessel_scalars(annotation)
        self.render_annotation(self.get_vessel_actors())
        return

    def update_branch_color(self):
        if not self.branchSingleColor.isChecked():
            return
        rgb = helpers.get_widget_rgb(self.branchColor)
        self.render_color([self.actors.branches], rgb)
        return

    def update_branch_annotation(self):
        self.toggle_randomization_lock()
        if not self.branchAnnotationColor.isChecked():
            return
        annotation = f"{self.branchAnnotationType.currentText()}_RGB"
        self.meshes.update_branch_scalars(annotation)
        self.render_annotation([self.actors.branches])
        return

    def update_end_color(self):
        if not self.endSingleColor.isChecked():
            return
        rgb = helpers.get_widget_rgb(self.endColor)
        self.render_color([self.actors.ends], rgb)
        return

    def update_end_annotation(self):
        self.toggle_randomization_lock()
        if not self.endAnnotationColor.isChecked():
            return
        annotation = f"{self.endAnnotationType.currentText()}_RGB"
        self.meshes.update_end_scalars(annotation)
        self.render_annotation([self.actors.ends])
        return

    def randomize_annotation_color(self):
        annotation_types = [
            self.vesselAnnotationType.currentText(),
            self.branchAnnotationType.currentText(),
            self.endAnnotationType.currentText(),
        ]
        rainbow = "Rainbow" in annotation_types
        shifted = "Shifted" in annotation_types
        helpers.randomize_mesh_colors(self.meshes, rainbow, shifted)
        if self.actors.vessels:
            self.update_vessel_annotation()
        if self.actors.branches:
            self.update_branch_annotation()
        if self.actors.ends:
            self.update_end_annotation()
        return

    # Color rendering
    def render_feature(self):
        scalar = helpers.get_scalar(self.vesselScalar)
        self.meshes.update_vessel_scalars(scalar)
        clim = self.retrieve_mesh_clim()
        self.mesh_clim = clim
        for actor in self.get_vessel_actors():
            mapper = actor.GetMapper()
            mapper.scalar_range = clim
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarVisibility(True)
        self.reset_clim()
        self.genOptions.showLegend.setChecked(True)
        self.toggle_legend()
        return

    def render_color(self, actors, rgb):
        for actor in actors:
            mapper = actor.GetMapper()
            mapper.SetColorModeToDefault()
            actor.GetProperty().SetColor(rgb)
            mapper.SetScalarVisibility(False)
        return

    def render_annotation(self, actors):
        for actor in actors:
            mapper = actor.GetMapper()
            mapper.SetColorModeToDirectScalars()
            mapper.SetScalarVisibility(True)
        return

    def get_vessel_actors(self):
        actors = [self.actors.vessels, self.actors.vessel_caps]
        return actors

    # Color change handling
    @pyqtSlot()
    def color_change(self):
        color = QColorDialog.getColor()
        if color.isValid():
            sender = self.sender()
            rgb = [color.red(), color.green(), color.blue()]
            if sender == self.updateBranchColor:
                widget = self.branchColor
                actors = [self.actors.branches]
            elif sender == self.updateEndColor:
                widget = self.endColor
                actors = [self.actors.ends]
            elif sender == self.updateVesselColor:
                widget = self.vesselColor
                actors = [self.actors.vessels, self.actors.vessel_caps]

            # update the widget color
            helpers.update_widget_color(widget, rgb)
            self.render_color(actors, helpers.get_widget_rgb(widget))
        return

    def update_cmap(self):
        colormap = self.cmap.currentText().lower()
        colortable = helpers.get_colortable(colormap)
        actors = [self.actors.vessels, self.actors.vessel_caps]
        for actor in actors:
            mapper = actor.GetMapper()
            mapper.cmap = colormap
            table = mapper.GetLookupTable()
            table.SetTable(pv._vtk.numpy_to_vtk(colortable))
        return

    # endregion

    ## Meshes updater
    def load_meshes(self, meshes, annotation):
        self.meshes = meshes
        self.networkTubes.setDisabled(self.meshes.network is None)
        self.scaledTubes.setDisabled(self.meshes.scaled is None)
        self.vesselAnnotationColor.setVisible(annotation != "None")
        self.branchAnnotationColor.setVisible(annotation != "None")
        self.endAnnotationColor.setVisible(annotation != "None")

        QtO.signal_block(
            True,
            [
                self.vesselFeatureColor,
                self.branchSingleColor,
                self.endSingleColor,
            ],
        )
        self.vesselFeatureColor.setChecked(True)
        self.branchSingleColor.setChecked(True)
        self.endSingleColor.setChecked(True)
        QtO.signal_block(
            False,
            [
                self.vesselFeatureColor,
                self.branchSingleColor,
                self.endSingleColor,
            ],
        )


class VolumeOptions(QWidget):
    def __init__(self, plotter, meshes, actors):
        super().__init__()
        self.plotter = plotter
        self.meshes = meshes
        self.actors = actors

        pageLayout = QtO.new_layout(self, "V", no_spacing=True)
        header = QLabel("<b>Volume Visualization")

        # Options box
        # three button setup
        self.volumeBox = QGroupBox()
        boxLayout = QtO.new_layout(self.volumeBox, "V", spacing=5)

        volumeGroup = QFrame()
        volumeGroup.setStyleSheet("border: 0px;")
        volumeGroupLayout = QtO.new_layout(volumeGroup, "V", spacing=2, margins=0)

        self.noVolume = QtO.new_radio("None", self.remove_volume_actors)
        self.originalVolume = QtO.new_radio("Original", self.add_volume)
        self.smoothedVolume = QtO.new_radio("Smoothed", self.add_volume)
        QtO.add_widgets(
            volumeGroupLayout,
            [self.noVolume, self.originalVolume, self.smoothedVolume],
        )

        self.originalVolume.setDisabled(True)
        self.smoothedVolume.setDisabled(True)

        ## Volume options
        message = "Visualization options for rendered volumes"
        self.volumeOptions = QtO.CollapsibleBox("Volume Options", message)
        optionsLayout = QtO.new_layout(None, "V", spacing=5, margins=(10, 10, 0, 10))

        colorLine = QtO.new_widget()
        colorLayout = QtO.new_layout(colorLine, no_spacing=True)
        colorLabel = QLabel("Color:")
        self.volumeColor = QtO.new_widget(20, 20, color=[255, 255, 255])
        changeColor = QtO.new_button("Change...", self.color_change, 90)
        QtO.add_widgets(colorLayout, [colorLabel, 4, self.volumeColor, 4, changeColor])

        opacityLine = QtO.new_widget()
        opacityLayout = QtO.new_layout(opacityLine, no_spacing=True)
        opacityHeader = QLabel("Opacity:")
        self.volumeOpacity = QtO.new_spinbox(
            0,
            100,
            100,
            step=10,
            suffix="%",
            connect=self.update_opacity,
            connect_type="valueChanged",
        )
        QtO.add_widgets(opacityLayout, [opacityHeader, 4, self.volumeOpacity])

        QtO.add_widgets(optionsLayout, [colorLine, opacityLine], "Center")
        self.volumeOptions.setContentLayout(optionsLayout)

        ## Add all of the buttons togeter now
        QtO.add_widgets(boxLayout, [volumeGroup, self.volumeOptions])

        QtO.add_widgets(pageLayout, [header, self.volumeBox])

        self.noVolume.setChecked(True)
        self.volumeBox.setDisabled(True)
        return

    ## Actor addition and removal
    def remove_volume_actors(self):
        self.actors.destroy_volume_actors(self.plotter)
        self.toggle_options()

        self.volumeOptions.lock(True)
        self.volumeOptions.setVisible(False)
        return

    @pyqtSlot()
    def add_volume(self):
        sender = self.sender()
        if not sender.isChecked():
            return

        # Find mesh to add
        if sender == self.originalVolume:
            mesh = self.meshes.original
            smooth_shading = False
        elif sender == self.smoothedVolume:
            mesh = self.meshes.smoothed
            smooth_shading = True

        # Unlock options box
        self.volumeOptions.lock(False)
        self.volumeOptions.setVisible(True)

        # remove old meshes
        self.remove_volume_actors()
        self.actors.volume = self.plotter.add_mesh(
            mesh,
            show_scalar_bar=False,
            reset_camera=False,
            smooth_shading=smooth_shading,
        )
        self.toggle_options()
        self.update_opacity()
        self.update_volume_color()
        return

    ## Volume mesh property updates
    def color_change(self):
        color = QColorDialog.getColor()
        if color.isValid():
            rgb = [color.red(), color.green(), color.blue()]
            helpers.update_widget_color(self.volumeColor, rgb)
            self.update_volume_color()
        return

    def update_volume_color(self):
        color = helpers.get_widget_rgb(self.volumeColor)
        actor = self.actors.volume
        # mapper = actor.GetMapper()
        actor.GetProperty().SetColor(color)
        return

    def update_opacity(self):
        opacity = self.volumeOpacity.value() / 100
        property = self.actors.volume.GetProperty()
        property.SetOpacity(opacity)
        return

    ## Button toggling
    def toggle_options(self):
        checked = self.noVolume.isChecked()
        self.volumeOptions.lock(checked)
        self.volumeOptions.setVisible(not checked)
        return

    def load_meshes(self, meshes):
        self.meshes = meshes
        self.originalVolume.setDisabled(self.meshes.original is None)
        self.smoothedVolume.setDisabled(self.meshes.smoothed is None)


###############
### Testing ###
###############
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = mainWindow()
    sys.exit(app.exec_())
