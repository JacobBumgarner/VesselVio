"""The file managers used in the GUI."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from typing import Union

from library.annotation import tree_processing


class AnalysisFileManager:
    """The class that stores and manages the input files used for analyses.

    Attributes
    ----------
    main_files : list
        The primary files for an analysis. These will be image files with segmented
        vasculature, pre-constructe graph vascular networks, or CSV-based graph files
        with information about the graph vertices. Default is empty list.
    associated_files : list
        The associated files for a vasculature analysis. These files will either be
        images with vasculature annotation information or CSV-based graph files with
        information about the graph edges. Default is empty list.
    annotation_data : dict
        The annotation data that will carry information about which annotation regions
        will be analyzed. Default is None.
    analyzed : bool
        Indicates whether the loaded files have been analyzed. Default is False.
    """

    def __init__(self):
        """Build the model."""
        self.main_files = []
        self.associated_files = []
        self.annotation_data = None
        self.analyzed = False

    # File addition
    def add_main_files(self, files: list):
        """Add main file(s) to the file list.

        Updates the self.main_files attribute.

        Parameters
        ----------
        files : list
            A list of file path strings.
        """
        self.main_files.extend(files)
        return

    def add_associated_files(self, files: list):
        """Add associated file(s) to the file list.

        Updates the self.associated_files attribute.

        Parameters
        ----------
        files : list
            A list of file path strings.
        """
        self.associated_files.extend(files)
        return

    def add_annotation_JSON(self, annotation_file: str) -> bool:
        """Add an annotation file to the dataset.

        Parameters
        ----------
        annotation_file : str
            The filepath to the JSON-based annotation file.

        Returns
        -------
        bool
            True if the file was compatible and loaded successfully. False otherwise.
        """
        if not tree_processing.check_annotation_data_origin(annotation_file):
            return False

        self.annotation_data = tree_processing.load_vesselvio_annotation_file(
            annotation_file
        )
        return True

    # File removal
    def remove_main_files(self, selected: Union[int, list]):
        """Remove the indicated file(s) from the main files list.

        Parameters
        ----------
        indices : int, list
            The single selection or reverse-sorted list of row indices that will be
            removed from the main files list.
        """
        if not self.main_files:
            return

        if isinstance(selected, int):
            self.main_files.pop(selected)
        elif isinstance(selected, list):
            for row in selected:
                self.main_files.pop(row)
        return

    def remove_associated_files(self, selected: Union[int, list]):
        """Remove the indicated file(s) from the associated files list.

        Parameters
        ----------
        indices : int, list
            The single selection or reverse-sorted list of row indices that will be
            removed from the associated files list.
        """
        if not self.associated_files:
            return

        if isinstance(selected, int):
            self.associated_files.pop(selected)
        elif isinstance(selected, list):
            for row in selected:
                self.associated_files.pop(row)
        return

    def clear_selected_files(self, selected: Union[int, list]):
        """Remove the indicated files from the file lists.

        Parameters
        ----------
        indices : int, list
            The single selection or top and bottom indices of the selection
            of files to be removed from the list.
        """
        self.remove_main_files(selected)
        self.remove_associated_files(selected)
        return

    # Resetting
    def clear_analysis_files(self):
        """Clear the files from the table."""
        self.main_files = []
        self.associated_files = []
        return

    def clear_annotation_data(self):
        """Clear the input annotation JSON file."""
        self.annotation_data = None
        return

    def clear_all_files(self):
        """Reset the object and clear all files."""
        self.clear_analysis_files()
        self.clear_annotation_data()
        return
