"""
The analysis page for the application.
"""


"""
The PyQt5 code used to build the analysis page for the program.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QMessageBox, QTabWidget, QWidget

from library import helpers, qt_threading as QtTh
from library.gui import AnalysisOptions, GraphOptions, qt_objects as QtO
from library.gui.analysis import AnalysisFileTable, FileManager, ResultsPathManager

from library.gui.file_loading_widgets.analysis_file_loaders import (
    AnnotationFileLoader,
    CSVGraphFileLoader,
)


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
        self.fileTable = AnalysisFileTable()

        # Result path manager
        self.resultsPathManager = ResultsPathManager()

        QtO.add_widgets(topRightLayout, [self.fileTable, self.resultsPathManager])

        # Top left - file manager
        self.fileManager = FileManager(self.fileTable)
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
