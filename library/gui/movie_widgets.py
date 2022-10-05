"""
The movie widgets related to movie generation in VesselVio. Currently users can
generate orbital and path-based (flythrough) movies of the rendered vasculature
meshes.
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"

import sys

import imageio_ffmpeg  # Needed for PyInstaller

import pyvista as pv
from imageio import get_writer

from library import (
    helpers,
    input_classes as IC,
    movie_processing as MovProc,
    qt_threading as QtTh,
)
from library.gui import qt_objects as QtO

from PyQt5.Qt import pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLayout,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


#####################
### Orbit widgets ###
#####################
class OrbitWidget(QWidget):
    """The dialogue used to create an orbital movie around a mesh.

    Allows users to move the plotter around the visaulized meshes and generate orbital
    paths in the plane orthogonal to the viewup angle.

    Parameters
    ----------
    plotter : PyVista.Plotter
        The plotter currently being used for the main application.
    """

    def __init__(self, plotter):
        """Build the widget."""
        super().__init__()
        self.plotter = plotter
        self.orbitPathActors = IC.OrbitActors()
        widgetLayout = QtO.new_layout(self, "V")
        formLayout = QtO.new_form_layout()

        pathLabel = QLabel("Camera Path")
        self.updateOrbitButton = QtO.new_button("Update", self.update_orbit)

        lengthLabel = QLabel("Movie Duration")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )

        QtO.add_form_rows(
            formLayout,
            [[pathLabel, self.updateOrbitButton], [lengthLabel, self.movieLength]],
        )
        QtO.add_widgets(widgetLayout, [0, formLayout, 0])

        self.default_setup()

    def update_orbit(self):
        """Update the orbit path for the movie based on the current plotter position."""
        path_seed = self.plotter.camera_position
        self.orbit_path = MovProc.generate_orbital_path(path_seed)
        self.update_path_actors()

    def update_path_actors(self):
        """Update the position of the orbital path actor."""
        self.remove_path_actors()
        self.orbitPathActors = MovProc.generate_orbit_path_actors(
            self.plotter, self.orbit_path
        )

    def remove_path_actors(self):
        """Eliminate and destroy all path actors."""
        for actor in self.orbitPathActors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor, reset_camera=False)
                del actor

    def generate_path(self, framerate: int):
        """Generate an orbital path with with the requested frame count.

        Parameters
        ----------
        framerate : int
            framerate used to generate the output frames

        Returns
        -------
        list
            (n,3,3) shaped list where each n index contains a
            plotter.camera_position

        """
        frames = MovProc.time_to_frames(framerate, self.movieLength.value())
        self.plotter.camera_position = self.orbit_path[0]
        return MovProc.generate_orbital_path(self.plotter.camera_position, frames)

    def reset(self):
        """Reset the widget."""
        self.remove_path_actors()

    def default_setup(self):
        """Provide a default orbit for the widget when called."""
        self.update_orbit()


##########################
### Flythrough widgets ###
##########################
class FlyThroughTable(QTableWidget):
    """A table widget used to keep track of/modify keyframes for flythrough movies.

    As long as there is at least one column in the table, it will be selected.
    Also contains a key_frame list that keeps track of the keyframe
    plotter.camera_positions

    Parameters
    ----------
    plotter : PyVista.Plotter
        The active plotter of the app.
    update_path_actors : Callable
        The update_path_actors of the parent FlyThroughWidget should be passed
    """

    key_frames = []
    selected_column = 0

    def __init__(self, plotter, update_path_actors):
        """Build the widget."""
        super().__init__()
        self.plotter = plotter
        self.update_path_actors = update_path_actors

        # Boiler plate
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectColumns)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Header boiler
        self.horizontalHeader().setDefaultSectionSize(30)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setStretchLastSection(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().hide()

        self.setFixedSize(240, 40)

        # Set the column headers
        self.setRowCount(1)
        self.setHorizontalHeaderLabels(["Key Frame"])

        # Connect the selection changed to the plotter
        self.selectionModel().selectionChanged.connect(self.update_plotter_view)
        self.cellClicked.connect(self.update_plotter_view)

    # Selection processing
    def default_selection(self):
        """Select the first column of the table by default."""
        if not self.selectionModel().hasSelection():
            self.selectColumn(0)

    def get_selected_column_index(self):
        """Identifie the selected column of the model."""
        if self.selectionModel().hasSelection():
            model = self.selectionModel()
            selection = model.selectedColumns()[0]
            keyframe_index = selection.column()
        else:
            keyframe_index = 0
        return int(keyframe_index)

    def update_plotter_view(self):
        """Update the position of the plotter based on the current table selection."""
        model = self.selectionModel()
        if not model.hasSelection():
            self.selected_column = 0
            return

        self.selected_column = model.selectedColumns()[0].column()
        MovProc.post_path_plotter_update(
            self.plotter, self.key_frames[self.selected_column], orbit=False
        )

    # column Processing
    def add_column(self):
        """Inserts a column into the table at the current index."""
        column_index = self.get_selected_column_index()

        if "After" in self.sender().text() and self.columnCount() > 0:
            column_index += 1
        self.insertColumn(column_index)  # add a column
        # self.default_selection()  # make sure a column is selected
        # add the keyframe index
        item = QTableWidgetItem("new_frame")
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(0, column_index, item)

        # update keyframes
        self.key_frames.insert(column_index, self.plotter.camera_position)

        # update columns - must happen after key_frames is updated
        self.rename_columns()
        self.selectColumn(column_index)

        # update the plotter actors from the parent widget
        self.update_path_actors()

    def remove_column(self):
        """Remove the currently selected column."""
        index = self.currentColumn()
        if index >= 0:
            # update the selection, if there are columns left
            if index - 1 >= 0:
                self.selectColumn(index - 1)
            elif index + 1 < self.columnCount():
                self.selectColumn(index + 1)

            # update the columns
            self.removeColumn(index)
            self.rename_columns()

            # update the key_frame list
            self.key_frames.pop(index)

            # update the plotter actors from the parent widget
            self.update_path_actors()

    def rename_columns(self):
        """Renams the keyframes of the table by ascending order."""
        for i in range(self.columnCount()):
            item = self.item(0, i)
            item.setText(str(i + 1))

    def load_frames(self, key_frames):
        """Load keyframes from previously saved options."""
        self.key_frames = key_frames

        # Reset the columns, add new items
        self.setColumnCount(len(key_frames))
        for i in range(self.columnCount()):
            item = QTableWidgetItem(str(i + 1))
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(0, i, item)

        self.update_path_actors()

    def reset(self):
        """Reset the table to have zero columns."""
        self.setColumnCount(0)
        self.key_frames = []

    # Force constant selection
    def mousePressEvent(self, event):
        """Track mousepress events to ensure that a column is always selected."""
        if self.indexAt(event.pos()).isValid():
            QTableWidget.mousePressEvent(self, event)


class FlythroughWidget(QWidget):
    """The dialogue used to create a path-based movie of a mesh.

    Allows the user to add plotter keyframes to a manageable list. Also lets one
    generate camera paths from those keyframes. Linear or interpolated paths can be
    generated to create flythrough videos of the rendered meshes.

    Parameters
    ----------
    plotter : PyVista.Plotter
        The active plotter of the app.

    """

    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        self.flyThroughPathActors = IC.FlyThroughActors()

        # Vertical layout: keyframe widget, form layout
        widgetLayout = QtO.new_layout(self, "V", margins=(0, 0, 0, 0))

        # Top widget: keyframe table, step buttons, and add/delete widget
        keyframeWidget = QtO.new_widget()
        keyframeWidgetLayout = QtO.new_layout(
            keyframeWidget, orient="V", no_spacing=True
        )

        keyframeLabel = QLabel("<b><cemter>Keyframes:")

        # table
        self.pathTable = FlyThroughTable(self.plotter, self.update_path_actors)

        # step buttons
        stepWidget = QtO.new_widget()
        stepWidgetLayout = QtO.new_layout(stepWidget, margins=(0, 0, 0, 0), spacing=5)
        pathStepStart = QtO.new_button("<<", self.step_start, 50)
        pathStepBack = QtO.new_button("<", self.step_backward, 50)
        pathStepForward = QtO.new_button(">", self.step_forward, 50)
        pathStepEnd = QtO.new_button(">>", self.step_end, 50)
        QtO.add_widgets(
            stepWidgetLayout,
            [pathStepStart, pathStepBack, pathStepForward, pathStepEnd],
        )

        # add/delete widget: two rows
        addRowLayout = QtO.new_layout()
        self.insertFrameBefore = QtO.new_button(
            "Add Before", self.pathTable.add_column, 100
        )
        self.insertFrameAfter = QtO.new_button(
            "Add After", self.pathTable.add_column, 100
        )
        QtO.add_widgets(addRowLayout, [self.insertFrameBefore, self.insertFrameAfter])

        self.deleteCurrentFrame = QtO.new_button(
            "Delete Current", self.pathTable.remove_column, 120
        )

        QtO.add_widgets(
            keyframeWidgetLayout,
            [
                keyframeLabel,
                self.pathTable,
                stepWidget,
                addRowLayout,
                self.deleteCurrentFrame,
            ],
            alignment="center",
        )

        # Path options form
        pathOptionsForm = QtO.new_form_layout()

        # Path type
        pathTypeLabel = QLabel("<b><center>Path Type:")
        self.pathTypeDropdown = QtO.new_combo(
            ["Linear", "Smoothed"], 120, connect=self.update_path_actors
        )

        # Movie Length
        movieLengthLabel = QLabel("Movie Length")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )

        QtO.add_form_rows(
            pathOptionsForm,
            [
                [pathTypeLabel, self.pathTypeDropdown],
                [movieLengthLabel, self.movieLength],
            ],
        )

        QtO.add_widgets(
            widgetLayout, [keyframeWidget, pathOptionsForm], alignment="center"
        )

    # Frame movement
    def check_columns(self, columns_needed=1):
        """Check that there are sufficient columns for the steps.

        Returns
        -------
        bool
            True if there are enough columns, False otherwise.
        """
        has_columns = False
        if self.pathTable.columnCount() >= columns_needed:
            return True
        return has_columns

    def step_start(self):
        """Move the plotter to the first keyframe."""
        if self.check_columns():
            self.pathTable.selectColumn(0)

    def step_backward(self):
        """Move the plotter to the previous keyframe, if there is one."""
        if self.check_columns(columns_needed=2):
            selected_column = self.pathTable.get_selected_column_index()
            if selected_column > 0:
                self.pathTable.selectColumn(selected_column - 1)

    def step_forward(self):
        """Move the plotter to the next keyframe, if there is one."""
        if self.check_columns(columns_needed=2):
            selected_column = self.pathTable.get_selected_column_index()
            if selected_column < self.pathTable.columnCount() - 1:
                self.pathTable.selectColumn(selected_column + 1)

    def step_end(self):
        """Move the plotter to the last keyframe."""
        if self.check_columns():
            self.pathTable.selectColumn(self.pathTable.columnCount() - 1)

    # Path actor management
    def update_path_actors(self):
        """Update the path actors when keyframes have been modified."""
        # remove the old path actors
        self.remove_path_actors()

        # make sure there are enough keyframes to update the path actors
        if self.pathTable.columnCount() > 1:

            # add the updated actors
            self.flyThroughPathActors = MovProc.generate_flythrough_actors(
                self.plotter,
                self.pathTable.key_frames,
                self.pathTypeDropdown.currentText(),  # linear/spline
                current_index=self.pathTable.selected_column,
            )

    def remove_path_actors(self):
        """Remove the path actors from the scene."""
        for actor in self.flyThroughPathActors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor, reset_camera=False)
                del actor
        return

    # Export
    def keyframe_check(self):
        """Check to ensure that there are at least two keyframes.

        Returns
        -------
        frame_check : bool
            True if > 1 keyframes, False otherwise
        """
        key_frame_check = True if self.pathTable.columnCount() > 1 else False
        return key_frame_check

    def keyframe_warning(self):
        """Raise an in-app warning to indicate that >=2 keyframes are needed."""
        warning = QMessageBox()
        warning.setWindowTitle("Keyframe Error")
        warning.setText(
            "At least <b>two</b> keyframes are ", "needed to create a Flythrough movie!"
        )
        warning.exec_()

    def generate_path(self, framerate: int):
        """Generate a flythrough path with the constructed keyframes.

        Parameters
        ----------
        framerate : int
            framerate used to generate the output frames

        Returns
        -------
        list
            (n,3,3) shaped list where each n index contains a
            plotter.camera_position

        """
        camera_path = MovProc.generate_flythrough_path(
            self.pathTable.key_frames,
            self.movieLength.value(),
            framerate,
            path_type=self.pathTypeDropdown.currentText(),
        )
        return camera_path

    # Defaulting and resetting
    def default_setup(self):
        """Initialize the default setup for the widget."""
        self.pathTable.reset()
        self.insertFrameAfter.click()  # adds an initial frame

    def reset(self):
        """Reset the widget."""
        self.remove_path_actors()
        self.pathTable.reset()


########################
### Movie generation ###
########################
class MovieDialogue(QDialog):
    """A dialogue widget used to create movies.

    With this widget, movie rendering settings are selected, a file save path is
    selected, and the movie path is created.

    Parameters
    ----------
    plotter : PyVista.Plotter
        The active plotter of the app.

    movie_dir : str
        The output directory that the movie will be saved to.

    mainWindow : QMainWindow
        The main window of the app. This is needed to make sure that the rendering
        dialogue always remains in front of all of the other windows.

    """

    def __init__(self, plotter: pv.Plotter, mainWindow: QMainWindow):
        """Build the widget."""
        super().__init__(mainWindow)
        self.plotter = plotter
        self.movie_dir = helpers.load_movie_dir()

        self.setWindowTitle("Movie Options")

        # Vertical Layout, two options boxes, bottom for path updates
        dialogueLayout = QtO.new_layout(self, "V", spacing=5)
        dialogueLayout.setSizeConstraint(QLayout.SetFixedSize)

        # Top options box
        generalOptionsWidget = QtO.new_widget(260)
        generalOptionsLayout = QtO.new_layout(
            generalOptionsWidget, orient="V", no_spacing=True
        )
        generalOptionsHeader = QLabel("<b>Movie options")

        generalOptionsBox = QGroupBox()
        generalOptionsBoxLayout = QtO.new_layout(generalOptionsBox, "V")
        generalOptionsFormLayout = QtO.new_form_layout()

        typeLabel = QLabel("Movie Type:")
        self.movieType = QtO.new_combo(
            ["Orbit", "Flythrough"], 120, connect=self.toggle_path_options
        )

        formatLabel = QLabel("File Format:")
        self.movieFormat = QtO.new_combo(
            ["mp4", "mov", "wmv"], 120, connect=self.update_format
        )

        resolutionLabel = QLabel("Resolution:")
        self.movieResolution = QtO.new_combo(
            [
                "720p",
                "1080p",
                "1440p",
                "2160p",
                "720p Square",
                "1080p Square",
                "1440p Square",
                "2160p Square",
                "Current",
            ],
            120,
        )

        fpsLabel = QLabel("Frame rate:")
        self.movieFPS = QtO.new_combo(["24", "30", "60"], 120)
        self.movieFPS.setCurrentIndex(1)

        QtO.add_form_rows(
            generalOptionsFormLayout,
            [
                [typeLabel, self.movieType],
                [formatLabel, self.movieFormat],
                [resolutionLabel, self.movieResolution],
                [fpsLabel, self.movieFPS],
            ],
        )

        QtO.add_widgets(generalOptionsBoxLayout, [0, generalOptionsFormLayout, 0])

        QtO.add_widgets(generalOptionsLayout, [generalOptionsHeader, generalOptionsBox])

        # Path options widget
        pathOptionsWidget = QtO.new_widget(260)
        pathOptionsLayout = QtO.new_layout(
            pathOptionsWidget, orient="V", no_spacing=True
        )
        self.pathOptionsHeader = QLabel("<b>Orbit Options")

        pathOptionsBox = QGroupBox()
        pathOptionsBoxLayout = QtO.new_layout(pathOptionsBox, "V")

        self.orbitWidget = OrbitWidget(self.plotter)
        self.flythroughWidget = FlythroughWidget(self.plotter)
        self.flythroughWidget.setVisible(False)

        # Tried to use a stacked widget here, but it was fucking with widget
        # resizing. abandoned it for a hide/show approach.

        QtO.add_widgets(pathOptionsBoxLayout, [self.orbitWidget, self.flythroughWidget])

        QtO.add_widgets(pathOptionsLayout, [self.pathOptionsHeader, pathOptionsBox])

        # Path IO
        pathIOWidget = QtO.new_widget(260)
        pathIOLayout = QtO.new_layout(pathIOWidget)

        loadPathbutton = QtO.new_button("Load Path", self.load_options)
        savePathButton = QtO.new_button("Save Path", self.save_options)

        QtO.add_widgets(pathIOLayout, [0, loadPathbutton, savePathButton, 0])

        # Filepath widget
        filePathWidget = QtO.new_widget(260)
        filePathWidgetLayout = QtO.new_layout(filePathWidget, no_spacing=True)
        titleLabel = QLabel("File Path:")
        self.savePathEdit = QtO.new_line_edit("None", 150, locked=True)
        self.pathDefaultStyle = self.savePathEdit.styleSheet()
        self.changePathButton = QtO.new_button("Change...", self.get_movie_save_path)
        QtO.add_widgets(
            filePathWidgetLayout,
            [titleLabel, self.savePathEdit, self.changePathButton],
        )

        # Rendering buttons.
        renderingButtonsWidget = QtO.new_widget(260)
        renderingButtonsWidgetLayout = QtO.new_layout(renderingButtonsWidget)
        cancelButton = QtO.new_button("Cancel", self.closeEvent)
        renderButton = QtO.new_button("Render", self.render_movie)
        QtO.add_widgets(
            renderingButtonsWidgetLayout, [0, cancelButton, renderButton, 0]
        )

        QtO.add_widgets(
            dialogueLayout,
            [
                generalOptionsWidget,
                filePathWidget,
                pathOptionsWidget,
                pathIOWidget,
                QtO.new_line(),
                filePathWidget,
                renderingButtonsWidget,
            ],
        )

        QtO.button_defaulting(renderButton, True)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)

    # Movie path processing
    def toggle_path_options(self):
        """Toggle the visibility of the path rendering options."""
        show_orbit = True if self.movieType.currentText() == "Orbit" else False

        # Update the path options header
        self.pathOptionsHeader.setText(
            "<b>Orbit Options" if show_orbit else "<b>Flythrough Options"
        )

        # Reset the widgets
        self.orbitWidget.reset()
        self.flythroughWidget.reset()

        # Toggle widget visibility
        self.orbitWidget.setVisible(show_orbit)
        self.flythroughWidget.setVisible(not show_orbit)

        if show_orbit:  # Add a default orbit from the current view
            self.orbitWidget.default_setup()
        else:
            self.flythroughWidget.default_setup()

    def render_movie(self):
        """Return the generated path, if created."""
        if self.savePathEdit.text() in ["None", "Select save path"]:
            self.save_path_warning()
            return

        # Make sure the save path exists
        helpers.prep_media_dir(self.savePathEdit.text())

        # Get the plotter path
        framerate = int(self.movieFPS.currentText())
        if self.movieType.currentText() == "Orbit":
            self.path = self.orbitWidget.generate_path(framerate)
        elif self.movieType.currentText() == "Flythrough":
            if not self.flythroughWidget.keyframe_check():
                self.flythroughWidget.keyframe_warning()
                return
            self.path = self.flythroughWidget.generate_path(framerate)

        self.movie_settings = IC.MovieOptions(
            self.savePathEdit.text(),
            self.movieResolution.currentText(),
            framerate,
            self.path.shape[0],
            self.path,
        )

        self.remove_path_actors()
        self.accept()

    def load_options(self):
        """Load previously saved movie options."""
        filename = helpers.load_JSON(helpers.get_dir("Desktop"))
        if not filename:
            return

        movie_options = MovProc.load_movie_options(filename)

        type_index = 0 if movie_options.movie_type == "Orbit" else 1
        self.movieType.setCurrentIndex(type_index)

        if type_index == 0:
            self.orbitWidget.orbit_path = movie_options.key_frames
            self.orbitWidget.update_path_actors()
        if type_index == 1:
            self.flythroughWidget.pathTable.load_frames(movie_options.key_frames)

        return

    def save_options(self):
        """Save the movie options for future reuse."""
        filename = helpers.get_save_file(
            "Save File As...", helpers.get_dir("Desktop"), "json"
        )
        if not filename:  # abandon if no filename
            return

        movie_type = self.movieType.currentText()
        if movie_type == "Orbit":
            key_frames = self.orbitWidget.orbit_path
        elif movie_type == "Flythrough":
            key_frames = self.flythroughWidget.pathTable.key_frames

        movie_options = IC.MovieExportOptions(movie_type, key_frames)
        MovProc.export_options(filename, movie_options)

    # File path processing
    def get_movie_save_path(self):
        """Get the save path of the movie."""
        movie_format = self.movieFormat.currentText().lower()
        path = helpers.get_save_file("Save movie as...", self.movie_dir, movie_format)

        if path:
            self.savePathEdit.setText(path)
            self.savePathEdit.setStyleSheet(self.pathDefaultStyle)

    def update_format(self):
        """Update the file format of the save path."""
        path = self.savePathEdit.text()
        # Make sure a path is selected
        if path not in ["None", "Select save path"]:
            path = list(path)
            path[-3:] = self.movieFormat.currentText().lower()
            path = ("").join(path)
            self.savePathEdit.setText(path)

    def save_path_warning(self):
        """Raise an in-app warning if a save path hasn't been selected."""
        self.savePathEdit.setStyleSheet("border: 1px solid red;")
        self.savePathEdit.setText("Select save path")

    # Window management
    def keyPressEvent(self, event):
        """Catch escape key press events to close the widget."""
        if event.key() == Qt.Key_Escape:
            self.closeEvent()
        else:
            event.accept()

    def remove_path_actors(self):
        """Remove all of the path actors and close the widget."""
        self.orbitWidget.remove_path_actors()
        self.flythroughWidget.remove_path_actors()

    def closeEvent(self, event=None):
        """An app close event."""
        self.remove_path_actors()
        self.plotter.reset_camera()
        self.reject()


#################
### Rendering ###
#################
class RenderDialogue(QDialog):
    """The popup widget used to visualize the progress of the movie rendering.

    Allows users to terminate the rendering.

    Because VTK on Windows does not like when the renderer tries to capture
    the images of the scene outside of the main thread, all plotter screen
    captures are conducted within this widget, whereas all plotter movements
    are outsourced to a qt_threading.MovieThread.

    The movie creation workflow of this widget follows the workflow below:
    1. RenderDialog writes the current frame to the movie_writer
    2. RenderDialog += the current frame and sends this frame info to the
    looping MovieThread
    3. MovieThread updates the position of the plotter and then enters a wait
    loop
    4. MovieThread calls the RenderDialog to write a new frame

    Parameters
    ----------
    plotter : PyVista.Plotter

    movie_options : input_classes.MovieOptions

    """

    def __init__(self, plotter: pv.Plotter, movie_options: IC.MovieOptions):
        """Build the dialogue."""
        super().__init__()
        self.movie_options = movie_options
        self.plotter = plotter
        self.current_frame = 0

        self.setFixedSize(350, 130)
        self.setWindowTitle("Rendering Movie...")

        # GUI Layout: top progress bar, bottom cancel button
        pageLayout = QtO.new_layout(self, "V")

        # Progress bar
        progressLayout = QtO.new_layout(orient="V", margins=0)
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, self.movie_options.frame_count)
        self.progressBarText = QLabel(
            f"<center>Writing frame 0/{self.movie_options.frame_count}"
        )
        QtO.add_widgets(progressLayout, [self.progressBar, self.progressBarText])

        # Cancel button
        buttonLayout = QtO.new_layout(margins=0)
        cancelButton = QtO.new_button("Stop", self.cancel, 100)
        QtO.add_widgets(buttonLayout, [0, cancelButton])

        QtO.add_widgets(pageLayout, [progressLayout, buttonLayout])

        # Movie thread construction
        # Resize the plotter
        if self.movie_options.resolution != "Current":
            X, Y = MovProc.get_resolution(self.movie_options.resolution)
            self.plotter.resize(X, Y)
            self.plotter.render()

        # Create the MovieThread
        self.movieRenderer = QtTh.MovieThread(
            self.plotter, self.movie_options.camera_path
        )
        self.movieRenderer.progress_update.connect(self.update_progress)
        self.movieRenderer.write_frame.connect(self.write_frame)
        self.movieRenderer.rendering_complete.connect(self.rendering_complete)

        # Set up the movie writer
        self.plotter.mwriter = get_writer(
            self.movie_options.filepath, fps=self.movie_options.fps, quality=7
        )

        # Start the MovieThread
        self.movieRenderer.start()

    def advance_frame(self):
        """Advance the current frame of the movie."""
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.update_frame(self.current_frame)
        else:
            self.movieRenderer.rendering = False

    def write_frame(self):
        """Capture a single frame adds it to the movie writer."""
        self.plotter.mwriter.append_data(self.plotter.image)
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.next_frame = self.current_frame
        else:
            self.update_progress(self.movie_options.frame_count)
            self.movieRenderer.rendering = False

    def update_progress(self, progress):
        """Update the value shown on the progress bar."""
        if progress != self.movie_options.frame_count:
            message = (
                f"<center>Writing frame {progress}/{self.movie_options.frame_count}..."
            )
        else:
            message = "<center>Compressing video..."

        self.progressBarText.setText(message)
        self.progressBar.setValue(progress)

    def keyPressEvent(self, event):
        """Monitor keypress events to catch 'escape' key presses to end the rendering."""
        if event.key() == Qt.Key_Escape:
            self.cancel()
        else:
            event.accept()

    def cancel(self):
        """Stop the movie rendering."""
        # Don't delete movie, just end it.
        self.movieRenderer.rendering = False

    def rendering_complete(self):
        """Upon the completion of the rendering, terminate the thread and close self."""
        self.movieRenderer.quit()
        self.plotter.mwriter.close()
        self.plotter.reset_camera()
        self.accept()
