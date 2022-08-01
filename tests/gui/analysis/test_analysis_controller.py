import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

from library.gui.analysis.analysis_controller import AnalysisController

from PyQt5.QtCore import Qt


class TestCalls:
    analyzed = False
    canceled = False

    def analyze(self):
        self.analyzed = True

    def cancel(self):
        self.canceled = True


def test_analysis_file_controller(qtbot, mocker):
    test_calls = TestCalls()

    analysisController = AnalysisController(test_calls.analyze, test_calls.cancel)

    qtbot.mouseClick(analysisController.analyzeButton, Qt.LeftButton)
    assert test_calls.analyzed is True

    qtbot.mouseClick(analysisController.cancelButton, Qt.LeftButton)
    assert test_calls.canceled is False  # Should be disabled by default
    analysisController.cancelButton.setEnabled(True)
    qtbot.mouseClick(analysisController.cancelButton, Qt.LeftButton)
    assert test_calls.canceled is True  # Should be disabled by default
