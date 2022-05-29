import os
import sys

import pytest

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

import numpy as np

from library import image_processing as ImProc
from library.annotation import labeling, segmentation_prep
from skimage.io import imread


THIS_PATH = os.path.realpath(__file__)
FIXTURE_DIR = os.path.join(os.path.dirname(THIS_PATH), "test_files")
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "annotation_data")


labeled_volume = imread(os.path.join(ANNOTATION_DIR, "test_labeled.nii"))
VOLUME = (labeled_volume > 0).astype(np.uint8)


# ROI array specific to the labeled_test.nii volume
@pytest.fixture
def prepped_data():
    roi_array = np.array([[1, 0], [2, 0], [3, 0]])
    roi_dict, roi_keys = segmentation_prep.prep_roi_array(roi_array)
    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(roi_array)
    minima = [
        (1, 3, 0),
        (2, 0, 0),
        (3, 3, 3),
    ]
    maxima = [(3, 4, 2), (4, 1, 4), (4, 4, 4)]
    expected_volumes = [18, 30, 8]
    prepped = {
        "roi_array": roi_array,
        "roi_dict": roi_dict,
        "roi_keys": roi_keys,
        "roi_volumes": roi_volumes,
        "volume_updates": volume_updates,
        "expected_minima": minima,
        "expected_maxima": maxima,
        "expected_volumes": expected_volumes,
    }
    return prepped


def test_update_bounds():
    # don't parameterize, we want to keep the minima/maxima values
    minima = np.full((5, 3), 10)
    maxima = np.zeros((5, 3))

    points = [(1, 1, 1), (5, 5, 5)]
    checks = [[(1, 1, 1), (0, 0, 0)], [(1, 1, 1), (5, 5, 5)]]

    for i in range(2):
        labeling.update_bounds(minima, maxima, *points[i], 1)
        assert np.all(minima[1] == checks[i][0])
        assert np.all(maxima[1] == checks[i][1])


def test_slice_labeling(prepped_data):
    volume = VOLUME.copy()

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(
        volume, prepped_data["roi_array"]
    )

    slice_volumes = prepped_data["roi_volumes"].copy()
    for z in range(5):
        volume, slice_volumes, minima, maxima = labeling.label_slice(
            volume,
            labeled_volume[z],
            slice_volumes,
            prepped_data["volume_updates"],
            prepped_data["roi_dict"],
            np.asarray(list(prepped_data["roi_keys"])),
            minima,
            maxima,
            z,
        )
        prepped_data["roi_volumes"] += slice_volumes
        slice_volumes *= 0

    assert np.all(prepped_data["roi_volumes"] == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


bgr_test_data = [
    (np.array([[255, 255, 255], [0, 0, 0]]), [16777215, 0], (2,)),
    (np.array([[[100, 100, 200]], [[0, 0, 1]]]), [[13132900], [65536]], (2, 1)),
]


@pytest.mark.parametrize("rgb_array, int_check, shape_check", bgr_test_data)
def test_convert_bgr_to_int(rgb_array, int_check, shape_check):
    int_array = labeling.convert_bgr_to_int(rgb_array)
    assert np.all(int_array == int_check)
    assert int_array.shape == shape_check
    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_RGB_labelng_input(datafiles, prepped_data):
    volume = VOLUME.copy()

    rgb_folder = os.path.join(datafiles, "test_rgb_labeled")

    volume, roi_volumes, minima, maxima = labeling.RGB_labeling_input(
        volume, rgb_folder, np.array([[255, 0], [65280, 0], [16711680, 0]])
    )

    assert np.all(np.unique(volume) == [0, 1, 2, 3])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_nn_id_labeling(datafiles, prepped_data):
    labeled_volume = ImProc.load_nii_volume(
        os.path.join(datafiles, "test_labeled_f4.nii")
    )
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.nn_id_labeling(
        volume, labeled_volume, np.array([[1, 0], [2, 0], [3, 0]])
    )
    assert np.all(np.unique(volume) == [0, 1, 2, 3])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_numba_id_labeling(datafiles, prepped_data):
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.numba_id_labeling(
        volume, labeled_volume, np.array([[1, 0], [2, 0], [3, 0]])
    )
    assert np.all(np.unique(volume) == [0, 1, 2, 3])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


id_annotation_test_files = [
    ("test_labeled.nii", False),
    ("test_labeled_f4.nii", False),
    ("test_labeled_wrong_size.nii", True),
]


@pytest.mark.parametrize(
    "annotation_file, empty_result_expected", id_annotation_test_files
)
def test_id_labeling_input(annotation_file, empty_result_expected, prepped_data):
    annotation_file = os.path.join(ANNOTATION_DIR, annotation_file)
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.id_labeling_input(
        volume, annotation_file, np.array([[1, 0], [2, 0], [3, 0]])
    )

    if empty_result_expected:
        assert all(x is None for x in (volume, roi_volumes, minima, maxima))
    else:
        assert np.all(np.unique(volume) == [0, 1, 2, 3])
        assert volume.shape == (5, 5, 5)
        assert np.all(roi_volumes == prepped_data["expected_volumes"])
        assert np.all(minima == prepped_data["expected_minima"])
        assert np.all(maxima == prepped_data["expected_maxima"])

    return


input_annotation_test_files = [
    ("test_labeled.nii", "ID", np.array([[1, 0], [2, 0], [3, 0]])),
    ("test_rgb_labeled", "RGB", np.array([[255, 0], [65280, 0], [16711680, 0]])),
]


@pytest.mark.parametrize(
    "annotation_file, annotation_type, roi_array", input_annotation_test_files
)
def test_volume_labeling_input(
    tmpdir, prepped_data, annotation_file, annotation_type, roi_array
):
    volume = VOLUME.copy()

    annotation_file = os.path.join(ANNOTATION_DIR, annotation_file)
    roi_volumes, minima, maxima = labeling.volume_labeling_input(
        volume,
        annotation_file,
        roi_array,
        annotation_type,
        tmpdir,
    )

    # check output
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])

    # check cached volume
    cache_path = os.path.join(tmpdir, "labeled_volume.npy")
    assert os.path.exists(cache_path)
    labeled_volume = np.load(cache_path)
    assert labeled_volume.shape == (5, 5, 5)
    assert all(np.unique(labeled_volume) == [0, 1, 2, 3])
    return


# test_volume_labeling_input(
#     "/Users/jacobbumgarner/Desktop/tmp_folder",
#     prepped_data(),
#     *input_annotation_test_files[1]
# )
