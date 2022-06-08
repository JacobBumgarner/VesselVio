"""Dialog warnings."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QMessageBox


class AnnotationJSONWarning(QMessageBox):
    """A message box that warns about an incompatible JSON file."""

    def __init__(self):
        super().__init__()
        """Build the warning."""
        self.setFixedSize(200, 100)
        self.setWindowTitle("Annotation Data Error")
        message = """<center>
        The Loaded JSON file is incompatible!<br><br>
        Please load a JSON file that was created on the Annotation Processing Page.
        """
        self.setText(message)
        self.exec_()
