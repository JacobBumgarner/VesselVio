"""The QTableWidget used to visualize the loaded files."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"

from typing import Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from library.file_processing import path_processing
from library.gui import qt_objects as QtO
from library.objects import AnalysisFileManager, StatusUpdate


class AnalysisFileTable(QTableWidget):
    """
    QTableWidget used to view the loaded datasets and their analysis status.

    Parameters
    ----------
    file_manager : objects.AnalysisFileManager
        The manager of all of the files for an analysis.
    """

    def __init__(self, file_manager: AnalysisFileManager):
        """Build the table widget."""
        super().__init__()
        self.file_manager = file_manager
        self.layout_type = "Default"

        self.setMinimumWidth(400)
        self.setShowGrid(False)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        # self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionMode(QTableWidget.MultiSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.horizontalHeader().setMinimumSectionSize(100)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setStretchLastSection(True)

        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

        self.apply_default_layout(startup=True)

    # File management
    def clear_selected_files(self, selected_rows: Union[int, list] = None):
        """Clear the selected files from the table.

        Parameters
        ----------
        selected_rows : int, list
            A reverse sorted list of row indices, or a single int that indicates
            which row should be removed. The list should be reverse sorted, as the
            row removal has to happen from the back. Default is None.
        """
        if not selected_rows:
            selected_rows = self.get_selected_row_indices()
        for row in selected_rows:
            self.removeRow(row)

    def clear_table(self):
        """Clear the current files from the table."""
        self.setRowCount(0)

    # Layout management
    def apply_default_layout(self, startup: bool = False):
        """Apply the default single file layout.

        Implements a two column layout:
        Column 1 shows file names.
        Column 2 shows the analysis status of the file.

        Parameters
        ----------
        startup : bool
            Adjust the column sizes to the default width, emperically determined.
            This necessary because the widget is resized after creation when being
            built on startup, thereby destroying the default sizing. Default is False.
        """
        self.layout_type = "Default"

        header = ["File Name", "File Status"]
        file_width = self.width() - self.width() // 4
        status_width = self.width() - file_width
        widths = [file_width, status_width]

        if startup:
            widths = [675, 225]

        self.set_table_layout(header, widths)
        return

    def apply_csv_layout(self):
        """Update the table for loaded CSV files.

        Implements a three column layout:
        Column 1 shows the vertex file names.
        Column 2 shows the edge file names.
        Column 3 shows the analysis status of the file.
        """
        self.layout_type = "CSV"

        header = ["File Name - Vertices", "File Name - Edges", "File Status"]
        file_width = int(self.width() - self.width() // 4) / 2
        status_width = self.width() - file_width * 2
        widths = [file_width, file_width, status_width]

        self.set_table_layout(header, widths)
        return

    def apply_annotation_layout(self):
        """Update the table for loaded annotation files.

        Implements a four column layout:
        Column 1 shows the volume file names.
        Column 2 shows the annotation file names.
        Column 3 shows the number of annotation regions.
        Column 4 shows the analysis status of the file.
        """
        self.layout_type = "Annotation"

        header = [
            "File Name",
            "Annotation File Name",
            "Regions Processed",
            "File Status",
        ]
        widths = [
            self.width() // 4 + (1 if x < self.width() % 4 else 0) for x in range(4)
        ]

        self.set_table_layout(header, widths)
        return

    def set_table_layout(self, header: list, widths: list):
        """Update the layout of the file table.

        Parameters
        ----------
        header : list
            A list of strings used for the headers of each column.
        widths : list
            A list of integers with the file widths
        """
        # Add columns
        self.setColumnCount(0)
        self.setColumnCount(len(header))

        # Add column headers, adjust the sizing of the final column.
        self.setHorizontalHeaderLabels(header)

        # Set text alignment for the file status and annotation columns
        right_aligned_columns = [self.columnCount() - 1]
        if self.layout_type == "Annotation":
            right_aligned_columns.append(self.columnCount() - 2)

        delegate = QtO.AlignCenterDelegate(self)
        for column in right_aligned_columns:
            self.setItemDelegateForColumn(column, delegate)

        # Set the width for the file columns
        for column in range(self.columnCount()):
            self.setColumnWidth(column, widths[column])

        # Restore the filenames
        self.update_body()
        return

    # File status updates
    @property
    def file_rows(self):
        """Return the number of rows that the loaded files occupy."""
        rows = max(
            len(self.file_manager.main_files), len(self.file_manager.associated_files)
        )
        return rows

    def update_body(self):
        """Update the text for each loaded file."""
        self.update_main_file_list()
        self.update_associated_file_list()
        self.update_file_queue_status(annotation_updates=False)

        if self.layout_type == "Annotation":
            self.update_annotation_column_status()

    def update_main_file_list(self):
        """Update the main file column."""
        self.setRowCount(self.file_rows)
        for row in range(len(self.file_manager.main_files)):
            filename = path_processing.get_basename(self.file_manager.main_files[row])
            item = QTableWidgetItem(filename)
            self.setItem(row, 0, item)

    def update_associated_file_list(self):
        """Update the associated file column."""
        self.setRowCount(self.file_rows)
        for row in range(len(self.file_manager.associated_files)):
            filename = path_processing.get_basename(
                self.file_manager.associated_files[row]
            )
            item = QTableWidgetItem(filename)
            self.setItem(row, 1, item)

    def update_file_queue_status(self, annotation_updates: bool = True):
        """Add a 'queued' status to each of the loaded files.

        Parameters
        ----------
        body_update : bool, optional
            Determines whether the annotation column needs to also be updated.
            This isn't necessary when ``update_body`` is the call source.
            Default is True.
        """
        last_column = self.columnCount() - 1
        for i in range(self.rowCount()):
            item = QTableWidgetItem("Queued...")
            self.setItem(i, last_column, item)

        if annotation_updates and self.layout_type == "Annotation":
            self.update_annotation_column_status()
        return

    def update_annotation_column_status(self):
        """Update the status of the annotation Region Processed column."""
        annotation_column = self.columnCount() - 2

        if not self.file_manager.annotation_data:
            text = "Load JSON!"
        else:
            text = f"0/{len(self.file_manager.annotation_data.keys())}"

        for row in range(self.rowCount()):
            item = QTableWidgetItem(text)
            self.setItem(row, annotation_column, item)

    def update_analysis_file_status(self, update_status: StatusUpdate):
        """Update the analysis status of a file.

        Parameters
        ----------
        status : StatusUpdate
            A StatusUpdate object that carries the current status of the analysis or
            the visualization.
        """
        # the analysis status will always be in the last column
        update_column = self.columnCount() - 1
        self.selectRow(update_status.file_row)  # select the updated row

        # Update the file status
        self.setItem(
            update_status.file_row,
            update_column,
            QTableWidgetItem(update_status.file_status),
        )

        # update the annotation progress
        if self.layout_type == "Annotation" and update_status.annotation_progress:
            self.setItem(
                update_status.file_row,
                update_column - 1,  # annotation ROI column is one to left
                QTableWidgetItem(update_status.annotation_progress),
            )
        return

    # Selection management
    def update_row_selection(self, row: int):
        """Update the selected row of the table.

        Parameters
        ----------
        row : int
            The index of the row that was selected.
        """
        if row not in self.get_selected_row_indices():
            self.selectRow(row)
        return

    def get_selected_row_indices(self) -> list:
        """Return a list of the selected rows.

        Returns
        -------
        list : selected_rows
            The list of currently selected rows.
        """
        selected_rows = self.selectionModel().selectedRows()
        if len(selected_rows):
            selected_rows = [index.row() for index in selected_rows]

        selected_rows.sort(reverse=True)
        return selected_rows
