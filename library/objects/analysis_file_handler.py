"""The file managers used in the GUI."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from typing import Union

from library.annotation import tree_processing


class AnalysisFileHandler:
    """A"""

    def __init__(self):
        self.main_files = []
        self.associated_files = []
        self.annotation_data = None

    def add_main_files(self, files: list):
        """Add main file(s) to the file list.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """
        self.main_files.extend(files)

    def add_associated_files(self, files: list):
        """Add associated file(s) to the file list.

        Parameters:
        files : list
            A list of str file paths. Updates the self.column1_files attribute.
        """
        self.associated_files.extend(files)

    def add_annotation_JSON(self, annotation_file: str) -> bool:
        """Add an annotation file to the dataset.

        Parameters:
        annotation_file : str
            The filepath to the JSON-based annotation file.

        Returns:
        bool : added
        """
        if not tree_processing.check_annotation_data_origin(annotation_file):
            return False

        self.annotation_data = tree_processing.load_vesselvio_annotation_file(
            annotation_file
        )
        return True

    def remove_main_files(self, indices: Union[int, list]):
        """Remove the indicated files from the main files list.

        Parameters:
        indices : int, list
            The single selection or top and bottom indices of the selection
            of files to be removed from the list. The top index will be removed.
        """
        if isinstance(indices, int):
            self.main_files.pop(indices)
        elif isinstance(indices, list) and len(indices) == 2:
            for index in range(indices[0], indices[1] + 1):
                self.main_files.pop(indices[0])
        return

    def remove_associated_files(self, indices: Union[int, list]):
        """Remove the indicated files from the associated files list.

        Parameters:
        indices : int, list
            The single selection or top and bottom indices of the selection
            of files to be removed from the list.
        """
        if isinstance(indices, int):
            self.associated_files.pop(indices)
        elif isinstance(indices, list) and len(indices) == 2:
            for index in range(indices[0], indices[1] + 1):
                self.associated_files.pop(indices[0])
        return

    def paired_files_check(self):
        """Return a bool indicating that the length of file lists is equal.

        Returns:
        bool : equal_lengths
        """
        return len(self.main_files) == len(self.associated_files)

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
