"""The analysis page for the application."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QTabWidget, QWidget

from library import qt_threading as QtTh
from library.gui import qt_objects as QtO
from library.gui.analysis import (
    AnalysisController,
    AnalysisFileController,
    AnalysisFileTable,
    ResultsPathController,
)
from library.gui.options_widgets import AnalysisOptionsWidget, GraphOptionsWidget
from library.gui.warnings import (
    IncompleteFileLoadingWarning,
    PreviouslyAnalyzedWarning,
    ResultsPathWarning,
)
from library.objects import AnalysisFileManager


class AnalysisPage(QWidget):
    """The page for batch analysis of volumes and graphs.

    Provides a GUI for users to load vasculature datasets for batch analyses.
    These datasets can including binary volumes, annotated volumes, and pre-constructed
    vascular graph networks. On this page, analysis and result export options can be
    set, and batch analyses on the loaded datasets can be run.
    """

    def __init__(self):
        """Build the analysis page."""
        super().__init__()

        # Initialize all of the objects up front. Organization below.
        self.file_mananger = AnalysisFileManager()
        self.optionsBox = QTabWidget()
        self.analysisOptions = AnalysisOptionsWidget()
        self.fileTable = AnalysisFileTable(self.file_mananger)
        self.graphOptions = GraphOptionsWidget(self.fileTable)
        self.resultsPathController = ResultsPathController()
        self.fileController = AnalysisFileController(
            self.file_mananger, self.fileTable, self.graphOptions, self.optionsBox
        )
        self.analysisController = AnalysisController(
            self.run_analysis, self.cancel_analysis
        )

        ### This page is organized into two vertical sections.
        pageLayout = QtO.new_layout(self, "V", spacing=5, margins=20)

        ## Top section - two widgets: fileController and top right widget
        topWidget = QtO.new_widget()
        topLayout = QtO.new_layout(topWidget, margins=(0, 0, 0, 0))

        # Top right - two widgets: file table widget, results export widget
        topRightWidget = QtO.new_widget()
        topRightLayout = QtO.new_layout(topRightWidget, "V", no_spacing=True)

        QtO.add_widgets(topRightLayout, [self.fileTable, self.resultsPathController])

        # Add widgets to the top layout
        QtO.add_widgets(topLayout, [self.fileController, topRightWidget])

        ## Bottom section - three widgets: spacer, options, analyze/cancel
        # three column horizontal
        bottomWidget = QtO.new_widget()
        bottomWidget.setFixedHeight(250)
        bottomLayout = QtO.new_layout(bottomWidget, no_spacing=True)

        # Left column is a spacer to match the top loading widget.
        spacer = QtO.new_widget(150)

        # Middle column is a tab widget
        self.optionsBox.addTab(self.analysisOptions, "Analysis Options")
        self.optionsBox.addTab(self.graphOptions, "Graph File Options")
        self.optionsBox.setTabEnabled(1, False)

        # Bottom Layout
        QtO.add_widgets(
            bottomLayout, [spacer, 0, self.optionsBox, self.analysisController, 0]
        )

        ## Add it all together
        QtO.add_widgets(pageLayout, [topWidget, bottomWidget])

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
        # Make sure everything is prepped correctly
        if not self.pre_analysis_check():
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
        self.file_mananger.analyzed = True
        return

    def pre_analysis_check(self) -> bool:
        """Check that the necessary steps have been completed for an analysis.

        - Checks to ensure that the loaded data have not already been analyzed.

        - Checks to see if annotation volumes have been appropriately loaded for
        annotation analyses.

        - Checks to see if the appropriate graph files have been loaded for CSV graph
        analyses.

        - Checks to see that a results path export option has been appropriately
        selected.

        Returns
        ------
        bool
            True if the analysis has been prepared correctly, False otherwise.
        """
        # If an analysis has already been run, make sure new files are loaded.
        if self.fileController.analyzed:
            PreviouslyAnalyzedWarning()
            return False

        # Make sure the appropriate files are loaded
        any_loaded = self.fileTable.rowCount() > 0
        dataset_type = self.fileController.datasetType.currentText()
        annotation_check = (
            dataset_type == "Volume"
            and self.fileController.annotationType.currentText() != "None"
        )
        graph_check = (
            dataset_type == "Graph"
            and self.graphOptions.graphFormat.currentText() == "CSV"
        )

        if not any_loaded or annotation_check or graph_check:
            IncompleteFileLoadingWarning()
            return False

        # Check that a results export path has been selected
        if self.resultsPathController.results_dir == "None":
            self.resultsPathController.highlight_empty_results_path_error()
            ResultsPathWarning()
            return False

        return True

    # Volume analysis
    def initialize_volume_analysis(self):
        """Initialize an analysis thread for volume-based analysis.

        Loads and prepares the relevant volume analysis options.
        """
        analysis_options = self.analysisOptions.prepare_options(
            self.resultsPathController.results_folder
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
            self.resultsPathController.results_folder
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

        True values lock:
            - Analyze button
            - File manager buttons (e.g., Clear All)
            - Results path controller
        True values enable:
            - Cancel button

        Parameters
        ----------
        lock_state : bool
            Enables or disables relevant buttons based on the lock state. See above
            for the specific buttons that are toggled.
        """
        self.cancelButton.setEnabled(lock_state)
        self.fileManager.setDisabled(lock_state)
        self.resultsPathController.changeFolder.setDisabled(lock_state)
        self.analyzeButton.setDisabled(lock_state)
        return
