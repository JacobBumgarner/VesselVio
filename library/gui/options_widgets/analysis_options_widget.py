"""Analysis options widget for batch dataset processing."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QLabel, QWidget

from library import input_classes as IC
from library.gui import qt_objects as QtO


class AnalysisOptions(QWidget):
    """Options widget used to define the analysis parameters.

    Also dictates the results export settings during batch analysis
    and visualization.

    Parameters:
    visualizing : bool
        Determines whether to add the Segment Results Export and Save Graph
        options to the analysis page.
    """

    def __init__(self, visualizing=False):
        """Create the analysis options widget."""
        super().__init__()

        # Main widget layout
        mainLayout = QtO.new_layout(self, "H")

        # Two column layout:
        #   left column - unit, resolution type, and analysis dimensions options
        #   right column - resolution, filtering, pruning, and export options

        ## Left column options
        leftColumn = QtO.new_form_layout(alignment="VCenter", vspacing=5)

        unitHeader = QLabel("Unit:")
        self.unit = QtO.new_combo(["µm", "mm"], 120, connect=self.update_units)

        resolutionHeader = QLabel("Resolution type:")
        self.resolutionType = QtO.new_combo(
            ["Isotropic", "Anisotropic"], 120, connect=self.update_isotropy
        )

        dimensionHeader = QLabel("Analysis dimensions:")
        self.imageDimension = QtO.new_combo(
            ["3D", "2D"], 120, connect=self.update_dimensions
        )

        QtO.add_form_rows(
            leftColumn,
            [
                [unitHeader, self.unit],
                [resolutionHeader, self.resolutionType],
                [dimensionHeader, self.imageDimension],
            ],
        )

        ## Right column options
        rightOptions = QtO.new_widget()
        rightOptionsLayout = QtO.new_layout(
            rightOptions, orient="V", spacing=5, margins=0
        )

        # Isotropic Resolution Widget
        self.isoResolutionWidget = QtO.new_widget()
        isoResLayout = QtO.new_layout(self.isoResolutionWidget, margins=0)
        isoResLabel = QLabel("Image resolution:")
        self.isoResolution = QtO.new_doublespin(
            0.01, 100, 1, 100, suffix=" µm\u00B3", decimals=2
        )
        QtO.add_widgets(isoResLayout, [isoResLabel, self.isoResolution])

        # Anisotropic Resolution Widget
        self.anisoResolutionWidget = QtO.new_widget()
        anisoResLayout = QtO.new_layout(
            self.anisoResolutionWidget, spacing=0, margins=0
        )
        anisoResLabel = QLabel("Image resolution (XYZ):")
        self.anisoX = QtO.new_doublespin(0.01, 100, 1, width=60, decimals=2)
        self.anisoY = QtO.new_doublespin(0.01, 100, 1, width=60, decimals=2)
        self.anisoZ = QtO.new_doublespin(
            0.01, 100, 1, width=80, suffix=" µm\u00B3", decimals=2
        )
        QtO.add_widgets(
            anisoResLayout, [anisoResLabel, 6, self.anisoX, self.anisoY, self.anisoZ]
        )
        self.anisoResolutionWidget.setVisible(False)

        # Segment Filtering Widget
        filterLengthWidget = QtO.new_widget()
        filterLengthLayout = QtO.new_layout(filterLengthWidget, margins=0)
        self.filterCheckBox = QtO.new_checkbox("Filter isolated segments shorter than:")
        self.filterCheckBox.setChecked(True)
        self.filterLength = QtO.new_doublespin(0.01, 1000, 10, width=100, suffix=" µm")
        QtO.add_widgets(filterLengthLayout, [self.filterCheckBox, self.filterLength])

        # Segment Pruning Widget
        pruneLengthWidget = QtO.new_widget()
        pruenLengthLayout = QtO.new_layout(pruneLengthWidget, margins=0)
        self.pruneCheckBox = QtO.new_checkbox("Prune end point segments shorter than:")
        self.pruneCheckBox.setChecked(True)
        self.pruneLength = QtO.new_doublespin(0.01, 1000, 5, width=100, suffix=" µm")
        QtO.add_widgets(pruenLengthLayout, [self.pruneCheckBox, self.pruneLength])

        widgets = [
            0,
            self.isoResolutionWidget,
            self.anisoResolutionWidget,
            filterLengthWidget,
            pruneLengthWidget,
            0,
        ]

        # Add csv and graph export options to the analysis page
        if not visualizing:
            segmentResultsWidget = QtO.new_widget()
            segmentResultsLayout = QtO.new_layout(segmentResultsWidget, margins=0)
            self.saveSegmentResults = QtO.new_checkbox(
                "Export detailed segment features to individual csv files"
            )
            QtO.add_widgets(segmentResultsLayout, [self.saveSegmentResults])

            graphExportWidget = QtO.new_widget()
            graphExportLayout = QtO.new_layout(graphExportWidget, margins=0)
            self.saveGraph = QtO.new_checkbox("Save graph files of datasets")
            QtO.add_widgets(graphExportLayout, [self.saveGraph])

            # Insert these widgets into the main widgets
            widgets[-1:-1] = [segmentResultsWidget, graphExportWidget]

        QtO.add_widgets(rightOptionsLayout, widgets, "Left")

        # Add it all together now
        line = QtO.new_line("V", 2)
        QtO.add_widgets(mainLayout, [0, leftColumn, line, rightOptions, 0])

    def update_dimensions(self):
        """Update the unit display of the analysis options.

        Represents either 2D or 3D units.

        Calls self.update_units() to ensure that the degree of units is
        appropriate.
        """
        if self.imageDimension.currentText() == "2D":
            self.anisoResolutionWidget.setVisible(False)
            self.isoResolutionWidget.setVisible(True)
            self.resolutionType.setCurrentIndex(0)
        self.update_units()
        return

    def update_isotropy(self):
        """Ensure that the resolution input matches resolution type.

        If 'Anisotropic' is selected, disables the '2D' image dimension option.
        """
        iso_resolution = (
            True if self.resolutionType.currentText() == "Isotropic" else False
        )
        if not iso_resolution:
            self.imageDimension.setCurrentIndex(0)
        self.isoResolutionWidget.setVisible(iso_resolution)
        self.anisoResolutionWidget.setVisible(not iso_resolution)
        return

    def update_units(self):
        """Update the exponent of the shown parameters."""
        unit = " " + self.unit.currentText()
        exponent = "\u00B3"
        if self.imageDimension.currentText() == "2D":
            exponent = "\u00B2"
        suffix = unit + exponent
        self.isoResolution.setSuffix(suffix)
        self.anisoZ.setSuffix(suffix)
        self.filterLength.setSuffix(unit)
        self.pruneLength.setSuffix(unit)
        return

    def prepare_options(self, results_folder=None, visualization=False):
        """Prepare the input options for an anlaysis or visualization.

        Parameters:
        results_folder : str, optional
            Default: None
            The folder where the results will be exported.

        visualization : bool, optional
            Default: False
            Indicates whether the results will be used for an analysis or
            visualization

        Returns:
        input_classes.AnalysisOptions

        """
        # resolution

        image_dim = int(self.imageDimension.currentText()[0])

        if image_dim == 2 or self.resolutionType.currentText() == "Isotropic":
            resolution = self.isoResolution.value()
        elif self.resolutionType.currentText() == "Anisotropic":
            X = self.anisoX.value()
            Y = self.anisoY.value()
            Z = self.anisoZ.value()
            resolution = [X, Y, Z]

        if self.pruneCheckBox.isChecked():
            prune_length = self.pruneLength.value()
        else:
            prune_length = 0

        if self.filterCheckBox.isChecked():
            filter_length = self.filterLength.value()
        else:
            filter_length = 0

        max_radius = 150  # Vestigial

        save_seg_results = (
            False if visualization else self.saveSegmentResults.isChecked()
        )
        save_graph = False if visualization else self.saveGraph.isChecked()

        analysis_options = IC.AnalysisOptions(
            results_folder,
            resolution,
            prune_length,
            filter_length,
            max_radius,
            save_seg_results,
            save_graph,
            image_dim,
        )

        return analysis_options
