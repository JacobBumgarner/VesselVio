"""
The file controller for the analysis page.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"

import os

from PyQt5.QtWidgets import QGroupBox, QLabel, QWidget

from library.file_processing import dataset_io
from library.gui import (
    AnalysisFileTable,
    AnnotationFileLoader,
    AnnotationJSONWarning,
    CSVGraphFileLoader,
    GraphOptions,
    qt_objects as QtO,
)
from library.objects import AnalysisFileManager


class AnalysisFileController(QWidget):
    def __init__(
        self,
        file_manager: AnalysisFileManager,
        fileTable: AnalysisFileTable,
        graphOptions: GraphOptions,
        optionsBox: QGroupBox,
    ):
        super().__init__()
        self.file_manager = file_manager
        self.fileTable = fileTable
        self.graphOptions = graphOptions  # simply to check the file_format
        self.optionsBox = optionsBox  # used to toggle graph options lock
        self.analyzed = False  # analysis status

        self.setMinimumHeight(400)
        self.setFixedWidth(150)

        ## Loading column
        layout = QtO.new_layout(self, orient="V", margins=(0, 0, 0, 0))

        loadButton = QtO.new_button("Load Files", self.file_loading_dispatch)
        clearFileButton = QtO.new_button("Remove File", self.clear_selected_files)
        clearAllFilesButton = QtO.new_button("Clear Files", self.clear_all_files)

        # Volume Options
        datasetTypeHeader = QLabel("<b>Dataset Type:")
        self.datasetType = QtO.new_combo(
            ["Volume", "Graph"], connect=self.file_type_options
        )

        # Annotation options
        annotationTypeHeader = QLabel("<b>Annotation Type:")
        self.annotationType = QtO.new_combo(
            ["None", "ID", "RGB"], connect=self.annotation_options
        )
        self.annotationType.currentIndexChanged.connect(self.update_JSON)

        # Load annotation
        self.annotationLoadingWidget = QtO.new_widget()
        aFileLayout = QtO.new_layout(self.loadAnnotationFile, "V", margins=(0, 0, 0, 0))

        loadJSON = QtO.new_button("Load JSON", self.load_vesselvio_annotation_file)
        loadJSON.setToolTip(
            "Load annotation file created using the Annotation Processing tab."
        )
        loaded = QLabel("<center>Loaded JSON:")
        self.loadedJSON = QtO.new_line_edit("None", "Center", locked=True)
        self.loadAnnotationFile.setVisible(False)
        QtO.add_widgets(aFileLayout, [loadJSON, loaded, self.loadedJSON], "Center")

        QtO.add_widgets(
            layout,
            [
                40,
                loadButton,
                clearFileButton,
                clearAllFilesButton,
                QtO.new_line("H", 100),  # visual dividing line
                datasetTypeHeader,
                self.datasetType,
                annotationTypeHeader,
                self.annotationType,
                self.annotationLoadingWidget,
                0,
            ],
            "Center",
        )

    def file_loading_dispatch(self):
        """Load the main files for the analysis.

        Depending on the the dataset type and annotation type, opens a
        QFileDialog or builds a FileLoadingDialog. If files are loaded, the
        controller then updates AnalysisFileManager model and updates
        the AnalysisFileTable.
        """
        # collect shorthand copies of the relevant settings
        dataset_type = self.datasetType.currentText()
        annotation_type = self.annotationType.currentText()
        graph_format = self.graphOptions.graphFormat.currentText()

        # if an analysis has been run, clear the analysis files
        if self.analyzed:
            self.clear_all_files()

        # check to see if a simple file loader can be used
        if (dataset_type == "Volume" and annotation_type == "None") or (
            dataset_type == "Graph" and graph_format != "CSV"
        ):
            self.load_main_files(dataset_type, graph_format)
            return

        # if not, create a file loader
        if annotation_type != "None":
            fileLoader = AnnotationFileLoader()
        elif graph_format == "CSV":
            fileLoader = CSVGraphFileLoader()

        if fileLoader.exec_():
            if fileLoader.main_files:
                self.update_main_files(fileLoader.main_files)
            elif fileLoader.associated_files:
                self.update_associated_files(fileLoader.associated_files)

    def load_main_files(self, dataset_type: str, graph_format: str):
        """Call the relevant function to load the specified main filetypes."""
        if dataset_type == "Volume":
            main_files = dataset_io.load_volume_files()
        elif dataset_type == "Graph":
            main_files = dataset_io.load_graph_files(graph_format)

        if main_files:
            self.update_main_files(main_files)

    def update_main_files(self, main_files: list):
        """Update the model and view with the loaded main files.

        Parameters:
        main_files : list
        """
        self.file_manager.add_main_files(main_files)
        self.fileTable.update_main_file_list()

    def update_associated_files(self, associated_files: list):
        """Update the model and view with the loaded associated files.

        Parameters:
        associated_files : list
        """
        self.file_manager.add_associated_files(associated_files)
        self.fileTable.update_associated_file_list()

    def load_vesselvio_annotation_file(self):
        """Load a VesselVio annotation file."""
        file = dataset_io.load_JSON()
        if not file:
            return

        # add the file to the manager
        if not self.file_manager.add_annotation_JSON(file):
            AnnotationJSONWarning()
            return

        # update the table view
        self.fileTable.update_annotation_column_status()

        # Update the JSON file name
        self.update_loaded_JSON_text(file)

    # File management
    def clear_selected_files(self):
        """Clear the selected files from the model and view."""
        selected_rows = self.fileTable.get_selected_row_indices()
        if not len(selected_rows):
            return
        self.fileTable.clear_selected_files(selected_rows)
        self.file_manager.clear_selected_files(selected_rows)

    def clear_all_files(self):
        """Clear files from the model and view."""
        self.file_manager.clear_all_files()
        self.fileTable.clear_table()

    # Analysis type controllers
    def update_dataset_type_view(self):
        """Update the visibility of widgets based on the dataset type."""
        self.clear_all_files()
        dataset_type = self.datasetType.currentText()

        # Update the annotation header. Default ``None``
        self.annotationType.setCurrentIndex(0)
        self.update_annotation_type_view()  # potential repeat, oh well.

        # Toggle the visibility of the graph loading widgets
        self.optionsBox.setTabEnabled(1, dataset_type == "Graph")

        # Toggle the layout of the table
        if dataset_type == "Volume":
            self.fileTable.apply_default_layout()
        elif dataset_type == "Graph":
            if self.graphOptions.graphFormat == "CSV":
                self.fileTable.apply_csv_layout()
            else:
                self.fileTable.apply_default_layout()

    def update_annotation_type_view(self):
        """Update the view of the annotation loading widget."""
        # Toggle the lock state of the annotation widget.
        self.annotationType.setEnabled(self.datasetType.currentText() == "Volume")

        # Toggle the visibility of the loading widget
        visible = self.annotationType.currentIndex() > 0
        self.annotationLoadingWidget.setVisible(visible)

        # Update the file table layout as needed
        if visible:
            self.fileTable.apply_annotation_layout()
        else:
            self.loadedJSON.setText("None")
            self.file_manager.clear_annotation_data()

    def update_loaded_JSON_text(self, filename="None"):
        """Update the loadedJSON QLineEdit text.

        Parameters:
        filename : str
        """
        self.loadedJSON.setText(os.path.basename(filename))
