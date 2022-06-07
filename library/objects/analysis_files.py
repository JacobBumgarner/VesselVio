"""The file managers used in the GUI."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


class AnalysisFiles:
    """A"""

    def __init__(self):
        self.main_files = []
        self.associated_files = []
        self.annotation_JSON = None

    def add_main_files(self, files: list):
        """Add main file(s) to the file list.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """
        if not isinstance(files, list):
            raise TypeError("``files`` must be a list.")
        self.main_files.extend(files)

    def add_associated_files(self, files: list):
        """Add associated file(s) to the file list.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """
        self.associated_files.extend(files)

    def clear_analysis_files(self):
        """Clear the files from the table."""
        self.main_files = []
        self.associated_files = []

    def clear_annotation_JSON(self):
        """Clear the input annotation JSON file."""
        self.annotation_JSON = None

    def clear_all_files(self):
        """Reset the object and clear all files."""
        self.clear_analysis_files()
        self.clear_annotation_JSON()
