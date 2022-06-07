"""
The QTableWidget used to visualize the loaded files.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from .. import qt_objects as QtO


class AnalysisFileTable(QTableWidget):
    """
    QTableWidget used to view the loaded datasets and their analysis status.

    Parameters:
    file_manager : objects.FileManager
        The file manager that manages the files for an analysis.
    """

    def __init__(self, file_manager):
        """Build the table widget."""
        super().__init__()
        self.file_manager = file_manager

        self.setShowGrid(False)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.verticalHeader().hide()
        self.horizontalHeader().setMinimumSectionSize(100)

        self.setMinimumWidth(400)

        self.apply_default_layout()

        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

    def update_file_analysis_status(self, status):
        """Update the analysis status of a file.

        Parameters:
        status : list

        """
        column = self.columnCount() - 1
        self.selectRow(status[0])
        self.setItem(status[0], column, QTableWidgetItem(status[1]))

        if column == 3 and len(status) == 3:
            self.setItem(status[0], column - 1, QTableWidgetItem(status[2]))
        return

    # Layout management
    def apply_default_layout(self):
        """Apply the default single file layout.

        Implements a two column layout:
        Column 1 shows file names.
        Column 2 shows the analysis status of the file.
        """
        header = ["File Name", "File Status"]
        self.set_table_layout(2, [300, 200], header)
        return

    def apply_annotation_layout(self):
        """Update the table for loaded annotation files.

        Implements a four column layout:
        Column 1 shows the volume file names.
        Column 2 shows the annotation file names.
        Column 3 shows the number of annotation regions.
        Column 4 shows the analysis status of the file.
        """
        header = [
            "File Name",
            "Annotation File Name",
            "Regions Processed",
            "File Status",
        ]
        self.set_table_layout(4, [200, 200, 150, 200], header)
        return

    def apply_csv_layout(self):
        """Update the table for loaded CSV files.

        Implements a three column layout:
        Column 1 shows the vertex file names.
        Column 2 shows the edge file names.
        Column 3 shows the analysis status of the file.
        """
        header = ["File Name - Vertices", "File Name - Edges", "File Status"]
        self.set_table_layout(3, [200] * 3, header)
        return

    def set_fixed_column_format(self, column_index):
        """Apply the fixed layout to the specified column.

        This format incluces a centered alignment with a fixed column width.

        Parameters:
        column_index : int
        """
        delegate = QtO.AlignCenterDelegate(self)  # center alignment
        self.setItemDelegateForColumn(column_index, delegate)
        self.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Fixed)
        return

    def set_table_layout(self, column_count, widths, header):
        """Update the layout of the file table.

        Parameters:
        column_count : int
            Indicates how many many columns should be placed into the table.

        widths : list
            A list of integers indicating how wide each column should be in
            pixels.

        header : list
            A list of strings used for the headers of each column.

        """
        # Add columns and update column size
        self.setColumnCount(0)
        self.setColumnCount(column_count)
        for i in range(column_count):
            self.setColumnWidth(i, widths[i])

        # Add column headers, adjust the sizing of the final column.
        self.setHorizontalHeaderLabels(header)

        # Update format of the status column
        last_column_index = self.columnCount() - 1
        self.set_fixed_column_format(last_column_index)

        # If an annotation file is present, apply the
        # fixed formatting to the annotatino column..
        if last_column_index == 3:
            last_column_index -= 1
            self.set_fixed_column_format(last_column_index - 1)

        # Left align text for the file names
        delegate = QtO.AlignLeftDelegate(self)
        for i in range(last_column_index):
            self.setItemDelegateForColumn(i, delegate)
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        return

    # Selection management
    def update_row_selection(self, row):
        """ "Update the selected row of the table.

        Parameters:
        row : int
        """
        self.selectRow(row)
        return
