"""File loading widgets used for batch analysis file processing."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import os

from PyQt5.QtWidgets import QDialog, QLabel, QLayout

from library.file_processing import dataset_io
from library.gui import qt_objects as QtO


## File loading
class CSVGraphFileLoader(QDialog):
    """Widget used to load CSV-based graphs.

    Attributes
    ----------
    main_files : list
        The csv files containing the graph vertex information. The list of these files
        is called ``main_files`` to stay consistent with the other file loader classes.
    associated_files : list
        The csv files containing the graph edge information. The list of these files is
        called ``associated_files`` to stay consistent with the other files loader
        classes.
    """

    main_files = []
    associated_files = []

    def __init__(self):
        """Build the CSV file loader."""
        super().__init__()

        # Dialog contains a form layout with a cancel button
        windowLayout = QtO.new_layout(orient="V")
        self.setLayout(windowLayout)
        self.setWindowTitle("CSV File Loading")

        # Two button form layout
        loadingLayout = QtO.new_form_layout()

        # Vertex loading button
        vertexLoadLabel = QLabel("Load CSV vertices files:")
        vertexLoadButton = QtO.new_button("Load...", self.load_csv_vertices)

        # Edge loading button
        edgeLoadLabel = QLabel("Load CSV edge files:")
        edgeLoadButton = QtO.new_button("Load", self.load_csv_edges)

        # Add widgets to the form
        QtO.add_form_rows(
            loadingLayout,
            [[vertexLoadLabel, vertexLoadButton], [edgeLoadLabel, edgeLoadButton]],
        )

        # Cancel button
        cancel = QtO.new_button("Cancel", self.cancel_file_loading)

        # Button defaulting
        QtO.button_defaulting(vertexLoadButton, False)
        QtO.button_defaulting(edgeLoadButton, False)
        QtO.button_defaulting(cancel, False)

        QtO.add_widgets(windowLayout, [loadingLayout, cancel], "Center")

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    # Graph loading
    def load_csv_vertices(self):
        """Load CSV files containing information about the graph vertices."""
        files = dataset_io.load_graph_files(
            graph_format="csv", message="Load CSV vertex files"
        )
        if files:
            self.main_files = files
            self.accept()
        return

    def load_csv_edges(self):
        """Load CSV files containing information about the graph edges."""
        files = dataset_io.load_graph_files(
            graph_format="csv", message="Load CSV edge files"
        )
        if files:
            self.associated_files = files
            self.accept()
        return

    def cancel_file_loading(self):
        """Close the opened file loading widget."""
        self.reject()


class AnnotationFileLoader(QDialog):
    """Widget used to load annotation files.

    Parameters
    ----------
    annotation_type : str
        Must be either ``"ID"`` or ``"RGB"``. Indicates the type of annotation files
        that will be loaded for the analysis. The RGB type generates a
        QFileLoadingWidget that seeks directories (of RGB images), and the ID type
        generates a widget that seeks image file types.

    Attributes
    ----------
    main_files : list
        The main vasculature files to be analyzed.
    associated_files : list
        The vasculature annotation files. These files can either be folders of RGB
        series or image files with int- or float-based region annotations.
    """

    main_files = []
    associated_files = []

    def __init__(self, annotation_type: str):
        """Build the file loading widget."""
        super().__init__()
        if not annotation_type.lower() in ["rgb", "id"]:
            raise ValueError("``annotation_type`` must either be 'ID' or 'RGB'.")

        self.annotation_type = annotation_type

        # Dialog contains a form layout with a cancel button
        windowLayout = QtO.new_layout(orient="V")
        self.setLayout(windowLayout)
        self.setWindowTitle("Dataset Loading")

        # Two button form layout
        loadingLayout = QtO.new_form_layout()

        # Volume loading button
        volumeLoadingLabel = QLabel("Load binarized volumes:")
        volumeLoadButton = QtO.new_button("Load...", self.load_binarized_volumes)

        # Annotation loading button
        if self.annotation_type == "RGB":
            annotationLoadingLabel = QLabel("Load RGB annotation parent folder:")
        else:
            annotationLoadingLabel = QLabel("Load volume annotations:")
        annotationLoadButton = QtO.new_button("Load...", self.load_annotation_files)

        # Add widgets to the form
        QtO.add_form_rows(
            loadingLayout,
            [
                [volumeLoadingLabel, volumeLoadButton],
                [annotationLoadingLabel, annotationLoadButton],
            ],
        )

        # Cancel button
        cancel = QtO.new_button("Cancel", self.cancel_file_loading)

        # Button defaulting
        QtO.button_defaulting(volumeLoadButton, False)
        QtO.button_defaulting(annotationLoadButton, False)
        QtO.button_defaulting(cancel, False)

        QtO.add_widgets(windowLayout, [loadingLayout, cancel], "Center")

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def load_binarized_volumes(self):
        """Load volume files for the analysis."""
        files = dataset_io.load_volume_files()
        if files:
            self.main_files = files
            self.accept()
        return

    # Annotation file loading
    def load_annotation_files(self):
        """Load annotation files for the analysis."""
        files = None
        if self.annotation_type == "ID":
            file_filter = "Images (*.nii)"
            files = self.load_ID_annotations(
                file_filter, "Load .nii annotation volumes"
            )
        else:
            folder = self.load_RGB_annotation_parent_folder()
            if folder:
                files = [
                    os.path.join(folder, path)
                    for path in os.listdir(folder)
                    if os.path.isdir(os.path.join(folder, path))
                ]

        if files:
            self.associated_files = files
            self.accept()
        return

    def load_ID_annotations(self, file_filter, message):
        """Return the file paths of ID annotation .nii files."""
        files = dataset_io.load_nii_annotation_files()
        return files

    def load_RGB_annotation_parent_folder(self):
        """Return the parent folder of RGB annotation sub-folders."""
        message = "Select parent folder of the RGB annotation folders"
        RGB_parent_dir = dataset_io.load_RGB_folder(message)
        return RGB_parent_dir

    def cancel_file_loading(self):
        """Close the opened file loading widget."""
        self.reject()
