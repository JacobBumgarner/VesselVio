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

    Parameters:
    start_function : function

    end_function : function

    """

    def __init__(self, start_function=None, end_function=None):
        layout = QtO.new_layout(self, orient="V", spacing=13)

        analyze_button = QtO.new_button("Analyze", start_function)
        cancel_button = QtO.new_button("Cancel", end_function)
        self.cancelButton.setDisabled(True)

        QtO.add_widgets(layout, [0, analyze_button, cancel_button, 0])
