"""
The options widget used to configure the analysis options during batch analysis
and visualization.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


from library import input_classes as IC
from library.gui import qt_objects as QtO
from PyQt5.QtWidgets import QLabel, QWidget


class GraphOptions(QWidget):
    """The widget"""

    def __init__(self, fileSheet=None):
        super().__init__()
        self.fileSheet = fileSheet

        self.setFixedWidth(800)
        boxLayout = QtO.new_layout(self, margins=10)

        ### Organized into three columns
        ## Left
        leftColumn = QtO.new_form_layout(alignment="VCenter", vspacing=5)

        formatHeader = QLabel("Graph file format:")
        self.graphFormat = QtO.new_combo(
            ["GraphML", "DIMACS", "GML", "CSV"], 120, connect=self.update_graph_options
        )

        typeHeader = QLabel("Vertex representation:")
        self.graphType = QtO.new_combo(
            ["Branches", "Centerlines"], 120, "Left", self.update_graph_type
        )

        delimiterHeader = QLabel("CSV Delimiter:")
        self.delimiterCombo = QtO.new_combo(
            [",", ";", "Tab (\\t)", "Space ( )"],
            120,
        )
        self.delimiterCombo.setDisabled(True)

        self.clLabel = QLabel("")
        self.centerlineLine = QtO.new_widget()
        clLayout = QtO.new_layout(self.centerlineLine, no_spacing=True)
        self.centerlineSmoothing = QtO.new_checkbox("Centerline smoothing")
        QtO.add_widgets(clLayout, [self.centerlineSmoothing])

        self.cliqueLabel = QLabel("")
        self.cliqueLine = QtO.new_widget()
        cliqueLayout = QtO.new_layout(self.cliqueLine, no_spacing=True)
        self.cliqueFiltering = QtO.new_checkbox("Clique filtering")
        QtO.add_widgets(cliqueLayout, [self.cliqueFiltering])

        QtO.add_form_rows(
            leftColumn,
            [
                [formatHeader, self.graphFormat],
                [typeHeader, self.graphType],
                [delimiterHeader, self.delimiterCombo],
                [self.clLabel, self.centerlineLine],
                [self.cliqueLabel, self.cliqueLine],
            ],
        )

        ## Middle
        self.middleColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        vertexHeader = QLabel("<b><center>Vertex identifiers:")
        QtO.add_widgets(headerLayout, [vertexHeader])

        xHeader = QLabel("X position:")
        self.xEdit = QtO.new_line_edit("X")

        yHeader = QLabel("Y position:")
        self.yEdit = QtO.new_line_edit("Y")

        zHeader = QLabel("Z position:")
        self.zEdit = QtO.new_line_edit("Z")

        radiusHeader = QLabel("Radius:")
        self.vertexRadiusEdit = QtO.new_line_edit("radius")
        self.vertexRadiusEdit.setDisabled(True)

        QtO.add_form_rows(
            self.middleColumn,
            [
                columnHeader,
                [xHeader, self.xEdit],
                [yHeader, self.yEdit],
                [zHeader, self.zEdit],
                [radiusHeader, self.vertexRadiusEdit],
            ],
        )

        ## Right
        rightColumn = QtO.new_form_layout(vspacing=5)

        columnHeader = QtO.new_widget()
        headerLayout = QtO.new_layout(columnHeader, no_spacing=True)
        edgeHeader = QLabel("<b><center>Edge identifiers:")
        QtO.add_widgets(headerLayout, [edgeHeader])

        sourceHeader = QLabel("Edge source:")
        self.sourceEdit = QtO.new_line_edit("Source ID")
        self.sourceEdit.setDisabled(True)

        targetHeader = QLabel("Edge target:")
        self.targetEdit = QtO.new_line_edit("Target ID")
        self.targetEdit.setDisabled(True)

        segRadiusHeader = QLabel("Mean segment radius:")
        self.segRadiusEdit = QtO.new_line_edit("radius_avg")

        segLengthHeader = QLabel("Segment length:")
        self.segLengthEdit = QtO.new_line_edit("length")

        segTortHeader = QLabel("Segment tortuosity")
        self.segTortuosityEdit = QtO.new_line_edit("tortuosity")

        segVolumeHeader = QLabel("Segment volume:")
        self.segVolumeEdit = QtO.new_line_edit("volume")

        segSAHeader = QLabel("Segment surface area:")
        self.segSAEdit = QtO.new_line_edit("surface_area")

        QtO.add_form_rows(
            rightColumn,
            [
                columnHeader,
                [segRadiusHeader, self.segRadiusEdit],
                [segLengthHeader, self.segLengthEdit],
                [segTortHeader, self.segTortuosityEdit],
                [segVolumeHeader, self.segVolumeEdit],
                [segSAHeader, self.segSAEdit],
                [sourceHeader, self.sourceEdit],
                [targetHeader, self.targetEdit],
            ],
        )

        ## Add it all together
        line0 = QtO.new_line("V", 2)
        line1 = QtO.new_line("V", 2)
        QtO.add_widgets(
            boxLayout, [0, leftColumn, line0, self.middleColumn, line1, rightColumn, 0]
        )

    def update_graph_options(self):
        enable_csv_info = False
        if self.graphFormat.currentText() == "CSV":
            if self.fileSheet:
                self.fileSheet.init_csv()
            enable_csv_info = True
        else:
            if self.fileSheet:
                self.fileSheet.init_default()

        self.delimiterCombo.setEnabled(enable_csv_info)
        self.vertexRadiusEdit.setEnabled(enable_csv_info)
        self.sourceEdit.setEnabled(enable_csv_info)
        self.targetEdit.setEnabled(enable_csv_info)
        self.update_graph_type()
        return

    def update_graph_type(self):
        type = self.graphType.currentText()
        enabled = False
        if type == "Centerlines":
            enabled = True

        # Centerline enabled
        self.vertexRadiusEdit.setEnabled(enabled)

        # Centerline disabled
        self.segRadiusEdit.setDisabled(enabled)
        self.segLengthEdit.setDisabled(enabled)
        self.segTortuosityEdit.setDisabled(enabled)
        self.segVolumeEdit.setDisabled(enabled)
        self.segSAEdit.setDisabled(enabled)
        return

    def prepare_options(self):
        # Prepare attribute key
        a_key = IC.AttributeKey(
            self.xEdit.text(),
            self.yEdit.text(),
            self.zEdit.text(),
            self.vertexRadiusEdit.text(),
            self.segRadiusEdit.text(),
            self.segLengthEdit.text(),
            self.segVolumeEdit.text(),
            self.segSAEdit.text(),
            self.segTortuosityEdit.text(),
            self.sourceEdit.text(),
            self.targetEdit.text(),
        )

        delimiter = self.delimiterCombo.currentText()
        if len(delimiter) > 1:
            if delimiter[0] == "S":
                delimiter = " "
            elif delimiter[0] == "T":
                delimiter = "\t"
        graph_options = IC.GraphOptions(
            self.graphFormat.currentText(),
            self.graphType.currentText(),
            self.cliqueFiltering.isChecked(),
            self.centerlineSmoothing.isChecked(),
            a_key,
            delimiter,
        )
        return graph_options
