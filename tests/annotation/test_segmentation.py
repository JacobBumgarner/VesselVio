import os
from pathlib import Path

import numpy as np

import pytest

from library.annotation import segmentation
from skimage.io import imread


THIS_PATH = Path(__file__).parent.absolute()
FIXTURE_DIR = Path(*THIS_PATH.parts[: list(THIS_PATH.parts).index("tests") + 1])
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "test_files", "annotation_data")


segmentation_data = [
    ((1, 3, 0), (3, 4, 2), 1, 18),
    ((2, 0, 0), (4, 1, 4), 2, 30),
    ((3, 3, 3), (4, 4, 4), 3, 8),
]


@pytest.mark.parametrize("minima, maxima, seg_id, roi_volume", segmentation_data)
def test_segement_roi(minima, maxima, seg_id, roi_volume):
    labeled_volume = imread(os.path.join(ANNOTATION_DIR, "test_labeled.nii"))

    minima = np.asarray(minima)
    maxima = np.asarray(maxima)
    volume = segmentation.segment_roi.py_func(labeled_volume, minima, maxima, seg_id)

    assert volume.sum() == roi_volume
    return


@pytest.mark.parametrize("minima, maxima, seg_id, roi_volume", segmentation_data)
def test_roi_segmenation_input(minima, maxima, seg_id, roi_volume):
    labeled_volume_fname = os.path.join(ANNOTATION_DIR, "test_labeled.nii")

    volume = segmentation.roi_segmentation_input(
        minima, maxima, seg_id, labeled_volume_fname, verbose=True
    )
    assert volume.sum() == roi_volume
