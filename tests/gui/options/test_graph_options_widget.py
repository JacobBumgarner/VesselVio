import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import pytest
from library.gui.analysis.file_table import AnalysisFileTable
from library.gui.options_widgets.graph_options_widget import GraphOptionsWidget
from library.objects import GraphAnalysisOptions
from library.objects.analysis_file_manager import AnalysisFileManager


@pytest.fixture
def graphOptions():
    file_manager = AnalysisFileManager()
    fileTable = AnalysisFileTable(file_manager)
    options = GraphOptionsWidget(fileTable)
    return options


def test_widget_init(qtbot):
    # rather than testing the presence of the attributes, just check enabled
    file_manager = AnalysisFileManager()
    fileTable = AnalysisFileTable(file_manager)
    options = GraphOptionsWidget(fileTable)

    assert options.csvDelimiterCombo.isEnabled() is False
    assert options.centerlineSmoothing.isChecked() is False
    assert options.cliqueFiltering.isChecked() is False


def test_update_graph_type_options(qtbot, graphOptions: GraphOptionsWidget):
    assert graphOptions.centerlineSmoothing.isChecked() is False

    qtbot.keyClicks(graphOptions.graphFormat, "CSV")

    assert graphOptions.fileTable.layout_type == "CSV"
    assert graphOptions.csvDelimiterCombo.isEnabled() is True
    assert graphOptions.edgeSourceKey.isEnabled() is True
    assert graphOptions.edgeTargetKey.isEnabled() is True


def test_update_graph_key_options(qtbot, graphOptions: GraphOptionsWidget):
    assert graphOptions.vertexRadiusKey.isEnabled() is False

    qtbot.keyClicks(graphOptions.graphType, "Centerlines")

    assert graphOptions.vertexRadiusKey.isEnabled() is True
    assert graphOptions.edgeRadiusKey.isEnabled() is False
    assert graphOptions.edgeLengthKey.isEnabled() is False
    assert graphOptions.edgeTortuosityKey.isEnabled() is False
    assert graphOptions.edgeVolumeKey.isEnabled() is False
    assert graphOptions.edgeSurfaceAreaKey.isEnabled() is False


def test_prepare_options(qtbot, graphOptions: GraphOptionsWidget):
    graph_options = graphOptions.prepare_options()

    assert isinstance(graph_options, GraphAnalysisOptions)
