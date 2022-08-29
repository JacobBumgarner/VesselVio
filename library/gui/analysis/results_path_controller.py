"""The results export path manager."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QLabel, QWidget

from library.file_processing import path_processing
from library.gui import qt_objects as QtO


class ResultsPathController(QWidget):
    """Widget that manages the results directory.

    By default, the results export directory is empty, and the user has
    to select one. Once a directory has been selected, it will then be stored
    in the preferences.json and used again in the future. If it no longer
    exists, the ``None` default will be selected.
    """

    def __init__(self):
        """Build the path processing widget."""
        super().__init__()

        self._file_dialog = None
        self.results_dir = path_processing.load_results_dir()
        if not self.results_dir:
            self.results_dir = "None"

        layout = QtO.new_layout(self, margins=(0, 0, 0, 0))
        folderHeader = QLabel("Result Folder:")
        self.resultsPath = QtO.new_line_edit(self.results_dir, locked=True)
        self.changeFolder = QtO.new_button("Change...", self.set_results_dir)
        QtO.add_widgets(layout, [folderHeader, self.resultsPath, self.changeFolder])

        # Results path stylesheets
        self.defaultPathStyle = self.resultsPath.styleSheet()
        self.errorPathStyle = "border: 1px solid red;"

        return

    def set_results_dir(self):
        """Update the results folder export directory."""
        results_dir = path_processing.set_results_dir(return_path=True)
        if results_dir:
            self.results_dir = results_dir
            self.resultsPath.setText(results_dir)
            self.clear_results_path_error()
        return

    def clear_results_path_error(self):
        """Clear the formatting of the results path."""
        self.resultsPath.setStyleSheet(self.defaultPathStyle)

    def highlight_empty_results_path_error(self):
        """Highlight the results path to show unselected export."""
        self.resultsPath.setStyleSheet(self.errorPathStyle)
