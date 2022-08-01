import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import os

import pytest

from library.gui.analysis import file_table
from library.objects import AnalysisFileManager, StatusUpdate


THIS_PATH = Path(__file__).parent.absolute()
FIXTURE_DIR = Path(*THIS_PATH.parts[: list(THIS_PATH.parts).index("tests") + 1])
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "test_files", "annotation_data")


def test_file_management(qtbot):
    # general table row clearance
    table = file_table.AnalysisFileTable(AnalysisFileManager())
    table.setRowCount(10)
    table.clear_table()
    assert table.rowCount() == 0

    # selected row clearance
    table.setRowCount(5)
    table.selectRow(3)
    table.clear_selected_files()
    assert table.rowCount() == 4


def test_layout_updates(qtbot):
    table = file_table.AnalysisFileTable(AnalysisFileManager())

    # startup columns
    assert table.columnCount() == 2

    # csv columns
    table.apply_csv_layout()
    assert table.columnCount() == 3

    # annotation columns
    table.apply_annotation_layout()
    assert table.columnCount() == 4


## six functions left to test
def test_file_status_updates(qtbot):
    table = file_table.AnalysisFileTable(AnalysisFileManager())
    table.apply_annotation_layout()
    table.setRowCount(2)

    status = StatusUpdate("test update", file_row=1, annotation_progress="1/10")
    table.update_analysis_file_status(status)

    assert table.item(1, 2).text() == "1/10"
    assert table.item(1, 3).text() == "test update"

    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_file_list_updates(qtbot, datafiles):
    # Test file list update for a default load
    table = file_table.AnalysisFileTable(AnalysisFileManager())
    table.file_manager.add_main_files(["test_file"])
    table.update_main_file_list()
    assert table.item(0, 0).text() == "test_file"

    # Check the empty annotations
    table.apply_annotation_layout()
    table.file_manager.add_associated_files(["test_associated"])
    table.update_associated_file_list()
    assert table.item(0, 1).text() == "test_associated"
    assert table.item(0, 2).text() == "Load JSON!"

    # Check loaded annotations
    table.file_manager.add_annotation_JSON(
        os.path.join(datafiles, "Cortex Unique.json")
    )
    table.update_annotation_column_status()
    assert table.item(0, 2).text() == "0/6"

    # Check the queued call
    table.update_file_queue_status()
    assert table.item(0, 3).text() == "Queued..."

    return


def test_row_selection(qtbot):
    table = file_table.AnalysisFileTable(AnalysisFileManager())
    table.setRowCount(5)

    table.update_row_selection(2)
    assert len(table.selectionModel().selectedRows()) == 1

    for row in [2, 1, 3]:
        table.update_row_selection(row)
    selected_rows = table.get_selected_row_indices()
    assert selected_rows == [3, 2, 1]
