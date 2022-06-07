"""
The results export path manager.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QLabel, QWidget

from library import helpers
from library.gui import qt_objects as QtO


class ResultsPathManager(QWidget):
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
