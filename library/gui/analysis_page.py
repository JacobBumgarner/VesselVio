"""
The PyQt5 code used to build the analysis page for the program.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os
import sys

from library import helpers, input_classes as IC, qt_threading as QtTh

from library.annotation_processing import RGB_check
from library.gui import qt_objects as QtO
from library.gui.annotation_page import RGB_Warning

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLayout,
    QMainWindow,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QWidget,
)


class mainWindow(QMainWindow):
    """A main window for development and testing of the analysis page only"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Annotation Testing")
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        layout = QtO.new_layout(None, "H", True, "None")
        self.centralWidget.setLayout(layout)

        annotationpage = AnalysisPage()

        layout.addWidget(annotationpage)

        self.show()


class AnalysisPage(QWidget):
    """The page used for batch processing and analysis of segmented vasculature
    datasets."""

    def __init__(self):
        super().__init__()
        self.analyzed = False
        ## This page is organized into to vertical sections.

        pageLayout = QtO.new_layout(self, "V", spacing=5, margins=20)

        ## Top section - file loading and processing
        self.Loading = LoadingWidget()
        self.Loading.loadButton.clicked.connect(self.load_files)

        ### Botom section - analysis and graph loading options
        # three column horizontal
        self.bottomWidget = QtO.new_widget()
        self.bottomWidget.setFixedHeight(250)
        bottomLayout = QtO.new_layout(self.bottomWidget, no_spacing=True)

        # Left column is a spacer
        spacer = QtO.new_widget(150)

        # Middle column is a tab widget
        self.analysisOptions = AnalysisOptions()
        self.graphOptions = GraphOptions(self.Loading.fileSheet)
        self.optionsTab = QTabWidget()
        self.optionsTab.addTab(self.analysisOptions, "Analysis Options")
        self.optionsTab.addTab(self.graphOptions, "Graph File Options")
        # Connect the loading filetype to the second options tab
        self.optionsTab.setTabEnabled(1, False)
        self.Loading.datasetType.currentIndexChanged.connect(self.update_table_view)

        # Bottom right column
        rightColumn = QtO.new_layout(orient="V", spacing=13)
        self.analyzeButton = QtO.new_button("Analyze", self.run_analysis)
        self.cancelButton = QtO.new_button("Cancel", self.cancel_analysis)
        self.cancelButton.setDisabled(True)
        QtO.add_widgets(rightColumn, [0, self.analyzeButton, self.cancelButton, 0])

        QtO.add_widgets(bottomLayout, [spacer, 0, self.optionsTab, rightColumn, 0])

        ## Add it all together
        QtO.add_widgets(pageLayout, [self.Loading, self.bottomWidget])

    ## File loading
    def load_files(self):
        """File loading. Manages loading segmented files, annotation files,
        and graph files for batch analysis."""
        dataset_type = self.Loading.datasetType.currentText()
        annotation = self.Loading.annotationType.currentText()
        graph_format = self.graphOptions.graphFormat.currentText()

        c1files, c2files = None, None
        if annotation == "None" and dataset_type == "Volume":
            c1files = helpers.load_volumes()
        elif dataset_type == "Graph" and graph_format != "CSV":
            c1files = helpers.load_graphs(graph_format)
        else:
            self.loader = FileLoader(dataset_type, annotation, graph_format)
            if self.loader.exec_():
                if self.loader.column1_files:
                    c1files = self.loader.column1_files
                if self.loader.column2_files:
                    c2files = self.loader.column2_files
            del self.loader

        if self.analyzed:
            self.Loading.clear_files()
            self.analyzed = False
        if c1files:
            self.Loading.column1_files += c1files
            self.Loading.add_column1_files()
        if c2files:
            self.Loading.column2_files += c2files
            self.Loading.add_column2_files()

        return

    # Analysis Processing
    def run_analysis(self):
        """Prepares and initiates the analysis of the loaded files, if there
        are any.

        Workflow:
        1. Check to ensure that the appropriate files have been loaded for the
        analysis.

        2. Connects the appropriate QThread to the appropriate buttons and
        selection signals.

        3. Starts the QThread
        """
        # If an analysis has already been run, make sure new files are loaded.
        if self.analyzed:
            self.analysis_warning()
            return

        # Make sure the appropriate files are loaded
        if not self.file_check():
            self.analysis_warning()
            return

        # Check for the loaded files and initialize the appropriate QThread
        if self.Loading.datasetType.currentText() == "Volume":
            self.initialize_volume_analysis()
        elif self.Loading.datasetType.currentText() == "Graph ":
            self.initialize_graph_analysis()

        self.a_thread.button_lock.connect(self.button_locking)
        self.a_thread.selection_signal.connect(self.Loading.update_row_selection)
        self.a_thread.analysis_status.connect(self.Loading.update_status)
        self.a_thread.start()
        self.analyzed = True
        return

    # Volume analysis
    def initialize_volume_analysis(self):
        """Creates an analysis thread for volume-based analysis. Loads and
        prepares the relevant volume analysis options."""
        analysis_options = self.analysisOptions.prepare_options(
            self.Loading.results_folder
        )
        analysis_options.annotation_type = self.Loading.annotationType.currentText()
        self.a_thread = QtTh.VolumeThread(
            analysis_options,
            self.Loading.column1_files,
            self.Loading.column2_files,
            self.Loading.annotation_data,
        )
        return

    def initialize_graph_analysis(self):
        """Creates an analysis thread for graph-based analysis. Loads and
        prepares the relevant graph analysis options."""
        analysis_options = self.analysisOptions.prepare_options(
            self.Loading.results_folder
        )
        graph_options = self.graphOptions.prepare_options()
        self.a_thread = QtTh.GraphThread(
            analysis_options,
            graph_options,
            self.Loading.column1_files,
            self.Loading.column2_files,
        )
        return

    def cancel_analysis(self):
        """Once called, triggers the analysis thread to stop the analysis at the
        next breakpoint."""
        # Disable the cancel button after the request is sent.
        self.cancelButton.setDisabled(True)
        self.a_thread.stop()
        return

    def button_locking(self, lock_state):
        """Toggles button disables for any relevant buttons or options during
        the analysis. Also serves to trigger any relevant log

        Parameters:
        lock_state : bool
            Enables/Disables the relevant buttons based on the lock state.
            Some buttons will be disabled, some will be enabled.
            The lock_state bool status is relevant for the 'setEnabled' or
            'setDisabled' call.
        """
        self.cancelButton.setEnabled(lock_state)
        self.Loading.loadingColumn.setDisabled(lock_state)
        self.Loading.changeFolder.setDisabled(lock_state)
        self.analyzeButton.setDisabled(lock_state)
        return

    def file_check(self):
        """Checks to ensure that the appropriate files have been loaded for
        the current analysis.

        Returns
        -------
        bool
            True if loaded correctly, False if incorrectly or incompletely
            loaded
        """
        if not self.Loading.column1_files:  # General file check
            return False

        if self.Loading.datasetType.currentText() == "Volume":  # Specific check
            if self.Loading.annotationType.currentText() != "None":
                if not self.column_file_check() or self.Loading.annotation_data:
                    return False
        if self.Loading.datasetType.currentText() == "Graph":
            if self.graphOptions.graphFormat.currentText() == "CSV":
                if not self.column_file_check():
                    return False
        return True

    def column_file_check(self):
        """Ensures that the column1_files and column2_files have the same number
        of loaded files.

        Returns
        -------
        bool
            True if the number of files match, False if they are different
        """
        file_check = len(self.Loading.column1_files) == len(self.Loading.column2_files)
        return file_check

    # Warnings
    def analysis_warning(self):
        """Creates a message box to indicate that the appropriate files have not
        been loaded."""
        msgBox = QMessageBox()
        message = "Load all files to run analysis."
        msgBox.setText(message)
        msgBox.exec_()

    def disk_space_warning(self, needed_space: float):
        """Creates a message box to indicate that at some point during the
        analysis, there was not enough disk space to conduct an annotation
        analysis."""
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Disk Space Error")
        message = (
            "<center>During the analysis, one or more files were unable to be",
            "analyzed because of insufficient free disk memory.<br><br>",
            "<center>To analyze annotated volume datasets, VesselVio will need",
            f"at least <u>{needed_space:.1f} GB</u> of free space.",
        )
        msgBox.setText(message)
        msgBox.exec_()

    # Tab viewing
    def update_table_view(self):
        """Updates the view of the file loading table. If an annotation-based
        analysis or a CSV graph-based analysis are selected, an additional
        column is added for the relevant files."""
        active = False
        if self.Loading.datasetType.currentText() == "Graph":
            active = True
            if self.graphOptions.graphFormat.currentText() != "CSV":
                self.Loading.fileSheet.init_default()
            else:
                self.Loading.fileSheet.init_csv()
        elif self.Loading.annotationType.currentText() != "None":
            self.Loading.fileSheet.init_annotation()
        self.optionsTab.setTabEnabled(1, active)
        return


class AnalysisOptions(QWidget):
    def __init__(self, vis_page=False):
        super().__init__()
        aBoxLayout = QtO.new_layout(self, "V")

        box = QtO.new_widget()
        boxLayout = QtO.new_layout(box)

        ## left column options
        leftColumn = QtO.new_form_layout(alignment="VCenter", vspacing=5)

        unitHeader = QLabel("Unit:")
        self.unit = QtO.new_combo(["µm", "mm"], 120, connect=self.update_units)

        resolutionHeader = QLabel("Resolution type:")
        self.resolutionType = QtO.new_combo(
            ["Isotropic", "Anisotropic"], 120, connect=self.update_isotropy
        )

        dimensionHeader = QLabel("Analysis dimensions:")
        self.imageDimension = QtO.new_combo(
            ["3D", "2D"], 120, connect=self.update_dimensions
        )

        QtO.add_form_rows(
            leftColumn,
            [
                [unitHeader, self.unit],
                [resolutionHeader, self.resolutionType],
                [dimensionHeader, self.imageDimension],
            ],
        )

        ## Right column options
        self.rightOptions = QtO.new_widget()
        self.rightOptionsLayout = QtO.new_layout(
            self.rightOptions, orient="V", spacing=5, margins=0
        )

        radiusLine = QtO.new_widget()
        rLayout = QtO.new_layout(radiusLine, margins=0)
        maxRadiusHeader = QLabel("Maximum radius:")
        self.maxRadius = QtO.new_spinbox(150, 500, 150, "Left", suffix=" µm")
        QtO.add_widgets(rLayout, [maxRadiusHeader, self.maxRadius])

        self.isoLine = QtO.new_widget()
        iLayout = QtO.new_layout(self.isoLine, margins=0)
        isoHeader = QLabel("Image resolution:")
        self.isoResolution = QtO.new_doublespin(
            0.01, 100, 1, 100, suffix=" µm\u00B3", decimals=2
        )
        QtO.add_widgets(iLayout, [isoHeader, self.isoResolution])

        self.anisoLine = QtO.new_widget()
        aLayout = QtO.new_layout(self.anisoLine, spacing=0, margins=0)
        self.anisoHeader = QLabel("Image resolution (XYZ):")
        self.anisoX = QtO.new_doublespin(0.01, 100, 1, width=60, decimals=2)
        self.anisoY = QtO.new_doublespin(0.01, 100, 1, width=60, decimals=2)
        self.anisoZ = QtO.new_doublespin(
            0.01, 100, 1, width=80, suffix=" µm\u00B3", decimals=2
        )
        QtO.add_widgets(
            aLayout, [self.anisoHeader, 6, self.anisoX, self.anisoY, self.anisoZ]
        )
        self.anisoLine.setVisible(False)

        self.filterLine = QtO.new_widget()
        fLayout = QtO.new_layout(self.filterLine, margins=0)
        self.filterHeader = QtO.new_checkbox("Filter isolated segments shorter than:")
        self.filterHeader.setChecked(True)
        self.filterSize = QtO.new_doublespin(0.01, 1000, 10, width=100, suffix=" µm")
        QtO.add_widgets(fLayout, [self.filterHeader, self.filterSize])

        self.pruneLine = QtO.new_widget()
        pLayout = QtO.new_layout(self.pruneLine, margins=0)
        self.pruneHeader = QtO.new_checkbox("Prune end point segments shorter than:")
        self.pruneHeader.setChecked(True)
        self.pruneSize = QtO.new_doublespin(0.01, 1000, 5, width=100, suffix=" µm")
        QtO.add_widgets(pLayout, [self.pruneHeader, self.pruneSize])

        segLine = QtO.new_widget()
        sLayout = QtO.new_layout(segLine, margins=0)
        self.saveSegmentResults = QtO.new_checkbox(
            "Export detailed segment features to individual csv files"
        )
        QtO.add_widgets(sLayout, [self.saveSegmentResults])

        graphLine = QtO.new_widget()
        gLayout = QtO.new_layout(graphLine, margins=0)
        self.saveGraph = QtO.new_checkbox("Save graph files of datasets")
        QtO.add_widgets(gLayout, [self.saveGraph])

        widgets = [self.isoLine, self.anisoLine, self.filterLine, self.pruneLine]

        if not vis_page:
            widgets += [segLine, graphLine]
        QtO.add_widgets(self.rightOptionsLayout, widgets, "Left")
        # self.rightOptions.setStyleSheet('border: 1px solid black;')

        ### Add it all together now
        line = QtO.new_line("V", 2)

        QtO.add_widgets(boxLayout, [0, leftColumn, line, self.rightOptions, 0])

        QtO.add_widgets(aBoxLayout, [0, box, 0])

    def update_dimensions(self):
        if self.imageDimension.currentText() == "2D":
            self.anisoLine.setVisible(False)
            self.isoLine.setVisible(True)
            self.resolutionType.setCurrentIndex(0)
        else:
            self.anisoHeader.setText("Image resolution (XYZ):")
        self.update_units()
        return

    def update_isotropy(self):
        iso_visible = True
        if self.resolutionType.currentText() == "Anisotropic":
            iso_visible = False
            self.imageDimension.setCurrentIndex(0)
        self.isoLine.setVisible(iso_visible)
        self.anisoLine.setVisible(not iso_visible)
        return

    def update_units(self):
        unit = " " + self.unit.currentText()
        exponent = "\u00B3"
        if self.imageDimension.currentText() == "2D":
            exponent = "\u00B2"
        suffix = unit + exponent
        self.isoResolution.setSuffix(suffix)
        self.anisoZ.setSuffix(suffix)
        self.filterSize.setSuffix(unit)
        self.pruneSize.setSuffix(unit)
        # self.maxRadius.setSuffix(unit)
        return

    def prepare_options(self, results_folder, visualization=False):
        # resolution

        image_dim = int(self.imageDimension.currentText()[0])

        if image_dim == 2 or self.resolutionType.currentText() == "Isotropic":
            resolution = self.isoResolution.value()
        elif self.resolutionType.currentText() == "Anisotropic":
            X = self.anisoX.value()
            Y = self.anisoY.value()
            Z = self.anisoZ.value()
            resolution = [X, Y, Z]

        if self.pruneHeader.isChecked():
            prune_length = self.pruneSize.value()
        else:
            prune_length = 0
        if self.filterHeader.isChecked():
            filter_length = self.filterSize.value()
        else:
            filter_length = 0
        # max_radius = self.maxRadius.value()
        max_radius = 150  # Vestigial

        if visualization:
            save_seg_results = False
            save_graph = False
        else:
            save_seg_results = self.saveSegmentResults.isChecked()
            save_graph = self.saveGraph.isChecked()

        analysis_options = IC.AnalysisOptions(
            results_folder,
            resolution,
            prune_length,
            filter_length,
            max_radius,
            save_seg_results,
            save_graph,
            image_dim,
        )

        return analysis_options


class GraphOptions(QWidget):
    def __init__(self, fileSheet=None):
        super().__init__()
        self.fileSheet = fileSheet

        self.setFixedWidth(800)
        boxLayout = QtO.new_layout(self, margins=10)

        ### Organized into three columns
        ## Left
        leftColumn = QtO.new_form_layout(alignment="VCenter", vspacing=5)

        formatHeader = QLabel("Graph file format:")
        self.graphFormat = QtO.new_combo(
            ["GraphML", "DIMACS", "GML", "CSV"], 120, connect=self.update_graph_options
        )

        typeHeader = QLabel("Vertex representation:")
        self.graphType = QtO.new_combo(
            ["Branches", "Centerlines"], 120, "Left", self.update_graph_type
        )

        delimiterHeader = QLabel("CSV Delimiter:")
        self.delimiterCombo = QtO.new_combo(
            [",", ";", "Tab (\\t)", "Space ( )"],
            120,
        )
        self.delimiterCombo.setDisabled(True)

        self.clLabel = QLabel("")
        self.centerlineLine = QtO.new_widget()
        clLayout = QtO.new_layout(self.centerlineLine, no_spacing=True)
        self.centerlineSmoothing = QtO.new_checkbox("Centerline smoothing")
        QtO.add_widgets(clLayout, [self.centerlineSmoothing])

        self.cliqueLabel = QLabel("")
        self.cliqueLine = QtO.new_widget()
        cliqueLayout = QtO.new_layout(self.cliqueLine, no_spacing=True)
        self.cliqueFiltering = QtO.new_checkbox("Clique filtering")
        QtO.add_widgets(cliqueLayout, [self.cliqueFiltering])

        QtO.add_form_rows(
            leftColumn,
            [
                [formatHeader, self.graphFormat],
                [typeHeader, self.graphType],
                [delimiterHeader, self.delimiterCombo],
                [self.clLabel, self.centerlineLine],
                [self.cliqueLabel, self.cliqueLine],
            ],
        )

        ## Middle
        self.middleColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        vertexHeader = QLabel("<b><center>Vertex identifiers:")
        QtO.add_widgets(headerLayout, [vertexHeader])

        xHeader = QLabel("X position:")
        self.xEdit = QtO.new_line_edit("X")

        yHeader = QLabel("Y position:")
        self.yEdit = QtO.new_line_edit("Y")

        zHeader = QLabel("Z position:")
        self.zEdit = QtO.new_line_edit("Z")

        radiusHeader = QLabel("Radius:")
        self.vertexRadiusEdit = QtO.new_line_edit("radius")
        self.vertexRadiusEdit.setDisabled(True)

        QtO.add_form_rows(
            self.middleColumn,
            [
                columnHeader,
                [xHeader, self.xEdit],
                [yHeader, self.yEdit],
                [zHeader, self.zEdit],
                [radiusHeader, self.vertexRadiusEdit],
            ],
        )

        ## Right
        rightColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        edgeHeader = QLabel("<b><center>Edge identifiers:")
        QtO.add_widgets(headerLayout, [edgeHeader])

        sourceHeader = QLabel("Edge source:")
        self.sourceEdit = QtO.new_line_edit("Source ID")
        self.sourceEdit.setDisabled(True)

        targetHeader = QLabel("Edge target:")
        self.targetEdit = QtO.new_line_edit("Target ID")
        self.targetEdit.setDisabled(True)

        segRadiusHeader = QLabel("Mean segment radius:")
        self.segRadiusEdit = QtO.new_line_edit("radius_avg")

        segLengthHeader = QLabel("Segment length:")
        self.segLengthEdit = QtO.new_line_edit("length")

        segTortHeader = QLabel("Segment tortuosity")
        self.segTortuosityEdit = QtO.new_line_edit("tortuosity")

        segVolumeHeader = QLabel("Segment volume:")
        self.segVolumeEdit = QtO.new_line_edit("volume")

        segSAHeader = QLabel("Segment surface area:")
        self.segSAEdit = QtO.new_line_edit("surface_area")

        QtO.add_form_rows(
            rightColumn,
            [
                columnHeader,
                [segRadiusHeader, self.segRadiusEdit],
                [segLengthHeader, self.segLengthEdit],
                [segTortHeader, self.segTortuosityEdit],
                [segVolumeHeader, self.segVolumeEdit],
                [segSAHeader, self.segSAEdit],
                [sourceHeader, self.sourceEdit],
                [targetHeader, self.targetEdit],
            ],
        )

        ## Add it all together
        line0 = QtO.new_line("V", 2)
        line1 = QtO.new_line("V", 2)
        QtO.add_widgets(
            boxLayout, [0, leftColumn, line0, self.middleColumn, line1, rightColumn, 0]
        )

    def update_graph_options(self):
        enable_csv_info = False
        if self.graphFormat.currentText() == "CSV":
            if self.fileSheet:
                self.fileSheet.init_csv()
            enable_csv_info = True
        else:
            if self.fileSheet:
                self.fileSheet.init_default()

        self.delimiterCombo.setEnabled(enable_csv_info)
        self.vertexRadiusEdit.setEnabled(enable_csv_info)
        self.sourceEdit.setEnabled(enable_csv_info)
        self.targetEdit.setEnabled(enable_csv_info)
        self.update_graph_type()
        return

    def update_graph_type(self):
        type = self.graphType.currentText()
        enabled = False
        if type == "Centerlines":
            enabled = True

        # Centerline enabled
        self.vertexRadiusEdit.setEnabled(enabled)

        # Centerline disabled
        self.segRadiusEdit.setDisabled(enabled)
        self.segLengthEdit.setDisabled(enabled)
        self.segTortuosityEdit.setDisabled(enabled)
        self.segVolumeEdit.setDisabled(enabled)
        self.segSAEdit.setDisabled(enabled)
        return

    def prepare_options(self):
        # Prepare attribute key
        a_key = IC.AttributeKey(
            self.xEdit.text(),
            self.yEdit.text(),
            self.zEdit.text(),
            self.vertexRadiusEdit.text(),
            self.segRadiusEdit.text(),
            self.segLengthEdit.text(),
            self.segVolumeEdit.text(),
            self.segSAEdit.text(),
            self.segTortuosityEdit.text(),
            self.sourceEdit.text(),
            self.targetEdit.text(),
        )

        delimiter = self.delimiterCombo.currentText()
        if len(delimiter) > 1:
            if delimiter[0] == "S":
                delimiter = " "
            elif delimiter[0] == "T":
                delimiter = "\t"
        graph_options = IC.GraphOptions(
            self.graphFormat.currentText(),
            self.graphType.currentText(),
            self.cliqueFiltering.isChecked(),
            self.centerlineSmoothing.isChecked(),
            a_key,
            delimiter,
        )
        return graph_options


class LoadingWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.results_folder = helpers.load_results_dir()
        self.column1_files = []
        self.column2_files = []
        self.annotation_data = None

        self.setMinimumHeight(400)
        topLayout = QtO.new_layout(self, no_spacing=True)

        ## Loading column
        self.loadingColumn = QtO.new_widget(150)
        loadingLayout = QtO.new_layout(self.loadingColumn, orient="V")

        self.loadButton = QtO.new_button("Load Files", None)
        clearFile = QtO.new_button("Remove File", self.remove_file)
        clearAll = QtO.new_button("Clear Files", self.clear_files)

        # Line
        line = QtO.new_line("H", 100)

        # Volume Options
        typeHeader = QLabel("<b>Dataset Type:")
        self.datasetType = QtO.new_combo(
            ["Volume", "Graph"], connect=self.file_type_options
        )

        # Annotation options
        annHeader = QLabel("<b>Annotation Type:")
        self.annotationType = QtO.new_combo(
            ["None", "ID", "RGB"], connect=self.annotation_options
        )
        self.annotationType.currentIndexChanged.connect(self.update_JSON)

        # Load annotation
        self.loadAnnotationFile = QtO.new_widget()
        aFileLayout = QtO.new_layout(self.loadAnnotationFile, "V", margins=(0, 0, 0, 0))

        loadJSON = QtO.new_button("Load JSON", self.load_annotation_file)
        loadJSON.setToolTip(
            "Load annotation file created using the Annotation Processing tab."
        )
        loaded = QLabel("<center>Loaded JSON:")
        self.loadedJSON = QtO.new_line_edit("None", "Center", locked=True)
        self.JSONdefault = self.loadedJSON.styleSheet()
        self.loadAnnotationFile.setVisible(False)
        QtO.add_widgets(aFileLayout, [loadJSON, loaded, self.loadedJSON], "Center")

        QtO.add_widgets(
            loadingLayout,
            [
                40,
                self.loadButton,
                clearFile,
                clearAll,
                line,
                typeHeader,
                self.datasetType,
                annHeader,
                self.annotationType,
                self.loadAnnotationFile,
                0,
            ],
            "Center",
        )

        ## Top right - file list information
        # region
        topRight = QtO.new_widget()
        topRightLayout = QtO.new_layout(topRight, "V", no_spacing=True)
        self.fileSheet = FileSheet()
        self.fileSheet.setMinimumWidth(400)

        # Result export location
        folderLine = QtO.new_widget()
        folderLayout = QtO.new_layout(folderLine, margins=(0, 0, 0, 0))
        folderHeader = QLabel("Result Folder:")
        self.resultPath = QtO.new_line_edit(self.results_folder, locked=True)
        self.changeFolder = QtO.new_button("Change...", self.set_results_folder)
        QtO.add_widgets(
            folderLayout, [folderHeader, self.resultPath, self.changeFolder]
        )

        QtO.add_widgets(topRightLayout, [self.fileSheet, folderLine])
        # endregion

        QtO.add_widgets(topLayout, [self.loadingColumn, topRight])

    ## File management
    def add_column1_files(self):
        files = self.column1_files
        for i, file in enumerate(files):
            if i + 1 > self.fileSheet.rowCount():
                self.fileSheet.insertRow(self.fileSheet.rowCount())
            filename = os.path.basename(file)
            self.fileSheet.setItem(i, 0, QTableWidgetItem(filename))

        self.update_queue()
        return

    def add_column2_files(self):
        files = self.column2_files
        for i, file in enumerate(files):
            if i + 1 > self.fileSheet.rowCount():
                self.fileSheet.insertRow(self.fileSheet.rowCount())
            filename = os.path.basename(file)
            self.fileSheet.setItem(i, 1, QTableWidgetItem(filename))

        self.update_queue()
        return

    def remove_file(self):
        columns = self.fileSheet.columnCount()
        if self.fileSheet.selectionModel().hasSelection():
            index = self.fileSheet.currentRow()
            self.fileSheet.removeRow(index)
            if index < len(self.column1_files):
                del self.column1_files[index]
            if columns == 3:
                if index < len(self.column2_files):
                    del self.column2_files[index]
        return

    def clear_files(self):
        self.fileSheet.setRowCount(0)
        self.column1_files = []
        self.column2_files = []
        return

    ## Status management
    # Status is sent as a len(2) list with [0] as index
    # and [1] as status
    def update_status(self, status):
        column = self.fileSheet.columnCount() - 1
        self.fileSheet.setItem(status[0], column, QTableWidgetItem(status[1]))
        self.fileSheet.selectRow(status[0])

        if column == 3 and len(status) == 3:
            self.fileSheet.setItem(status[0], column - 1, QTableWidgetItem(status[2]))
        return

    def update_row_selection(self, row):
        self.fileSheet.selectRow(row)
        return

    def update_queue(self):
        last_column = self.fileSheet.columnCount() - 1
        for i in range(self.fileSheet.rowCount()):
            self.fileSheet.setItem(i, last_column, QTableWidgetItem("Queued..."))

        if self.fileSheet.columnCount() == 4:
            if self.annotation_data:
                count = len(self.annotation_data.keys())
                status = f"0/{count}"
            else:
                status = "Load JSON!"
            last_column -= 1
            for i in range(self.fileSheet.rowCount()):
                self.fileSheet.setItem(i, last_column, QTableWidgetItem(status))

        return

    ## JSON file loading
    def file_type_options(self):
        visible = False
        if self.datasetType.currentText() == "Graph":
            visible = True
        else:
            self.fileSheet.init_default()

        if self.annotationType.currentIndex():
            self.loadAnnotationFile.setVisible(not visible)

        self.annotationType.setDisabled(visible)
        self.clear_files()
        return

    def annotation_options(self):
        visible = False
        if self.annotationType.currentIndex():
            visible = True
            self.fileSheet.init_annotation()
        else:
            self.fileSheet.init_default()
            self.column2_files = []
        self.loadAnnotationFile.setVisible(visible)
        self.add_column1_files()
        return

    def load_annotation_file(self):
        loaded_file = helpers.load_JSON(helpers.get_dir("Desktop"))

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
                    if self.annotationType.currentText() == "RGB" and RGB_check(
                        annotation_data["VesselVio Annotations"]
                    ):
                        if RGB_Warning().exec_() == QMessageBox.No:
                            return

                    self.loadedJSON.setStyleSheet(self.JSONdefault)
                    filename = os.path.basename(loaded_file)
                    self.loadedJSON.setText(filename)
                    self.annotation_data = annotation_data["VesselVio Annotations"]
                    self.update_queue()
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

    ## Results folder processing
    def set_results_folder(self):
        folder = helpers.set_results_dir()
        if folder:
            self.results_folder = folder
            self.resultPath.setText(folder)
        return


class FileSheet(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setShowGrid(False)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.verticalHeader().hide()
        self.horizontalHeader().setMinimumSectionSize(100)

        self.setMinimumWidth(400)

        self.init_default()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

    def init_default(self):
        header = ["File Name", "File Status"]
        self.set_format(2, [300, 200], header)
        return

    def init_annotation(self):
        header = [
            "File Name",
            "Annotation File Name",
            "Regions Processed",
            "File Status",
        ]
        self.set_format(4, [200, 200, 150, 200], header)
        return

    def init_csv(self):
        header = ["File Name - Vertices", "File Name - Edges", "File Status"]
        self.set_format(3, [200] * 3, header)
        return

    def set_format(self, column_count, widths, header):
        # Add columns, column info, and column size
        self.setColumnCount(0)
        self.setColumnCount(column_count)
        for i in range(column_count):
            self.setColumnWidth(i, widths[i])

        self.setHorizontalHeaderLabels(header)

        # Make sure status column is fixed size
        last = self.columnCount() - 1
        delegate = QtO.AlignCenterDelegate(self)
        self.setItemDelegateForColumn(last, delegate)

        self.horizontalHeader().setSectionResizeMode(last, QHeaderView.Fixed)
        if last == 3:
            last -= 1
            self.horizontalHeader().setSectionResizeMode(last, QHeaderView.Fixed)
            self.setItemDelegateForColumn(last, delegate)

        # Left align text for the file names
        delegate = QtO.AlignLeftDelegate(self)
        for i in range(last):
            self.setItemDelegateForColumn(i, delegate)
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        return


## File loading
class FileLoader(QDialog):
    def __init__(self, dataset_type, annotation, graph_format):
        super().__init__()
        self.column1_files = []
        self.column2_files = []
        self.graph_format = graph_format
        self.annotation = annotation

        # Sizing

        windowLayout = QtO.new_layout(orient="V")
        self.setLayout(windowLayout)
        self.setWindowTitle("Dataset Loading")

        # Create volume loading buttons
        # Create load volume buttons
        loadingLayout = QtO.new_form_layout()
        if dataset_type == "Volume":
            volumeLabel = QLabel("Load binarized volumes:")
            loadButton = QtO.new_button("Load...", self.load_volumes)
            QtO.add_form_rows(loadingLayout, [[volumeLabel, loadButton]])
            if annotation == "RGB":
                annLabel = QLabel("Load RGB annotation parent folder:")
            else:
                annLabel = QLabel("Load volume annotations:")
            annButton = QtO.new_button("Load...", self.load_annotations)
            QtO.add_form_rows(loadingLayout, [[annLabel, annButton]])
            QtO.button_defaulting(loadButton, False)
            QtO.button_defaulting(annButton, False)

        else:
            vHeader = QLabel("Load CSV vertices files:")
            vButton = QtO.new_button("Load...", self.load_csv_vertices)
            eHeader = QLabel("Load CSV edges files:")
            eButton = QtO.new_button("Load", self.load_csv_edges)
            QtO.add_form_rows(loadingLayout, [[vHeader, vButton], [eHeader, eButton]])
            QtO.button_defaulting(vButton, False)
            QtO.button_defaulting(eButton, False)

        cancel = QtO.new_button("Cancel", self.cancel_load)
        QtO.button_defaulting(cancel, False)
        QtO.add_widgets(windowLayout, [loadingLayout, cancel], "Center")

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def load_csv_vertices(self):
        files = self.init_dialog("csv (*.csv)", "Load CSV vertex files")
        if files:
            self.column1_files += files
            self.accept()
        return

    def load_csv_edges(self):
        files = self.init_dialog("csv (*.csv)", "Load CSV edge files")
        if files:
            self.column2_files += files
            self.accept()
        return

    def load_volumes(self):
        file_filter = "Images (*.nii *.png *.bmp *.tif *.tiff *.jpg *.jpeg)"
        files = self.init_dialog(file_filter, "Load volume files")
        if files:
            self.column1_files += files
            self.accept()
        return

    # Format either is a folder or .nii files
    def load_annotations(self):
        files = None
        if self.annotation == "ID":
            file_filter = "Images (*.nii)"
            files = self.init_dialog(file_filter, "Load .nii annotation volumes")
        else:
            folder = self.init_dir_dialog()
            if folder:
                files = [
                    os.path.join(folder, path)
                    for path in os.listdir(folder)
                    if os.path.isdir(os.path.join(folder, path))
                ]

        if files:
            self.column2_files += files
            self.accept()

        return

    def cancel_load(self):

        self.reject()

    def init_dialog(self, file_filter, message):
        files = QFileDialog.getOpenFileNames(
            self, message, helpers.get_dir("Desktop"), file_filter
        )
        return files[0]

    def init_dir_dialog(self):
        results_dir = QFileDialog.getExistingDirectory(
            self,
            "Select parent folder of RGB annotation folders",
            helpers.get_dir("Desktop"),
        )
        return results_dir


###############
### Testing ###
###############
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = mainWindow()
    sys.exit(app.exec_())
