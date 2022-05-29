import os
import sys

import pytest

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

import numpy as np

from library.annotation import segmentation
from skimage.io import imread


THIS_PATH = os.path.realpath(__file__)
FIXTURE_DIR = os.path.join(os.path.dirname(THIS_PATH), "test_files")
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "annotation_data")


segmentation_data = [
    ((1, 3, 0), (4, 5, 3), 1, 18),
    ((2, 0, 0), (5, 3, 5), 2, 30),
    ((3, 3, 3), (5, 5, 5), 3, 8),
]


@pytest.mark.parametrize("minima, maxima, seg_id, roi_volume", segmentation_data)
def test_segement_roi(minima, maxima, seg_id, roi_volume):
    labeled_volume = imread(os.path.join(ANNOTATION_DIR, "test_labeled.nii"))

    minima = np.asarray(minima)
    maxima = np.asarray(maxima)
    volume = segmentation.segment_roi(labeled_volume, minima, maxima, seg_id)

    assert volume.sum() == roi_volume
    return


@pytest.mark.parametrize("minima, maxima, seg_id, roi_volume", segmentation_data)
def test_roi_segmenation_input(minima, maxima, seg_id, roi_volume):
    labeled_volume_fname = os.path.join(ANNOTATION_DIR, "test_labeled.nii")

    volume = segmentation.roi_segmentation_input(
        minima, maxima, seg_id, labeled_volume_fname
    )
    assert volume.sum() == roi_volume
