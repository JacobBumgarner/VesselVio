"""Dialog warnings."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QMessageBox


class MessageBoxTemplate(QMessageBox):
    """A template for short warning messages.

    Parameters:
    message : str

    window_title : str

    window_size : list
        A list of two integers
    """

    def __init__(self, message: str, window_title: str, window_size: list = [200, 100]):
        """Build the warning."""
        super().__init__()
        self.setFixedSize(*window_size)
        self.setWindowTitle(window_title)
        self.setText(message)


class AnnotationJSONWarning(MessageBoxTemplate):
    """A message box that warns about an incompatible JSON file."""

    def __init__(self):
        """Build the warning."""
        window_title = "Annotation Data Error"
        message = """<center>
        The Loaded JSON file is incompatible!<br><br>
        Please load a JSON file that was created on the Annotation Processing Page.
        """
        super().__init__(message, window_title)
        self.exec_()


class PreviouslyAnalyzedWarning(MessageBoxTemplate):
    """A warning indicating that the loaded files have already been analyzed."""

    def __init__(self):
        message = """<center>
        The currently loaded files have already been analyzed.
        """
        window_title = "Analysis Error"
        super.__init__(message, window_title)
        self.exec_()


class ResultsPathWarning(MessageBoxTemplate):
    """A warning indicating that the user must select a results export path."""

    def __init__(self):
        """Build the warning."""
        window_title = "Results Path Warning"
        message = """<center>
        A folder must be selected for results export prior to running an
        analysis.
        """
        super().__init__(message, window_title)
        self.exec_()


class IncompleteFileLoadingWarning(MessageBoxTemplate):
    """A warning indicating that the files have been loaded incompletely."""

    def __init__(self):
        window_title = "Incomplete Loading Warning"
        message = """<center>
        All of the appropriate files must be loaded prior to analysis.<br><br>

        This may include the annotation JSON, annotation volumes, or CSV graph
        files.
        """
        super().__init__(message, window_title)
        self.exec_()


class DiskSpaceWarning(MessageBoxTemplate):
    """A warning inicating insufficient disk space for an annotation analysis.

    Parameters
    ----------
    needed_space : float
        The amount of needed disk space in GB.

    """

    def __init__(self, needed_space: float):
        window_title = "Disk Space Error"
        message = (
            "<center>During the analysis, one or more files were unable to be",
            "analyzed because of insufficient free disk memory.<br><br>",
            "<center>To analyze annotated volume datasets, VesselVio will need",
            f"at least <u>{needed_space:.1f} GB</u> of free space.",
        )

        super().__init__(message, window_title)
        self.exec_()
