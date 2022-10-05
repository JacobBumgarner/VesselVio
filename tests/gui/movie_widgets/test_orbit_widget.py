import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import numpy as np

import pytest
from library.gui.movie_widgets import OrbitWidget
from library.input_classes import OrbitActors
from PyQt5.QtCore import Qt

from pyvista import Plotter


@pytest.fixture
def plotter():
    p = Plotter()
    return p


def test_init(qtbot, plotter: Plotter):
    widget = OrbitWidget(plotter)

    # check that an orbit exists
    assert isinstance(widget.orbit_path, np.ndarray)
    assert isinstance(widget.orbitPathActors, OrbitActors)


def test_update_orbit(qtbot, plotter: Plotter):
    widget = OrbitWidget(plotter)

    old_path = widget.generate_path(30)

    new_camera_position = np.array([[2, 2, 6], [0, 0, 0], [0, 1, 0]])
    plotter.camera_position = new_camera_position

    qtbot.mouseClick(widget.updateOrbitButton, Qt.LeftButton)
    new_path = widget.generate_path(30)

    assert old_path.shape == new_path.shape
    assert np.any(old_path[0] != new_path[0])


def test_generate_path(qtbot, plotter: Plotter):
    widget = OrbitWidget(plotter)

    path = widget.generate_path(30)

    assert isinstance(path, np.ndarray)
    assert path.shape[0] == 30 * widget.movieLength.value()

    widget.movieLength.setValue(20)

    path = widget.generate_path(30)
    assert path.shape[0] == 30 * widget.movieLength.value()


def test_reset(qtbot, plotter: Plotter):
    widget = OrbitWidget(plotter)

    widget.reset()

    assert len(plotter.renderer.actors) == 0
