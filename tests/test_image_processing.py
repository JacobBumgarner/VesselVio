import os
import sys

import pytest

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")


import numpy as np
from library import image_processing

from skimage.io import imread


THIS_PATH = os.path.realpath(__file__)
TEST_FILES = os.path.join(os.path.dirname(THIS_PATH), "test_files")


@pytest.mark.datafiles(TEST_FILES)
def test_binary_check(datafiles):
    volume = imread(os.path.join(datafiles, "non_binary_volume.tiff"))

    # test 3D
    assert image_processing.binary_check(volume) is False
    assert image_processing.binary_check(volume > 0) is True

    # test 2D
    assert image_processing.binary_check(volume[0]) is False
    assert image_processing.binary_check(volume[0] > 0) is True


@pytest.mark.datafiles(TEST_FILES)
def test_segmentation_check(datafiles):
    # test None
    assert image_processing.segmentation_check(None) is False

    # test full
    assert image_processing.segmentation_check(np.ones((5, 5, 5))) is True

    # test empty
    assert image_processing.segmentation_check(np.zeros((5, 5, 5))) is False
