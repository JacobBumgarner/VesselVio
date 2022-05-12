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
import matplotlib  # Needed for PyInstaller
import numpy as np

import pyvista as pv
from imageio import get_writer

from library import (
    helpers,
    input_classes as IC,
    movie_processing as MovProc,
    qt_threading as QtTh,
)
from library.ui import qt_objects as QtO

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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


class OrbitWidget(QWidget):
    """The dialogue used to create an orbital movie around a mesh. Allows users
    to move the plotter around the visaulized meshes and generate orbital paths
    in the plane orthogonal to the viewup angle.

    Parameters
    ----------
    plotter: PyVista.Plotter

    Returns
    -------
    QWidget
        The widget used to update the orbit options for the movie

    """

    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        self.orbitPathActors = IC.OrbitActors()
        self.setFixedSize(260, 140)
        widgetLayout = QtO.new_layout(self, "V")
        formLayout = QtO.new_form_layout()

        pathLabel = QLabel("Camera Path")
        updateOrbit = QtO.new_button("Update", self.update_orbit)

        lengthLabel = QLabel("Movie Duration")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )

        QtO.add_form_rows(
            formLayout, [[pathLabel, updateOrbit], [lengthLabel, self.movieLength]]
        )
        QtO.add_widgets(widgetLayout, [0, formLayout, 0])

        self.update_orbit()

    def update_orbit(self):
        """Updates the orbit path for the movie based on the current
        plotter position
        """
        path_seed = self.plotter.camera_position
        self.orbit_path = MovProc.generate_orbital_path(path_seed)
        self.update_path_actors()

    def update_path_actors(self):
        """Updates the position of the orbital path actor"""
        self.remove_path_actors()
        self.orbitPathActors = MovProc.generate_orbit_path_actors(
            self.plotter, self.orbit_path
        )

    def remove_path_actors(self):
        """Eliminates all path actors from the scene and destroys them"""
        for actor in self.orbitPathActors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor, reset_camera=False)
                del actor

    def export_path(self, framerate):
        """Generates an orbital path with with the requested frame count

        Parameters
        ----------
        framerate: int
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
        """Resets the widget"""
        self.remove_path_actors()

    def default_setup(self):
        """Provides a default orbit for the widget when called"""
        self.update_orbit()


class FlyThroughTable(QTableWidget):
    """The table widget used to keep track of and modifiy the keyframes for the
    flythrough movie. As long as there is at least one column in the table, it will
    be selected. Also contains a key_frame list that keeps track of the keyframe
    plotter.camera_positions

    Parameters
    ----------
    plotter: PyVista.Plotter

    update_path_actors: Callable
        The update_path_actors of the parent FlyThroughWidget should be passed

    Returns
    -------
    QTableWidget

    """

    key_frames = []
    selected_column = 0

    def __init__(self, plotter, update_path_actors):
        super().__init__()
        self.plotter = plotter
        self.update_path_actors = update_path_actors

        # Boiler plate
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectColumns)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        # self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.horizontalHeader().setDefaultSectionSize(30)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setStretchLastSection(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setFixedSize(200, 40)

        # Set the column headers
        self.setRowCount(1)
        self.setHorizontalHeaderLabels(["Key Frame"])

        # Connect the selection changed to the plotter
        self.selectionModel().selectionChanged.connect(self.update_plotter_view)
        self.cellClicked.connect(self.update_plotter_view)

    # Selection processing
    def default_selection(self):
        """Selects the first column of the table by default"""
        if not self.selectionModel().hasSelection():
            self.selectColumn(0)

    def get_selected_column_index(self):
        """Identifies the selected column of the model"""
        if self.selectionModel().hasSelection():
            model = self.selectionModel()
            selection = model.selectedColumns()[0]
            keyframe_index = selection.column()
        else:
            keyframe_index = 0
        return int(keyframe_index)

    def update_plotter_view(self):
        """Updates the position of the plotter based on the current table
        selection
        """
        model = self.selectionModel()
        if not model.hasSelection():
            self.selected_column = 0
            return

        self.selected_column = model.selectedColumns()[0].column()
        MovProc.post_path_plotter_update(
            self.plotter, self.key_frames[self.selected_column], orbit=False
        )

    # column Processing
    @pyqtSlot()
    def add_column(self):
        """Inserts a column into the table at the current index, either before
        or after the selected column. Uses a pyqtSlot to find the
        currently selected column
        """
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
        """Removes the actively selected column"""
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
        """Renames the keyframes of the table by ascending order"""
        for i in range(self.columnCount()):
            item = self.item(0, i)
            item.setText(str(i + 1))

    def load_frames(self, key_frames):
        """Loads keyframes from previously saved options"""
        self.key_frames = key_frames

        # Reset the columns, add new items
        self.setColumnCount(len(key_frames))
        for i in range(self.columnCount()):
            item = QTableWidgetItem(str(i + 1))
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(0, i, item)

        self.update_path_actors()

    def reset(self):
        """Resets the table to have zero columns"""
        self.setColumnCount(0)
        self.key_frames = []

    # Force constant selection
    def mousePressEvent(self, event):
        """Tracks mousepress events to ensure that a column is always selected, so
        long as there is at least one column in the table"""
        if self.indexAt(event.pos()).isValid():
            QTableWidget.mousePressEvent(self, event)


class FlythroughWidget(QWidget):
    """The dialogue used to create a path-based movie of a mesh. Allows you to
    add plotter keyframes to a managable list, and lets you generate camera
    paths from those keyframes. Linear or interpolated paths can be generated
    to create flythrough videos of the rendered meshes.

    Parameters
    ----------
    plotter: PyVista.Plotter

    """

    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        self.flyThroughPathActors = IC.FlyThroughActors()

        # Horizontal layout, two components
        layout = QtO.new_layout(self, "H", no_spacing=True)

        # Left layout, two components: table, step buttons
        leftLayout = QtO.new_layout(orient="V", no_spacing=True)

        # table
        self.pathTable = FlyThroughTable(self.plotter, self.update_path_actors)

        # step buttons
        stepWidget = QtO.new_widget()
        stepLayout = QtO.new_layout(stepWidget, margins=(0, 0, 0, 0), spacing=5)
        pathStepStart = QtO.new_button("<<", self.step_start, 50)
        pathStepBack = QtO.new_button("<", self.step_backward, 50)
        pathStepForward = QtO.new_button(">", self.step_forward, 50)
        pathStepEnd = QtO.new_button(">>", self.step_end, 50)
        QtO.add_widgets(
            stepLayout, [pathStepStart, pathStepBack, pathStepForward, pathStepEnd]
        )

        lengthLayout = QtO.new_layout()
        lengthLabel = QLabel("Movie Duration")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )
        QtO.add_widgets(lengthLayout, [lengthLabel, self.movieLength])

        QtO.add_widgets(leftLayout, [self.pathTable, 5, stepWidget, lengthLayout])

        # right widget, horizontal layout, two widgets:
        # keyframes management, path type
        rightLayout = QtO.new_layout(orient="V", spacing=5)

        # keyframe management
        framesLabel = QLabel("<b><center>Keyframes:")
        self.insertFrameBefore = QtO.new_button(
            "Add Before", self.pathTable.add_column, 120
        )
        self.insertFrameAfter = QtO.new_button(
            "Add After", self.pathTable.add_column, 120
        )
        self.deleteCurrentFrame = QtO.new_button(
            "Delete Current", self.pathTable.remove_column, 120
        )

        # path type
        pathTypeLabel = QLabel("<b><center>Path Type:")
        self.pathTypeDropdown = QtO.new_combo(
            ["Linear", "Smoothed"], 120, connect=self.update_path_actors
        )

        QtO.add_widgets(
            rightLayout,
            [
                0,
                framesLabel,
                self.insertFrameBefore,
                self.insertFrameAfter,
                self.deleteCurrentFrame,
                10,
                pathTypeLabel,
                self.pathTypeDropdown,
                0,
            ],
            alignment="center",
        )

        QtO.add_widgets(layout, [leftLayout, 5, rightLayout])

    # Frame movement
    def check_columns(self, columns_needed=1):
        """Check that there are sufficient columns for the steps

        Returns
        -------
        bool
        """
        has_columns = False
        if self.pathTable.columnCount() >= columns_needed:
            return True
        return has_columns

    def step_start(self):
        """Moves the plotter to the first keyframe"""
        if self.check_columns():
            self.pathTable.selectColumn(0)

    def step_backward(self):
        """Moves the plotter to the previous keyframe, if there is one"""
        if self.check_columns(columns_needed=2):
            selected_column = self.pathTable.get_selected_column_index()
            if selected_column > 0:
                self.pathTable.selectColumn(selected_column - 1)

    def step_forward(self):
        """Moves the plotter to the next keyframe, if there is one"""
        if self.check_columns(columns_needed=2):
            selected_column = self.pathTable.get_selected_column_index()
            if selected_column < self.pathTable.columnCount() - 1:
                self.pathTable.selectColumn(selected_column + 1)

    def step_end(self):
        """Moves the plotter to the last keyframe"""
        if self.check_columns():
            self.pathTable.selectColumn(self.pathTable.columnCount() - 1)

    # Path actor management
    def update_path_actors(self):
        # remove the old path actors
        self.remove_path_actors()

        # make sure there are enough keyframes to update the path actors
        if self.pathTable.columnCount() > 1:

            # add the udpated actors
            self.flyThroughPathActors = MovProc.generate_flythrough_actors(
                self.plotter,
                self.pathTable.key_frames,
                self.pathTypeDropdown.currentText(),  # linear/spline
                current_index=self.pathTable.selected_column,
            )

    def remove_path_actors(self):
        for actor in self.flyThroughPathActors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor, reset_camera=False)
                del actor
        return

    # Export
    def keyframe_check(self):
        """Checks to ensure that there are at least two keyframes.

        Returns
        -------
        frame_check : bool
            True if > 1 keyframes, False otherwise
        """
        key_frame_check = True if self.pathTable.columnCount() > 1 else False
        return key_frame_check

    def keyframe_warning(self):
        """Throws a warning indicating that at least two keyframes
        are needed to create a movie."""
        warning = QMessageBox()
        warning.setWindowTitle("Keyframe Error")
        warning.setText(
            "At least <b>two</b> keyframes are needed to create a Flythrough movie!"
        )
        warning.exec_()

    def export_path(self, framerate):
        """Exports the created keyframes into a path for movie rendering"""
        camera_path = MovProc.generate_flythrough_path(
            self.pathTable.key_frames,
            self.movieLength.value(),
            framerate,
            path_type=self.pathTypeDropdown.currentText(),
        )
        return camera_path

    # Defaulting and resetting
    def default_setup(self):
        """Creates a default setup for the widget. Resets the table"""
        self.pathTable.reset()
        self.insertFrameAfter.click()  # adds an initial frame

    def reset(self):
        self.remove_path_actors()
        self.pathTable.reset()


class MovieDialogue(QDialog):
    """A dialogue widget used to create movies. Movie rendering settings are
    selected, a save path is selected, and the movie path is created.

    Parameters
    ----------
    plotter: PyVista.Plotter

    movie_dir: The output directory that the movie will be saved to.

    mainWindow: QMainWindow
        Needed to make sure that the rendering dialogue always remains in front
        of all of the other windows.

    """

    def __init__(self, plotter, mainWindow):
        super().__init__(mainWindow)
        self.plotter = plotter
        self.movie_dir = helpers.load_movie_dir()

        self.setWindowTitle("Movie Options")

        ## Layout, two rows
        dialogueLayout = QtO.new_layout(self, "V", spacing=5)
        dialogueLayout.setSizeConstraint(QLayout.SetFixedSize)

        ## Top row
        topRow = QtO.new_widget()
        topRowLayout = QtO.new_layout(topRow, margins=0)

        # Top left
        optionsColumn = QtO.new_widget(260)
        optionsColumnLayout = QtO.new_layout(optionsColumn, orient="V", no_spacing=True)
        optionsHeader = QLabel("<b>Movie options")

        optionsBox = QGroupBox()
        optionsLayout = QtO.new_layout(optionsBox, "V")
        optionsForm = QtO.new_form_layout()

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
                "2160p Square" "Current",
            ],
            120,
        )

        fpsLabel = QLabel("Frame rate:")
        self.movieFPS = QtO.new_combo(["24", "30", "60"], 120)
        self.movieFPS.setCurrentIndex(1)

        QtO.add_form_rows(
            optionsForm,
            [
                [typeLabel, self.movieType],
                [formatLabel, self.movieFormat],
                [resolutionLabel, self.movieResolution],
                [fpsLabel, self.movieFPS],
            ],
        )

        QtO.add_widgets(optionsLayout, [0, optionsForm, 0])

        QtO.add_widgets(optionsColumnLayout, [optionsHeader, optionsBox])

        # Top right
        pathColumn = QtO.new_widget()
        pathColumnLayout = QtO.new_layout(pathColumn, orient="V", no_spacing=True)
        self.pathColumnHeader = QLabel("<b>Path Options")

        pathBox = QGroupBox()
        boxLayout = QtO.new_layout(pathBox, "V")

        self.orbitWidget = OrbitWidget(self.plotter)
        self.flythroughWidget = FlythroughWidget(self.plotter)
        self.flythroughWidget.setVisible(False)

        # Tried to use a stacked widget here, but it was fucking with widget
        # resizing. abandoned it for a simpler hide/show approach.
        # self.pathStack = QtO.new_stacked([self.orbitWidget, self.flythroughWidget])
        # # Connect the movieType button to the pathStack
        # self.movieType.currentIndexChanged.connect(self.pathStack.setCurrentIndex)
        # QtO.add_widgets(boxLayout, [self.pathStack])

        QtO.add_widgets(boxLayout, [self.orbitWidget, self.flythroughWidget])

        QtO.add_widgets(pathColumnLayout, [self.pathColumnHeader, pathBox])

        QtO.add_widgets(topRowLayout, [optionsColumn, pathColumn])

        ## Bottom layout
        filePathWidget = QtO.new_widget()
        filePathLayout = QtO.new_layout(filePathWidget, no_spacing=True)
        titleLabel = QLabel("Save path:")
        self.savePathEdit = QtO.new_line_edit("None", 150, locked=True)
        self.pathDefaultStyle = self.savePathEdit.styleSheet()
        self.changePathButton = QtO.new_button("Change...", self.get_movie_save_path)
        QtO.add_widgets(
            filePathLayout, [titleLabel, 5, self.savePathEdit, 5, self.changePathButton]
        )

        # add bottom row buttons to initia.
        buttons = QtO.new_layout(None)
        saveLabel = QLabel("<b>Movie Options:")
        loadButton = QtO.new_button("Load", self.load_options)
        saveButton = QtO.new_button("Save", self.save_options)
        cancelButton = QtO.new_button("Cancel", self.closeEvent)
        renderButton = QtO.new_button("Render", self.return_movie_path)
        renderButton.setAutoDefault(True)
        QtO.add_widgets(
            buttons, [saveLabel, loadButton, saveButton, 0, cancelButton, renderButton]
        )

        QtO.button_defaulting(cancelButton, False)
        QtO.button_defaulting(renderButton, True)

        QtO.add_widgets(dialogueLayout, [topRow, filePathWidget, buttons])

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)

    # Movie path processing
    def toggle_path_options(self):
        """Toggle the visbiility of the rendering path options"""
        show_orbit = True if self.movieType.currentText() == "Orbit" else False

        # Update the path options header
        options_text = "<b>Orbit Options" if show_orbit else "<b>Flythrough Options"
        self.pathColumnHeader.setText(options_text)

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

    def return_movie_path(self):
        """Return the generated path, if created."""
        if self.savePathEdit.text() in ["None", "Select save path"]:
            self.save_path_warning()
            return

        # Make sure the save path exists
        helpers.prep_media_dir(self.savePathEdit.text())

        # Get the plotter path
        framerate = int(self.movieFPS.currentText())
        if self.movieType.currentText() == "Orbit":
            self.path = self.orbitWidget.export_path(framerate)
        elif self.movieType.currentText() == "Flythrough":
            if not self.flythroughWidget.keyframe_check():
                self.flythroughWidget.keyframe_warning()
                return
            self.path = self.flythroughWidget.export_path(framerate)

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
        """Load previously saved movie options"""
        filename = helpers.load_JSON(helpers.get_dir("Desktop"))
        if not filename:
            return

        movie_options = MovProc.load_options(filename)

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
        """Get the save path of the movie"""
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
        """Throw a warning if a save path hasn't been selected"""
        self.savePathEdit.setStyleSheet("border: 1px solid red;")
        self.savePathEdit.setText("Select save path")

    # Window management
    def keyPressEvent(self, event):
        """Catch escape key press events to close the widget"""
        if event.key() == Qt.Key_Escape:
            self.closeEvent()
        else:
            event.accept()

    def remove_path_actors(self):
        """Remove all of the path actors and close the widget"""
        self.orbitWidget.remove_path_actors()
        self.flythroughWidget.remove_path_actors()

    def closeEvent(self, event=None):
        self.remove_path_actors()
        self.plotter.reset_camera()
        self.reject()


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
        super().__init__()
        self.movie_options = movie_options
        self.plotter = plotter
        
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
        if self.movie_options.resolution != "Current":
            X, Y = MovProc.get_resolution(self.movie_options.resolution)
            self.plotter.resize(X, Y)
            self.plotter.render()

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

        self.current_frame = 0
        self.movieRenderer.start()

    def advance_frame(self):
        """Advances the current frame of the movie"""
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.update_frame(self.current_frame)
        else:
            self.movieRenderer.rendering = False

    def write_frame(self):
        """Captures a single frame adds it to the movie writer"""
        self.plotter.mwriter.append_data(self.plotter.image)
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.next_frame = self.current_frame
        else:
            self.update_progress(self.movie_options.frame_count)
            self.movieRenderer.rendering = False

    def update_progress(self, progress):
        """Updates the value shown on the progress bar"""
        if progress != self.movie_options.frame_count:
            message = (
                f"<center>Writing frame {progress}/{self.movie_options.frame_count}..."
            )
        else:
            message = "<center>Compressing video..."

        self.progressBarText.setText(message)
        self.progressBar.setValue(progress)

    def keyPressEvent(self, event):
        """Monitors keypress events to cancel the rendering if the 'escape' key
        is pressed"""
        if event.key() == Qt.Key_Escape:
            self.cancel()
        else:
            event.accept()

    def cancel(self):
        """Stops the movie rendering."""
        # Don't delete movie, just end it.
        self.movieRenderer.rendering = False

    def rendering_complete(self):
        """Upon the completion of the rendering, closes the MovieThread, the 
        movie writer, and self."""
        self.movieRenderer.quit()
        self.plotter.mwriter.close()
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    p = pv.Plotter()
    window = QMainWindow()
    window.show()

    demo = MovieDialogue(p, window)
    demo.exec_()
    sys.exit(app.exec_())
