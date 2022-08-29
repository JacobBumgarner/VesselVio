"""
The analysis controller for the analysis page.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"

from PyQt5.QtWidgets import QWidget

from library.gui import qt_objects as QtO


class AnalysisController(QWidget):
    """The analysis controller widget.

    Parameters
    ----------
    start_function : function
        A function that will be connected to the click of the controllers "Analyze"
        button.
    end_function : function
        A function that will be connected to the click of the controllers "Cancel"
        button.
    """

    def __init__(self, start_function=None, end_function=None):
        super().__init__()
        layout = QtO.new_layout(self, orient="V", spacing=13)

        self.analyzeButton = QtO.new_button("Analyze", start_function)
        self.cancelButton = QtO.new_button("Cancel", end_function)
        self.cancelButton.setDisabled(True)

        QtO.add_widgets(layout, [0, self.analyzeButton, self.cancelButton, 0])
