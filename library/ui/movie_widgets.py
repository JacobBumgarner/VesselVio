import imageio_ffmpeg  # Needed for PyInstaller
import numpy as np
from imageio import get_writer

from library import helpers, input as IC, qt_threading as QtTh
from library.ui import qt_objects as QtO

from PyQt5.Qt import pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QGroupBox, QLabel, QProgressBar


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

        self.pathActors = IC.CameraActors()

        self.setWindowTitle("Movie Options")

        ## Layout, two rows
        dialogueLayout = QtO.new_layout(self, "V", spacing=5)

        ## Top row
        topRow = QtO.new_widget()
        topRowLayout = QtO.new_layout(topRow, margins=0)

        # Top left
        optionsColumn = QtO.new_widget(240)
        optionsColumnLayout = QtO.new_layout(optionsColumn, orient="V", no_spacing=True)
        optionsHeader = QLabel("<b>Movie options")

        optionsBox = QGroupBox()
        optionsLayout = QtO.new_form_layout(optionsBox)

        typeLabel = QLabel("Movie Type:")
        self.movieType = QtO.new_combo(
            ["Orbit", "Flythrough"], 120, connect=self.toggle_type
        )
        self.movieType.currentIndexChanged.connect(self.visualize_path)

        formatLabel = QLabel("File Format:")
        self.movieFormat = QtO.new_combo(
            ["mp4", "mov", "wmv"], 120, connect=self.update_format
        )

        resolutionLabel = QLabel("Resolution:")
        self.movieResolution = QtO.new_combo(
            ["720p", "1080p", "1440p", "2160p", "Current"], 120
        )

        fpsLabel = QLabel("Frame rate:")
        self.movieFPS = QtO.new_combo(["24", "30", "60"], 120)
        self.movieFPS.setCurrentIndex(1)

        frameLabel = QLabel("Movie Frames:")
        self.movieFrames = QtO.new_spinbox(60, 100000, 120, step=10, width=120)

        QtO.add_form_rows(
            optionsLayout,
            [
                [typeLabel, self.movieType],
                [formatLabel, self.movieFormat],
                [resolutionLabel, self.movieResolution],
                [fpsLabel, self.movieFPS],
                [frameLabel, self.movieFrames],
            ],
        )

        QtO.add_widgets(optionsColumnLayout, [optionsHeader, optionsBox])

        # Top right
        pathColumn = QtO.new_widget(260)
        pathColumnLayout = QtO.new_layout(pathColumn, orient="V", no_spacing=True)
        pathColumnHeader = QLabel("<b>Path Options")

        pathBox = QGroupBox()
        boxLayout = QtO.new_layout(pathBox, "V")

        pathLayout = QtO.new_form_layout()

        pathHeader = QLabel("Camera path:")
        self.updatePath = QtO.new_button("Update", self.visualize_path)

        self.orientationHeader = QLabel("Camera Orientation:")
        self.updateOrientation = QtO.new_button("Update", self.visualize_path)
        self.orientationHeader.setVisible(False)
        self.updateOrientation.setVisible(False)

        QtO.add_form_rows(
            pathLayout,
            [
                [pathHeader, self.updatePath],
                [self.orientationHeader, self.updateOrientation],
            ],
        )
        QtO.add_widgets(boxLayout, [0, pathLayout, 0])

        QtO.add_widgets(pathColumnLayout, [pathColumnHeader, pathBox])

        QtO.add_widgets(topRowLayout, [optionsColumn, pathColumn])

        ## Bottom layout
        filePathWidget = QtO.new_widget()
        filePathLayout = QtO.new_layout(filePathWidget, no_spacing=True)
        titleLabel = QLabel("Save path:")
        self.pathEdit = QtO.new_line_edit("None", 150, locked=True)
        self.pathDefaultStyle = self.pathEdit.styleSheet()
        self.changePathButton = QtO.new_button("Change...", self.get_save_path)
        QtO.add_widgets(
            filePathLayout, [titleLabel, 5, self.pathEdit, 5, self.changePathButton]
        )

        buttons = QtO.new_layout(None)
        cancelButton = QtO.new_button("Cancel", self.closeEvent)
        renderButton = QtO.new_button("Render", self.return_results)
        QtO.add_widgets(buttons, [0, cancelButton, renderButton])

        QtO.button_defaulting(cancelButton, False)
        QtO.button_defaulting(renderButton, True)

        QtO.add_widgets(dialogueLayout, [topRow, filePathWidget, buttons])

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)

        self.resize()

        self.visualize_path()

        return

    # Movie path procesing
    @pyqtSlot()
    def visualize_path(self):
        self.remove_camera_actors()

        if self.movieType.currentText() == "Orbit":
            self.path = helpers.construct_orbital_path(self.plotter, 120)
        elif self.movieType.currentText() == "Flythrough":
            if self.sender() in [self.updatePath, self.movieType]:
                self.path = helpers.construct_flythrough_path(self.plotter, 120)
            elif self.sender() == self.updateOrientation:
                self.path = helpers.update_flythrough_orientation(
                    self.plotter, self.path, 120
                )

        # Create camera actor
        self.pathActors = helpers.create_path_actors(self.plotter, self.path)
        return

    def remove_camera_actors(self):
        for actor in self.pathActors.iter_actors():
            if actor:
                self.plotter.remove_actor(
                    self.pathActors.iter_actors(), reset_camera=False
                )
        self.pathActors.reset_actors()
        return

    def toggle_type(self):
        show = False if self.movieType.currentText() == "Orbit" else True
        self.orientationHeader.setVisible(show)
        self.updateOrientation.setVisible(show)
        self.resize()

    def return_results(self):
        if self.pathEdit.text() in ["None", "Select save path"]:
            self.path_warning()
            return

        # Make sure the save path exists
        helpers.prep_media_dir(self.pathEdit.text())

        # Get the at-frame path
        if self.movieType.currentText() == "Orbit":
            self.path = helpers.update_orbit_frames(self.path, self.movieFrames.value())
        elif self.movieType.currentText() == "Flythrough":
            self.path = helpers.update_flythrough_frames(
                self.path, self.movieFrames.value()
            )
        self.movie_settings = IC.MovieOptions(
            self.pathEdit.text(),
            self.movieResolution.currentText(),
            int(self.movieFPS.currentText()),
            self.movieFrames.value(),
            self.path,
        )

        self.remove_camera_actors()
        self.accept()
        return

    # File path processing
    def get_save_path(self):
        format = self.movieFormat.currentText().lower()
        path = helpers.get_save_file("Save movie as...", self.movie_dir, format)
        if path:
            self.pathEdit.setText(path)
            self.pathEdit.setStyleSheet(self.pathDefaultStyle)
        return

    def update_format(self):
        path = self.pathEdit.text()
        if path not in ["None", "Select save path"]:
            path = list(path)
            path[-3:] = self.movieFormat.currentText().lower()
            path = ("").join(path)
            self.pathEdit.setText(path)

    def path_warning(self):
        self.pathEdit.setStyleSheet("border: 1px solid red;")
        self.pathEdit.setText("Select save path")
        return

    # Window management
    def resize(self):
        self.window().setFixedSize(self.window().sizeHint())
        return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.closeEvent()
        return  # for cleanliness

    def closeEvent(self, event=None):
        self.remove_camera_actors()
        self.plotter.camera_position = self.path[0]
        self.reject()
        return  # for cleanliness


class RenderDialogue(QDialog):
    def __init__(self, plotter, movie_options):
        super().__init__()

        ### GUI Layout
        self.movie_options = movie_options
        self.plotter = plotter

        self.setFixedSize(350, 130)
        self.setWindowTitle("Rendering Movie...")

        pageLayout = QtO.new_layout(self, "V")

        progressLayout = QtO.new_layout(orient="V", margins=0)
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, self.movie_options.frame_count)
        self.progressBarText = QLabel(
            f"<center>Writing frame 0/{self.movie_options.frame_count}"
        )
        QtO.add_widgets(progressLayout, [self.progressBar, self.progressBarText])

        buttonLayout = QtO.new_layout(margins=0)
        cancelButton = QtO.new_button("Stop", self.cancel, 100)
        QtO.add_widgets(buttonLayout, [0, cancelButton])

        QtO.add_widgets(pageLayout, [progressLayout, buttonLayout])

        ## Movie thread construction
        if self.movie_options.resolution != "Current":
            X, Y = helpers.get_resolution(self.movie_options.resolution)
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
        return

    def advance_frame(self):
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.update_frame(self.current_frame)
        else:
            self.movieRenderer.rendering = False

    def write_frame(self):
        self.plotter.mwriter.append_data(self.plotter.image)
        self.current_frame += 1
        if self.current_frame < self.movie_options.frame_count:
            self.movieRenderer.next_frame = self.current_frame
        else:
            self.update_progress(self.movie_options.frame_count)
            self.movieRenderer.rendering = False

    def update_progress(self, progress):
        if progress != self.movie_options.frame_count:
            message = (
                f"<center>Writing frame {progress}/{self.movie_options.frame_count}..."
            )
        else:
            message = "<center>Compressing video..."

        self.progressBarText.setText(message)
        self.progressBar.setValue(progress)
        return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
        else:
            event.accept()
        return

    def cancel(self):
        # Don't delete movie, just end it.
        self.movieRenderer.rendering = False
        return

    def rendering_complete(self):
        self.movieRenderer.quit()
        self.plotter.mwriter.close()
        self.accept()
        return
