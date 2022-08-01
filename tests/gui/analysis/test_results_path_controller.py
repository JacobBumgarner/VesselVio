from library.gui.analysis import results_path_controller

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog


def test_set_results_dir(qtbot, mocker):
    controller = results_path_controller.ResultsPathController()
    expected_path = "/Users/jacobbumgarner/Desktop/VesselVio"
    mocker.patch.object(QFileDialog, "getExistingDirectory", return_value=expected_path)
    qtbot.mouseClick(controller.changeFolder, Qt.LeftButton)

    assert controller.resultsPath.text() == expected_path
    return


def test_path_errors(qtbot):
    controller = results_path_controller.ResultsPathController()

    controller.highlight_empty_results_path_error()
    assert controller.resultsPath.styleSheet() == controller.errorPathStyle

    controller.clear_results_path_error()
    assert controller.resultsPath.styleSheet() == controller.defaultPathStyle
