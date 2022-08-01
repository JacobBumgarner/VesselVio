import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import os

import pytest

from library.gui.analysis import AnalysisFileController, AnalysisFileTable
from library.gui.file_loading_widgets import AnnotationFileLoader, CSVGraphFileLoader
from library.gui.options_widgets import GraphOptionsWidget
from library.objects import AnalysisFileManager
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QFileDialog, QTabWidget

THIS_PATH = Path(__file__).parent.absolute()
FIXTURE_DIR = Path(*THIS_PATH.parts[: list(THIS_PATH.parts).index("tests") + 1])
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "test_files", "annotation_data")

IMAGE_PATHS = [["fake_folder/image_01.nii", "fake_folder/image_02.nii"]]

ANNOTATION_PATHS = [["fake_folder/anno_01.nii", "fake_folder/anno_02.nii"]]

ANNOTATION_JSON = [os.path.join(ANNOTATION_DIR, "Cortex Unique.json")]

GRAPH_PATHS = [["fake_folder/graph_01.graphml"]]

CSV_PATHS = [["fake_folder/edges_01.csv", "fake_folder/edges_02.csv"]]


@pytest.fixture
def controller():
    file_manager = AnalysisFileManager()
    fileTable = AnalysisFileTable(file_manager)
    graphOptions = GraphOptionsWidget(fileTable)
    optionsBox = QTabWidget()
    controller = AnalysisFileController(
        file_manager, fileTable, graphOptions, optionsBox
    )
    return controller


def test_file_loading_dispatch_volume(
    qtbot, mocker, controller: AnalysisFileController
):
    mocker.patch.object(QFileDialog, "getOpenFileNames", return_value=IMAGE_PATHS)
    qtbot.mouseClick(controller.loadButton, Qt.LeftButton)

    assert controller.fileTable.file_rows == 2
    filename = controller.fileTable.item(0, 0).text()
    assert filename == os.path.basename(IMAGE_PATHS[0][0])
    assert controller.file_manager.main_files == IMAGE_PATHS[0]

    # test to make sure that files are cleared once analyzed
    controller.file_manager.analyzed = True
    mocker.patch.object(QFileDialog, "getOpenFileNames", return_value=[None])
    qtbot.mouseClick(controller.loadButton, Qt.LeftButton)

    assert controller.fileTable.file_rows == 0
    assert controller.file_manager.analyzed is False


def test_file_loading_dispatch_graph(qtbot, mocker, controller: AnalysisFileController):
    qtbot.keyClicks(controller.datasetType, "Graph")
    mocker.patch.object(QFileDialog, "getOpenFileNames", return_value=GRAPH_PATHS)
    qtbot.mouseClick(controller.loadButton, Qt.LeftButton)

    assert controller.fileTable.file_rows == 1
    filename = controller.fileTable.item(0, 0).text()
    assert filename == os.path.basename(GRAPH_PATHS[0][0])
    assert controller.file_manager.main_files == GRAPH_PATHS[0]


def test_file_loading_dispatch_annotation_volume(
    qtbot, mocker, controller: AnalysisFileController
):
    qtbot.keyClicks(controller.annotationType, "ID")

    mocker.patch.object(AnnotationFileLoader, "exec_", return_value=True)
    mocker.patch.object(AnnotationFileLoader, "associated_files", ANNOTATION_PATHS[0])

    qtbot.mouseClick(controller.loadButton, Qt.LeftButton)

    assert controller.fileTable.file_rows == 2
    filename = controller.fileTable.item(0, 1).text()
    assert filename == os.path.basename(ANNOTATION_PATHS[0][0])
    assert controller.file_manager.associated_files == ANNOTATION_PATHS[0]

    return


def test_file_loading_dispatch_csv_graphs(
    qtbot, mocker, controller: AnalysisFileController
):
    qtbot.keyClicks(controller.datasetType, "Graph")
    qtbot.keyClicks(controller.graphOptions.graphFormat, "CSV")

    # test loading annotation files
    mocker.patch.object(CSVGraphFileLoader, "exec_", return_value=True)
    mocker.patch.object(CSVGraphFileLoader, "main_files", CSV_PATHS[0])

    qtbot.mouseClick(controller.loadButton, Qt.LeftButton)

    assert controller.fileTable.file_rows == 2
    filename = controller.fileTable.item(0, 0).text()
    assert filename == os.path.basename(CSV_PATHS[0][0])
    assert controller.file_manager.main_files == CSV_PATHS[0]

    return


def test_update_main_files(controller: AnalysisFileController):
    controller.update_main_files(IMAGE_PATHS[0])

    assert controller.file_manager.main_files == IMAGE_PATHS[0]
    assert controller.fileTable.rowCount() == 2


def test_update_associated_files(controller: AnalysisFileController):
    controller.update_main_files(ANNOTATION_PATHS[0])

    assert controller.file_manager.main_files == ANNOTATION_PATHS[0]
    assert controller.fileTable.rowCount() == 2


def test_load_vesselvio_annotation(qtbot, mocker, controller: AnalysisFileController):
    mocker.patch.object(QFileDialog, "getOpenFileName", return_value=ANNOTATION_JSON)

    qtbot.keyClicks(controller.annotationType, "ID")

    # add some mock files
    controller.update_main_files(IMAGE_PATHS[0])
    controller.load_vesselvio_annotation_file()

    count = controller.fileTable.item(0, 2).text()

    assert count == "0/6"
    assert controller.loadedJSON.text() == os.path.basename(ANNOTATION_JSON[0])


def test_clear_selected_files(qtbot, controller: AnalysisFileController):
    controller.update_main_files(IMAGE_PATHS[0])

    qtbot.mouseClick(controller.clearSelectedFileButton, Qt.LeftButton)

    assert len(controller.file_manager.main_files) == 2
    assert controller.fileTable.rowCount() == 2

    controller.fileTable.selectRow(1)
    qtbot.mouseClick(controller.clearSelectedFileButton, Qt.LeftButton)

    assert len(controller.file_manager.main_files) == 1
    assert controller.fileTable.rowCount() == 1


def test_clear_all_files(qtbot, controller: AnalysisFileController):
    controller.update_main_files(IMAGE_PATHS[0])

    qtbot.mouseClick(controller.clearAllFilesButton, Qt.LeftButton)

    assert len(controller.file_manager.main_files) == 0
    assert controller.fileTable.rowCount() == 0


def test_update_dataset_type_view(qtbot, controller: AnalysisFileController):
    qtbot.keyClicks(controller.datasetType, "Graph")
    assert controller.fileTable.layout_type == "Default"

    qtbot.keyClicks(controller.graphOptions.graphFormat, "CSV")
    assert controller.fileTable.layout_type == "CSV"

    # qtbot.keyClicks(controller.datasetType, "Volume")
    controller.datasetType.setCurrentIndex(0)
    assert controller.fileTable.layout_type == "Default"


def test_update_annotation_type_view(qtbot, controller: AnalysisFileController):
    qtbot.keyClicks(controller.datasetType, "Graph")
    assert controller.annotationType.isEnabled() is False
    assert controller.fileTable.layout_type == "Default"

    # qtbot.keyClicks(controller.datasetType, "Volume")  # not working
    controller.datasetType.setCurrentIndex(0)
    assert controller.annotationType.isEnabled() is True

    qtbot.keyClicks(controller.annotationType, "ID")
    assert controller.fileTable.layout_type == "Annotation"
    return
