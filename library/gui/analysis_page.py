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

from library import helpers, qt_threading as QtTh

from library.annotation.tree_processing import RGB_duplicates_check
from library.gui import qt_objects as QtO
from library.gui.annotation_page import RGB_Warning
from library.gui.file_loading_widgets.analysis_file_loaders import (
    AnnotationFileLoader,
    CSVGraphFileLoader,
)
from library.gui.options_widgets.analysis_options_widget import AnalysisOptions
from library.gui.options_widgets.graph_options_widget import GraphOptions

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QWidget,
)


class mainWindow(QMainWindow):
    """A main window for development and testing of the analysis page only."""

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
    """The page for batch analysis of volumes and graphs.

    Provides a GUI for users to load multiple datasets, including binary
    volumes, annotated volumes, and graphs. Analysis and result export
    options can be set, and batch analyses on the loaded datasets can be run.

    """

    def __init__(self):
        """Build the analysis page."""
        super().__init__()
        self.analyzed = False

        ### This page is organized into two vertical sections.
        pageLayout = QtO.new_layout(self, "V", spacing=5, margins=20)

        ## Top section - two widgets: file loading and file table
        topWidget = QtO.new_widget()
        topLayout = QtO.new_layout(topWidget, margins=(0, 0, 0, 0))

        # Top right - file table widget, results export widget
        topRightWidget = QtO.new_widget()
        topRightLayout = QtO.new_layout(topRightWidget, "V", no_spacing=True)
        self.fileTable = FileTableWidget()

        # Result path manager
        self.resultsPathManager = ResultsPathManagerWidget()

        QtO.add_widgets(topRightLayout, [self.fileTable, self.resultsPathManager])

        # Top left - file manager
        self.fileManager = FileManagerWidget(self.fileTable)
        self.fileManager.loadButton.clicked.connect(self.load_files)

        # Add widgets to the top layout
        QtO.add_widgets(topLayout, [self.fileManager, topRightWidget])

        ## Bottom section - three widgets: spacer, options, analyze/cancel
        # three column horizontal
        bottomWidget = QtO.new_widget()
        bottomWidget.setFixedHeight(250)
        bottomLayout = QtO.new_layout(bottomWidget, no_spacing=True)

        # Left column is a spacer to match the top loading widget.
        spacer = QtO.new_widget(150)

        # Middle column is a tab widget
        self.analysisOptions = AnalysisOptions()
        self.graphOptions = GraphOptions(self.fileTable)
        self.optionsTab = QTabWidget()
        self.optionsTab.addTab(self.analysisOptions, "Analysis Options")
        self.optionsTab.addTab(self.graphOptions, "Graph File Options")

        # Connect the loading filetype to the second options tab
        self.optionsTab.setTabEnabled(1, False)
        self.fileManager.datasetType.currentIndexChanged.connect(self.update_table_view)

        # Right column
        rightColumn = QtO.new_layout(orient="V", spacing=13)
        self.analyzeButton = QtO.new_button("Analyze", self.run_analysis)
        self.cancelButton = QtO.new_button("Cancel", self.cancel_analysis)
        self.cancelButton.setDisabled(True)
        QtO.add_widgets(rightColumn, [0, self.analyzeButton, self.cancelButton, 0])

        QtO.add_widgets(bottomLayout, [spacer, 0, self.optionsTab, rightColumn, 0])

        ## Add it all together
        QtO.add_widgets(pageLayout, [topWidget, bottomWidget])

    ## File loading
    def load_files(self):
        """Load files based on the selected filetypes.

        Dispatches loading for segmented files, annotation files,
        and graph files.
        """
        dataset_type = self.fileManager.datasetType.currentText()
        annotation_type = self.fileManager.annotationType.currentText()
        graph_format = self.graphOptions.graphFormat.currentText()

        column1_files, column2_files = None, None
        self.file_loader = None
        if dataset_type == "Volume":
            if annotation_type == "None":
                column1_files = helpers.load_volume_files()
            else:
                self.file_loader = AnnotationFileLoader(annotation_type)

        elif dataset_type == "Graph":
            if graph_format == "CSV":
                self.file_loader = CSVGraphFileLoader()
            else:
                column1_files = helpers.load_graph_files(graph_format)

        # If dual file loading is necessary, exec the file loader.
        if self.file_loader and self.file_loader.exec_():
            if self.file_loader.column1_files:
                column1_files = self.file_loader.column1_files
            if self.file_loader.column2_files:
                column2_files = self.file_loader.column2_files
            del self.file_loader

        if self.analyzed:
            self.fileTable.clear_files()
            self.analyzed = False
        if column1_files:
            self.fileTable.add_column1_files(column1_files)
        if column2_files:
            self.fileTable.add_column2_files(column2_files)

        return

    # Analysis Processing
    def run_analysis(self):
        """Initiate the analysis of the loaded files.

        Workflow:
        1. Check to ensure that the appropriate files have been loaded for the
        analysis.

        2. Connect the appropriate QThread to the appropriate buttons and
        selection signals.

        3. Start the QThread

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
        if self.fileManager.datasetType.currentText() == "Volume":
            self.initialize_volume_analysis()
        elif self.fileManager.datasetType.currentText() == "Graph":
            self.initialize_graph_analysis()

        self.a_thread.button_lock.connect(self.button_locking)
        self.a_thread.selection_signal.connect(self.fileTable.update_row_selection)
        self.a_thread.analysis_status.connect(
            self.fileTable.update_file_analysis_status
        )
        self.a_thread.start()
        self.analyzed = True
        return

    # Volume analysis
    def initialize_volume_analysis(self):
        """Initialize an analysis thread for volume-based analysis.

        Loads and prepares the relevant volume analysis options.
        """
        analysis_options = self.analysisOptions.prepare_options(
            self.resultsPathManager.results_folder
        )
        analysis_options.annotation_type = self.fileManager.annotationType.currentText()
        self.a_thread = QtTh.VolumeThread(
            analysis_options,
            self.fileManager.column1_files,
            self.fileManager.column2_files,
            self.fileManager.annotation_data,
            self.disk_space_warning,
        )
        return

    def initialize_graph_analysis(self):
        """Initialize an analysis thread for graph-based analysis.

        Loads and prepares the relevant graph analysis options.
        """
        analysis_options = self.analysisOptions.prepare_options(
            self.resultsPathManager.results_folder
        )
        graph_options = self.graphOptions.prepare_options()
        self.a_thread = QtTh.GraphThread(
            analysis_options,
            graph_options,
            self.fileManager.column1_files,
            self.fileManager.column2_files,
        )
        return

    def cancel_analysis(self):
        """Trigger the analysis thread to stop at the next breakpoint."""
        # Disable the cancel button after the request is sent.
        self.cancelButton.setDisabled(True)
        self.a_thread.stop()
        return

    def button_locking(self, lock_state):
        """Toggle button locking during the analysis.

        Also serves to trigger any relevant log.

        Parameters:
        lock_state : bool
            Enables/Disables the relevant buttons based on the lock state.
            Some buttons will be disabled, some will be enabled.
            The lock_state bool status is relevant for the 'setEnabled' or
            'setDisabled' call.
        """
        self.cancelButton.setEnabled(lock_state)
        self.fileManager.setDisabled(lock_state)
        self.resultsPathManager.changeFolder.setDisabled(lock_state)
        self.analyzeButton.setDisabled(lock_state)
        return

    def file_check(self):
        """Ensure that the appropriate files have been loaded for the analysis.

        Returns:
        bool
            True if loaded correctly, False if incorrectly or incompletely
            loaded
        """
        if not self.fileTable.column1_files:  # General file check
            return False

        if self.fileManager.datasetType.currentText() == "Volume":  # Specific check
            if self.fileManager.annotationType.currentText() != "None":
                if not self.column_file_check() or not self.fileManager.annotation_data:
                    return False
        if self.fileManager.datasetType.currentText() == "Graph":
            if self.graphOptions.graphFormat.currentText() == "CSV":
                if not self.column_file_check():
                    return False
        return True

    def column_file_check(self):
        """Ensures that two columns have equal file counts.

        Returns
        -------
        bool
            True if the number of files match, False if they are different
        """
        file_check = len(self.fileTable.column1_files) == len(
            self.fileTable.column2_files
        )
        return file_check

    # Warnings
    def analysis_warning(self):
        """Create an incomplete file loading error."""
        msgBox = QMessageBox()
        message = "Load all files to run analysis."
        msgBox.setText(message)
        msgBox.exec_()

    def disk_space_warning(self, needed_space: float):
        """Create a disk space warning error."""
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
        """Update the view of the file loading table.

        If an annotation-based analysis or a CSV graph-based analysis are
        selected, an additional column is added for the relevant files.
        """
        active = False
        if self.fileManager.datasetType.currentText() == "Graph":
            active = True
            if self.graphOptions.graphFormat.currentText() != "CSV":
                self.fileTable.apply_default_layout()
            else:
                self.fileTable.apply_csv_layout()
        elif self.fileManager.annotationType.currentText() != "None":
            self.fileTable.apply_annotation_layout()
        self.optionsTab.setTabEnabled(1, active)
        return


class ResultsPathManagerWidget(QWidget):
    """Widget used to manage the results export directory.

    Attributes:
    results_folder : string
        The user-selected path to export the results to.
    """

    def __init__(self):
        """Build the path processing widget."""
        super().__init__()
        self.results_folder = helpers.load_results_dir()

        layout = QtO.new_layout(self, margins=(0, 0, 0, 0))
        folderHeader = QLabel("Result Folder:")
        self.resultPath = QtO.new_line_edit(self.results_folder, locked=True)
        self.changeFolder = QtO.new_button("Change...", self.set_results_folder)
        QtO.add_widgets(layout, [folderHeader, self.resultPath, self.changeFolder])
        return

    def set_results_folder(self):
        """Update the results folder export directory."""
        folder = helpers.set_results_dir()
        if folder:
            self.results_folder = folder
            self.resultPath.setText(folder)
        return


class FileTableWidget(QTableWidget):
    """
    QTableWidget used to view the loaded datasets and their analysis status.

    Attributes:
    column1_files : list

    column2_files : list
    """

    def __init__(self):
        """Build the table widget."""
        super().__init__()
        self.column1_files = []
        self.column2_files = []

        self.setShowGrid(False)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.verticalHeader().hide()
        self.horizontalHeader().setMinimumSectionSize(100)

        self.setMinimumWidth(400)

        self.apply_default_layout()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

    # File management
    def add_column1_files(self, files: list):
        """Add files to the first column of the table.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """
        self.setRowCount(len(files))
        self.column1_files.extend(files)
        for i, file in enumerate(self.column1_files):
            filename = os.path.basename(file)
            self.setItem(i, 0, QTableWidgetItem(filename))

    def add_column2_files(self, files: list):
        """Add files to the second column of the table.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """

        for i, file in enumerate(self.column1_files):
            if i + 1 > self.rowCount():
                self.insertRow(self.rowCount())
            filename = os.path.basename(file)
            self.setItem(i, 0, QTableWidgetItem(filename))

    def clear_files(self):
        """Clear the files from the table."""
        self.setRowCount(0)
        self.column1_files = []
        self.column2_files = []

    def update_file_analysis_status(self, status):
        """Update the analysis status of a file.

        Parameters:
        status : list

        """
        column = self.columnCount() - 1
        self.selectRow(status[0])
        self.setItem(status[0], column, QTableWidgetItem(status[1]))

        if column == 3 and len(status) == 3:
            self.setItem(status[0], column - 1, QTableWidgetItem(status[2]))
        return

    # Layout management
    def apply_default_layout(self):
        """Apply the default single file layout.

        Implements a two column layout:
        Column 1 shows file names.
        Column 2 shows the analysis status of the file.
        """
        header = ["File Name", "File Status"]
        self.set_table_layout(2, [300, 200], header)
        return

    def apply_annotation_layout(self):
        """Update the table for loaded annotation files.

        Implements a four column layout:
        Column 1 shows the volume file names.
        Column 2 shows the annotation file names.
        Column 3 shows the number of annotation regions.
        Column 4 shows the analysis status of the file.
        """
        header = [
            "File Name",
            "Annotation File Name",
            "Regions Processed",
            "File Status",
        ]
        self.set_table_layout(4, [200, 200, 150, 200], header)
        return

    def apply_csv_layout(self):
        """Update the table for loaded CSV files.

        Implements a three column layout:
        Column 1 shows the vertex file names.
        Column 2 shows the edge file names.
        Column 3 shows the analysis status of the file.
        """
        header = ["File Name - Vertices", "File Name - Edges", "File Status"]
        self.set_table_layout(3, [200] * 3, header)
        return

    def set_fixed_column_format(self, column_index):
        """Apply the fixed layout to the specified column.

        This format incluces a centered alignment with a fixed column width.

        Parameters:
        column_index : int
        """
        delegate = QtO.AlignCenterDelegate(self)  # center alignment
        self.setItemDelegateForColumn(column_index, delegate)
        self.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Fixed)
        return

    def set_table_layout(self, column_count, widths, header):
        """Update the layout of the file table.

        Parameters:
        column_count : int
            Indicates how many many columns should be placed into the table.

        widths : list
            A list of integers indicating how wide each column should be in
            pixels.

        header : list
            A list of strings used for the headers of each column.

        """
        # Add columns and update column size
        self.setColumnCount(0)
        self.setColumnCount(column_count)
        for i in range(column_count):
            self.setColumnWidth(i, widths[i])

        # Add column headers, adjust the sizing of the final column.
        self.setHorizontalHeaderLabels(header)

        # Update format of the status column
        last_column_index = self.columnCount() - 1
        self.set_fixed_column_format(last_column_index)

        # If an annotation file is present, apply the
        # fixed formatting to the annotatino column..
        if last_column_index == 3:
            last_column_index -= 1
            self.set_fixed_column_format(last_column_index - 1)

        # Left align text for the file names
        delegate = QtO.AlignLeftDelegate(self)
        for i in range(last_column_index):
            self.setItemDelegateForColumn(i, delegate)
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        return

    # Selection management
    def update_row_selection(self, row):
        """ "Update the selected row of the table.

        Parameters:
        row : int
        """
        self.selectRow(row)
        return


class FileManagerWidget(QWidget):
    def __init__(self, fileTable: FileTableWidget):
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


###############
### Testing ###
###############
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = mainWindow()
    sys.exit(app.exec_())
