import sys


sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

from library import input_classes as IC
from library.gui.analysis_options_widget import AnalysisOptions
from PyQt5.QtWidgets import QApplication


def creation_test():
    _ = QApplication(sys.argv)
    widget = AnalysisOptions(visualizing=False)
    assert hasattr(widget, "saveGraph")
    assert hasattr(widget, "saveSegmentResults")

    widget = AnalysisOptions(visualizing=True)
    assert not hasattr(widget, "saveGraph")
    assert not hasattr(widget, "saveSegmentResults")
    return


def default_value_test():
    _ = QApplication(sys.argv)
    widget = AnalysisOptions(visualizing=False)

    # Resolution default values
    assert widget.isoResolution.value() == 1
    assert widget.anisoX.value() == 1
    assert widget.anisoY.value() == 1
    assert widget.anisoY.value() == 1

    # Prune & filter lengths
    assert widget.pruneLength.value() == 5.0
    assert widget.filterLength.value() == 10.0
    return


def dimensions_test():
    _ = QApplication(sys.argv)
    widget = AnalysisOptions(visualizing=False)

    assert widget.imageDimension.currentText() == "3D"
    assert widget.isoResolution.suffix() == " µm\u00B3"

    widget.imageDimension.setCurrentIndex(1)
    assert widget.imageDimension.currentText() == "2D"
    assert widget.isoResolution.suffix() == " µm\u00B2"
    print(widget.anisoZ.suffix())
    assert widget.anisoZ.suffix() == " µm\u00B3"


def options_export():
    _ = QApplication(sys.argv)
    widget = AnalysisOptions(visualizing=False)

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
