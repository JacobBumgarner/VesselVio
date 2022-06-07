"""
The file manager for the FileTable on the analysis page.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os

from PyQt5.QtWidgets import QLabel, QMessageBox, QTableWidgetItem, QWidget

from ... import helpers
from ...annotation.tree_processing import RGB_duplicates_check

from .. import qt_objects as QtO
from ..annotation_page import RGB_Warning


class FileManager(QWidget):
    def __init__(self, fileTable):
        super().__init__()
        self.column1_files = []
        self.column2_files = []
        self.annotation_data = None
        self.fileTable = fileTable

        self.setMinimumHeight(400)
        self.setFixedWidth(150)

        ## Loading column
        layout = QtO.new_layout(self, orient="V", margins=(0, 0, 0, 0))

        self.loadButton = QtO.new_button("Load Files", None)
        clearFile = QtO.new_button("Remove File", self.remove_file)
        clearAll = QtO.new_button("Clear Files", self.fileTable.clear_files)

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
            layout,
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

    ## File management
    def add_column1_files(self):
        files = self.column1_files
        for i, file in enumerate(files):
            if i + 1 > self.fileTable.rowCount():
                self.fileTable.insertRow(self.fileTable.rowCount())
            filename = os.path.basename(file)
            self.fileTable.setItem(i, 0, QTableWidgetItem(filename))

        self.update_queue()
        return

    def add_column2_files(self):
        files = self.column2_files
        for i, file in enumerate(files):
            if i + 1 > self.fileTable.rowCount():
                self.fileTable.insertRow(self.fileTable.rowCount())
            filename = os.path.basename(file)
            self.fileTable.setItem(i, 1, QTableWidgetItem(filename))

        self.update_queue()
        return

    def remove_file(self):
        columns = self.fileTable.columnCount()
        if self.fileTable.selectionModel().hasSelection():
            index = self.fileTable.currentRow()
            self.fileTable.removeRow(index)
            if index < len(self.column1_files):
                del self.column1_files[index]
            if columns == 3:
                if index < len(self.column2_files):
                    del self.column2_files[index]
        return

    ## Status management
    # Status is sent as a len(2) list with [0] as index
    # and [1] as status

    def update_queue(self):
        last_column = self.fileTable.columnCount() - 1
        for i in range(self.fileTable.rowCount()):
            self.fileTable.setItem(i, last_column, QTableWidgetItem("Queued..."))

        if self.fileTable.columnCount() == 4:
            if self.annotation_data:
                count = len(self.annotation_data.keys())
                status = f"0/{count}"
            else:
                status = "Load JSON!"
            last_column -= 1
            for i in range(self.fileTable.rowCount()):
                self.fileTable.setItem(i, last_column, QTableWidgetItem(status))

        return

    ## JSON file loading
    def file_type_options(self):
        visible = False
        if self.datasetType.currentText() == "Graph":
            visible = True
        else:
            self.fileTable.apply_default_layout()

        if self.annotationType.currentIndex():
            self.loadAnnotationFile.setVisible(not visible)

        self.annotationType.setDisabled(visible)
        self.clear_files()
        return

    def annotation_options(self):
        if self.annotationType.currentIndex():
            self.fileTable.apply_annotation_layout()
        else:
            self.fileTable.apply_default_layout()
            self.column2_files = []
        self.loadAnnotationFile.setVisible(self.annotationType.currentIndex() > 0)
        self.add_column1_files()
        return

    def load_annotation_file(self):
        loaded_file = helpers.load_JSON(helpers.get_dir("Desktop"))

        if not loaded_file:
            return

        with open(loaded_file) as f:
            annotation_data = json.load(f)
            if (
                len(annotation_data) != 1
                or "VesselVio Annotations" not in annotation_data.keys()
            ):
                self.JSON_error("Incorrect filetype!")
            else:
                # If loading an RGB filetype, make sure there's no duplicate colors.
                if self.annotationType.currentText() == "RGB" and RGB_duplicates_check(
                    annotation_data["VesselVio Annotations"]
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
