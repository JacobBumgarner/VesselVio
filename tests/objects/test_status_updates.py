import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import pytest

from library.objects import StatusUpdate


def test_status_update_init():
    # check default values
    with pytest.raises(TypeError):
        update = StatusUpdate()

    update = StatusUpdate("Test")
    assert update.file_status == "Test"
    assert update.analysis_progress == 0
    assert update.file_row == 0
    assert update.annotation_progress is None
    return
