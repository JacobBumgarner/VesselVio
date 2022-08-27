"""
The options widget used to configure the analysis options during batch analysis
and visualization.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from PyQt5.QtWidgets import QLabel, QWidget

from library.gui import qt_objects as QtO

from library.objects import GraphAnalysisOptions, GraphAttributeKey


class GraphOptionsWidget(QWidget):
    """An options widget for graph analysis settings and graph feature keys.

    Parameters
    ----------
    fileTable : AnalysisFileTable, optional
        The file table that shows the loaded vasculature files. This option is available
        for the Analysis Page and is passed to this object in order to update the
        column headers for CSV graphs. If non-CSV graphs are loaded, the file table
        will only have two columns. Otherwise, it will have three. Defaults to ``None``.

    """

    def __init__(self, fileTable: "AnalysisFileTable" = None):
        """Construct the widget."""
        super().__init__()
        self.fileTable = fileTable

        self.setFixedWidth(800)
        boxLayout = QtO.new_layout(self, margins=10)

        ### Organized into three columns
        ## Left
        leftColumn = QtO.new_form_layout(alignment="VCenter", vspacing=5)

        formatHeader = QLabel("Graph file format:")
        self.graphFormat = QtO.new_combo(
            ["GraphML", "DIMACS", "GML", "CSV"],
            120,
            connect=self.update_graph_type_options,
        )

        typeHeader = QLabel("Vertex representation:")
        self.graphType = QtO.new_combo(
            ["Branches", "Centerlines"], 120, "Left", self.update_graph_key_options
        )

        delimiterHeader = QLabel("CSV Delimiter:")
        self.csvDelimiterCombo = QtO.new_combo(
            [",", ";", "Tab (\\t)", "Space ( )"],
            120,
        )
        self.csvDelimiterCombo.setDisabled(True)

        self.centerlineSpacer = QLabel("")
        centerlineWidget = QtO.new_widget()
        clLayout = QtO.new_layout(centerlineWidget, no_spacing=True)
        self.centerlineSmoothing = QtO.new_checkbox("Centerline smoothing")
        QtO.add_widgets(clLayout, [self.centerlineSmoothing])

        self.cliqueLabel = QLabel("")
        cliqueWidget = QtO.new_widget()
        cliqueLayout = QtO.new_layout(cliqueWidget, no_spacing=True)
        self.cliqueFiltering = QtO.new_checkbox("Clique filtering")
        QtO.add_widgets(cliqueLayout, [self.cliqueFiltering])

        QtO.add_form_rows(
            leftColumn,
            [
                [formatHeader, self.graphFormat],
                [typeHeader, self.graphType],
                [delimiterHeader, self.csvDelimiterCombo],
                [self.centerlineSpacer, centerlineWidget],
                [self.cliqueLabel, cliqueWidget],
            ],
        )

        ## Middle
        self.middleColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        vertexHeader = QLabel("<b><center>Vertex identifiers:")
        QtO.add_widgets(headerLayout, [vertexHeader])

        xPosHeader = QLabel("X position:")
        self.vertexXPosKey = QtO.new_line_edit("X")

        yPosHeader = QLabel("Y position:")
        self.vertexYPosKey = QtO.new_line_edit("Y")

        zPosHeader = QLabel("Z position:")
        self.vertexZPosKey = QtO.new_line_edit("Z")

        radiusHeader = QLabel("Radius:")
        self.vertexRadiusKey = QtO.new_line_edit("radius")
        self.vertexRadiusKey.setDisabled(True)

        QtO.add_form_rows(
            self.middleColumn,
            [
                columnHeader,
                [xPosHeader, self.vertexXPosKey],
                [yPosHeader, self.vertexYPosKey],
                [zPosHeader, self.vertexZPosKey],
                [radiusHeader, self.vertexRadiusKey],
            ],
        )

        ## Right
        rightColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        edgeHeader = QLabel("<b><center>Edge identifiers:")
        QtO.add_widgets(headerLayout, [edgeHeader])

        edgeSourceHeader = QLabel("Edge source:")
        self.edgeSourceKey = QtO.new_line_edit("Source ID")
        self.edgeSourceKey.setDisabled(True)

        edgeTargetHeader = QLabel("Edge target:")
        self.edgeTargetKey = QtO.new_line_edit("Target ID")
        self.edgeTargetKey.setDisabled(True)

        edgeRadiusHeader = QLabel("Mean segment radius:")
        self.edgeRadiusKey = QtO.new_line_edit("radius_avg")

        edgeLengthHeader = QLabel("Segment length:")
        self.edgeLengthKey = QtO.new_line_edit("length")

        edgeTortuosityHeader = QLabel("Segment tortuosity")
        self.edgeTortuosityKey = QtO.new_line_edit("tortuosity")

        edgeVolumeHeader = QLabel("Segment volume:")
        self.edgeVolumeKey = QtO.new_line_edit("volume")

        edgeSurfaceAreaHeader = QLabel("Segment surface area:")
        self.edgeSurfaceAreaKey = QtO.new_line_edit("surface_area")

        QtO.add_form_rows(
            rightColumn,
            [
                columnHeader,
                [edgeRadiusHeader, self.edgeRadiusKey],
                [edgeLengthHeader, self.edgeLengthKey],
                [edgeTortuosityHeader, self.edgeTortuosityKey],
                [edgeVolumeHeader, self.edgeVolumeKey],
                [edgeSurfaceAreaHeader, self.edgeSurfaceAreaKey],
                [edgeSourceHeader, self.edgeSourceKey],
                [edgeTargetHeader, self.edgeTargetKey],
            ],
        )

        ## Add it all together
        line0 = QtO.new_line("V", 2)
        line1 = QtO.new_line("V", 2)
        QtO.add_widgets(
            boxLayout, [0, leftColumn, line0, self.middleColumn, line1, rightColumn, 0]
        )

    def update_graph_type_options(self):
        """Update activations for the widgets associated with CSV/non-CSV graphs."""
        enable_csv_info = self.graphFormat.currentText() == "CSV"

        if self.fileTable is not None:
            if enable_csv_info:
                self.fileTable.apply_csv_layout()
            else:
                self.fileTable.apply_default_layout()

        self.csvDelimiterCombo.setEnabled(enable_csv_info)
        self.edgeSourceKey.setEnabled(enable_csv_info)
        self.edgeTargetKey.setEnabled(enable_csv_info)
        return

    def update_graph_key_options(self):
        """Update w associated with branch/centerline keys."""
        centerline_graph = self.graphType.currentText() == "Centerlines"

        # Centerline enabled
        self.vertexRadiusKey.setEnabled(centerline_graph)

        # Centerline disabled
        self.edgeRadiusKey.setDisabled(centerline_graph)
        self.edgeLengthKey.setDisabled(centerline_graph)
        self.edgeTortuosityKey.setDisabled(centerline_graph)
        self.edgeVolumeKey.setDisabled(centerline_graph)
        self.edgeSurfaceAreaKey.setDisabled(centerline_graph)
        return

    def prepare_options(self):
        """Return the analysis options for the input graph.

        Returns:
        --------
        graph_options : input_classes.GraphAnalysisOptions
            The input keys and selected parameters necessary to load and analyze a
            pre-constructed vasculature graph.
        """
        # Prepare the attribute_key
        attribute_key = GraphAttributeKey(
            self.vertexXPosKey.text(),
            self.vertexYPosKey.text(),
            self.vertexZPosKey.text(),
            self.vertexRadiusKey.text(),
            self.edgeRadiusKey.text(),
            self.edgeLengthKey.text(),
            self.edgeVolumeKey.text(),
            self.edgeSurfaceAreaKey.text(),
            self.edgeTortuosityKey.text(),
            self.edgeSourceKey.text(),
            self.edgeTargetKey.text(),
        )

        # Identify the csv_delimiter (may not end up being used)
        csv_delimiter = self.csvDelimiterCombo.currentText()
        if len(csv_delimiter) > 1:
            if "Space" in csv_delimiter:
                csv_delimiter = " "
            elif "Tab" in csv_delimiter:
                csv_delimiter = "\t"

        graph_options = GraphAnalysisOptions(
            self.graphFormat.currentText(),
            self.graphType.currentText(),
            self.cliqueFiltering.isChecked(),
            self.centerlineSmoothing.isChecked(),
            attribute_key,
            csv_delimiter,
        )

        return graph_options
