import sys

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")
from library import input_classes as IC
from library.gui.analysis_options_widget import AnalysisOptions
from PyQt5.QtCore import Qt


def test_widget_creation(qtbot):
    widget = AnalysisOptions(visualizing=False)
    assert hasattr(widget, "saveGraph")
    assert hasattr(widget, "saveSegmentResults")

    widget = AnalysisOptions(visualizing=True)
    assert not hasattr(widget, "saveGraph")
    assert not hasattr(widget, "saveSegmentResults")

    return


def test_default_values(qtbot):
    widget = AnalysisOptions()

    # Resolution default values
    assert widget.isoResolution.value() == 1
    assert widget.anisoX.value() == 1
    assert widget.anisoY.value() == 1
    assert widget.anisoY.value() == 1

    # Prune & filter lengths
    assert widget.pruneLength.value() == 5.0
    assert widget.filterLength.value() == 10.0
    return


def test_dimensions(qtbot):
    widget = AnalysisOptions()
    widget.show()
    qtbot.addWidget(widget)

    assert widget.imageDimension.currentText() == "3D"
    assert widget.isoResolution.suffix() == " µm\u00B3"

    qtbot.keyClicks(widget.imageDimension, str("2D"))
    assert widget.imageDimension.currentText() == "2D"
    assert widget.isoResolution.suffix() == " µm\u00B2"


def test_isotropy(qtbot):
    widget = AnalysisOptions()
    widget.show()
    qtbot.addWidget(widget)

    assert widget.resolutionType.currentText() == "Isotropic"
    assert widget.isoResolutionWidget.isVisible()
    assert not widget.anisoResolutionWidget.isVisible()

    qtbot.keyClicks(widget.resolutionType, "Anisotropic")
    assert not widget.isoResolutionWidget.isVisible()
    assert widget.anisoResolutionWidget.isVisible()


def test_options_export(qtbot):
    widget = AnalysisOptions()
    widget.show()
    qtbot.addWidget(widget)

    options = widget.prepare_options()
    assert isinstance(options, IC.AnalysisOptions)
    assert options.filter_length == 10
    assert options.prune_length == 5
    assert options.image_dimensions == 3
    assert options.max_radius == 150
    assert options.results_folder is None
    assert options.save_graph is False
    assert options.save_seg_results is False
    assert options.resolution == 1

    # Adjust the options
    qtbot.keyClicks(widget.resolutionType, "Anisotropic")
    qtbot.mouseClick(widget.pruneCheckBox, Qt.LeftButton)
    qtbot.mouseClick(widget.filterCheckBox, Qt.LeftButton)

    options = widget.prepare_options()
    assert isinstance(options, IC.AnalysisOptions)
    assert options.filter_length == 0
    assert options.prune_length == 0
    assert options.image_dimensions == 3
    assert options.max_radius == 150
    assert options.results_folder is None
    assert options.save_graph is False
    assert options.save_seg_results is False
    assert options.resolution == [1, 1, 1]
