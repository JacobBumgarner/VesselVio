import sys

import imageio_ffmpeg  # Needed for PyInstaller
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
    QApplication,
    QDialog,
    QGroupBox,
    QLabel,
    QMainWindow,
    QProgressBar,
    QWidget,
)


class OrbitWidget(QWidget):
    """The dialogue used to create an orbital movie around a mesh.

    Parameters
    ----------
    plotter: PyVista.Plotter

    """

    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        self.cameraActors = IC.CameraActors()

        layout = QtO.new_form_layout(self)

        pathLabel = QLabel("Camera Path")
        updateOrbit = QtO.new_button("Update", self.update_orbit)

        lengthLabel = QLabel("Movie Duration")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )

        QtO.add_form_rows(
            layout, [[pathLabel, updateOrbit], [lengthLabel, self.movieLength]]
        )

        self.update_orbit()

    def update_orbit(self):
        path_seed = self.plotter.camera_position
        self.orbit_path = MovProc.generate_orbital_path(path_seed)
        self.update_path_actors()
        return

    def update_path_actors(self):
        self.cameraActors = MovProc.generate_orbit_path_actors(
            self.plotter, self.orbit_path
        )
        return

    def remove_path_actors(self):
        for actor in self.cameraActors.iter_actors():
            if actor:
                self.plotter.remove_actor(actor)
                del actor
        return

    def generate_final_path(self, framerate):
        frames = MovProc.orbit_time_to_frames(framerate, self.movieLength.value())
        self.plotter.camera_position = self.orbit_path[0]
        return MovProc.generate_orbital_path(self.plotter.camera_position, frames)


class FlythroughWidget(QWidget):
    """The dialogue used to create a path-based movie of a mesh.

    Parameters
    ----------
    plotter: PyVista.Plotter

    """

    def __init__(self, plotter):
        super().__init__()
        layout = QtO.new_form_layout(self)

        pathLabel = QLabel("Camera Path")
        updateOrbit = QtO.new_button("Update", self.update_orbit)

        lengthLabel = QLabel("Step Duration")
        self.movieLength = QtO.new_doublespin(
            1, 1000, 10, 100, alignment="Center", suffix="s"
        )

        QtO.add_form_rows(
            layout, [[pathLabel, updateOrbit], [lengthLabel, self.movieLength]]
        )

    def add_path_actors(self):

        return

    def remove_path_actors(self):

        return

    def update_orbit(self):

        return


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
            ["Orbit", "Flythrough"], 120, connect=self.toggle_path_options
        )

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

        QtO.add_form_rows(
            optionsLayout,
            [
                [typeLabel, self.movieType],
                [formatLabel, self.movieFormat],
                [resolutionLabel, self.movieResolution],
                [fpsLabel, self.movieFPS],
            ],
        )

        QtO.add_widgets(optionsColumnLayout, [optionsHeader, optionsBox])

        # Top right
        pathColumn = QtO.new_widget(260)
        pathColumnLayout = QtO.new_layout(pathColumn, orient="V", no_spacing=True)
        self.pathColumnHeader = QLabel("<b>Path Options")

        pathBox = QGroupBox()
        boxLayout = QtO.new_layout(pathBox, "V")

        self.orbitWidget = OrbitWidget(self.plotter)
        self.flythroughWidget = FlythroughWidget(self.plotter)
        self.flythroughWidget.setVisible(False)

        QtO.add_widgets(boxLayout, [0, self.orbitWidget, self.flythroughWidget, 0])

        QtO.add_widgets(pathColumnLayout, [self.pathColumnHeader, pathBox])

        QtO.add_widgets(topRowLayout, [optionsColumn, pathColumn])

        ## Bottom layout
        filePathWidget = QtO.new_widget()
        filePathLayout = QtO.new_layout(filePathWidget, no_spacing=True)
        titleLabel = QLabel("Save path:")
        self.savePathEdit = QtO.new_line_edit("None", 150, locked=True)
        self.pathDefaultStyle = self.savePathEdit.styleSheet()
        self.changePathButton = QtO.new_button("Change...", self.get_save_path)
        QtO.add_widgets(
            filePathLayout, [titleLabel, 5, self.savePathEdit, 5, self.changePathButton]
        )

        buttons = QtO.new_layout(None)
        cancelButton = QtO.new_button("Cancel", self.closeEvent)
        renderButton = QtO.new_button("Render", self.return_movie_path)
        QtO.add_widgets(buttons, [0, cancelButton, renderButton])

        QtO.button_defaulting(cancelButton, False)
        QtO.button_defaulting(renderButton, True)

        QtO.add_widgets(dialogueLayout, [topRow, filePathWidget, buttons])

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)

        self.set_fixed_size()

    def toggle_path_options(self):
        """Toggle the visbiility of the rendering path options"""
        show_orbit = True if self.movieType.currentText() == "Orbit" else False

        # Update the path options header
        options_text = "Orbit Options" if show_orbit else "Flythrough Options"
        self.pathColumnHeader.setText(options_text)

        # Remove the path actors
        self.orbitWidget.remove_path_actors()
        self.flythroughWidget.remove_path_actors()

        # Update the widget visibility
        self.orbitWidget.setVisible(show_orbit)
        self.flythroughWidget.setVisible(not show_orbit)
        if show_orbit:  # Add a defaul orbit from the current view
            self.orbitWidget.update_orbit()

        self.set_fixed_size()

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
            self.path = self.orbitWidget.generate_final_path(framerate)
        elif self.movieType.currentText() == "Flythrough":
            self.path = MovProc.update_flythrough_frames(
                self.path, self.movieFrames.value()
            )

        self.movie_settings = IC.MovieOptions(
            self.savePathEdit.text(),
            self.movieResolution.currentText(),
            framerate,
            self.path.shape[0],
            self.path,
        )

        self.remove_camera_actors()
        self.accept()

    # File path processing
    def get_save_path(self):
        """Load the save path of the movie"""
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
    def set_fixed_size(self):
        """Lock the size of the window widget"""
        self.window().setFixedSize(self.window().sizeHint())

    def keyPressEvent(self, event):
        """Catch escape key press events to close the widget"""
        if event.key() == Qt.Key_Escape:
            self.closeEvent()
        else:
            event.accept()

    def remove_camera_actors(self):
        """Remove all of the path actors and close the widget"""
        self.orbitWidget.remove_path_actors()
        self.flythroughWidget.remove_path_actors()

    def closeEvent(self, event=None):
        self.remove_camera_actors()
        self.reject()


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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
        else:
            event.accept()

    def cancel(self):
        # Don't delete movie, just end it.
        self.movieRenderer.rendering = False

    def rendering_complete(self):
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
