"""
Dataset filepath processing functions.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from library.file_processing import path_processing

from PyQt5.QtWidgets import QFileDialog


def load_volume_files(message="Load volume files"):
    """Return selected image files

    Parameters:
    message : str, optional
        Message for the loading dialog. Default ``"Load volume files"``.

    Returns:
    list, None
        List of the selected files, or None if no files were selected.

    """
    file_filter = "Images (*.nii *.png *.bmp *.tif *.tiff *.jpg *.jpeg)"
    files = QFileDialog.getOpenFileNames(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]
    if files:
        files = [path_processing.std_path(file) for file in files]
    return files


def load_volume_file(message="Load volume file"):
    """Return a single selected image file.

    Parameters:
    message : str, optional
        Message for the loading dialog. Default ``"Load volume file"``.

    Returns:
    list, None
        List of the selected files, or None if no files were selected.

    """
    file_filter = "Images (*.nii *.png *.bmp *.tif *.tiff *.jpg *.jpeg)"
    file = QFileDialog.getOpenFileName(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]
    if file:
        file = path_processing.std_path(file)
    return file


def load_graph_file(graph_format: str, message=None):
    """Return the selected graph file of the specified format.

    Parameters:
    graph_format : str

    message : str, optional
        Message for the loading dialog. Default f"Load {graph_format} file".

    Returns:
    str, None
        List of the selected files, or None if no files were selected.

    """
    if not message:
        message = f"Load {graph_format} file"
    file_filter = f"{graph_format} (*.{graph_format})"
    files = QFileDialog.getOpenFileName(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )
    return files[0]


def load_graph_files(graph_format: str, message=None):
    """Return the selected graph files of the specified format.

    Parameters:
    graph_format : str

    message : str, optional
        Message for the loading dialog. Default f"Load {graph_format} files".

    Returns:
    list, None
        List of the selected files, or None if no files were selected.

    """
    if not message:
        message = f"Load {graph_format} files"
    file_filter = f"{graph_format} (*.{graph_format})"
    files = QFileDialog.getOpenFileNames(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]
    if files:
        files = [path_processing.std_path(file) for file in files]
    return files


def load_nii_annotation_files(message="Load .nii annotation files"):
    """Return all selected .nii files.

    Parameters:
    message : str, optional
        Message for the loading dialog.
        Default ``"Load .nii annotation files"``.

    Returns:
    list, None
        List of the selected files, or None if no files were selected.

    """
    file_filter = "nii (*.nii)"
    files = QFileDialog.getOpenFileNames(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]
    if files:
        files = [path_processing.std_path(file) for file in files]
    return files


def load_nii_annotation_file(message="Load .nii annotation file"):
    """Return a single selected .nii file.

    Parameters:
    message : str, optional
        Message for the loading dialog. Default ``"Load .nii annotation file"``.

    Returns:
    str

    """
    file_filter = "nii (*.nii)"
    file = QFileDialog.getOpenFileName(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]
    if file:
        file = path_processing.std_path(file[0])
    return file


def load_RGB_folder(message="Select RGB annotation folder"):
    """Return a selected folder from a QFileDialog.

    Parameters:
    message : str, optional
        Default: ``"Select RGB annotation folder"``.

    Returns:
    folder : str

    """
    folder = QFileDialog.getExistingDirectory(
        QFileDialog(),
        message,
        path_processing.get_desktop_path(),
    )
    if folder:
        folder = path_processing.std_path(folder)
    return folder


def load_JSON(message="Select VesselVio Annotation JSON File"):
    """Open a QFileDialog to load a JSON file.

    Parameters:
    message : str
        Default: ``"Select VesselVio Annotation JSON File"``.
    """
    file_filter = "json (*.json)"
    loaded_file = QFileDialog.getOpenFileName(
        QFileDialog(), message, path_processing.get_desktop_path(), file_filter
    )[0]

    if loaded_file:
        loaded_file = path_processing.std_path(loaded_file)
    return loaded_file
